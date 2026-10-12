// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use base64::{engine::general_purpose::STANDARD as BASE64, Engine as _};
use std::io::{Read, Write};
use std::net::TcpStream;
use std::path::PathBuf;
use std::process::{Child, Command, Stdio as ProcessStdio};
use std::sync::Mutex;
use std::time::{Duration, Instant};
use tauri::{Manager, RunEvent};

/// 嵌入的后端可执行文件（PyInstaller 单文件），release 时打进主 EXE
#[cfg(not(debug_assertions))]
const BACKEND_BIN: &[u8] =
    include_bytes!("../binaries/lottery-backend-x86_64-pc-windows-msvc.exe");

/// 保存后端子进程句柄，退出时统一关闭。
struct BackendProcess(Mutex<Option<Child>>);

/// 默认等待后端就绪的最长时间。
const BACKEND_READY_TIMEOUT: Duration = Duration::from_secs(30);
/// 健康检查间隔。
const HEALTH_CHECK_INTERVAL: Duration = Duration::from_millis(200);

/// 把嵌入的 backend exe 解压到 app_data_dir，返回可执行文件路径。
fn extract_backend(app: &tauri::AppHandle) -> Result<PathBuf, String> {
    #[cfg(not(debug_assertions))]
    {
        let dir = app
            .path()
            .app_data_dir()
            .map_err(|e| format!("无法获取应用数据目录：{e}"))?;
        std::fs::create_dir_all(&dir).map_err(|e| format!("创建数据目录失败：{e}"))?;

        let exe_name = if cfg!(windows) { "lottery-backend.exe" } else { "lottery-backend" };
        let target = dir.join(exe_name);

        let need_extract = match std::fs::read(&target) {
            Ok(existing) => existing.as_slice() != BACKEND_BIN,
            Err(_) => true,
        };
        if need_extract {
            std::fs::write(&target, BACKEND_BIN)
                .map_err(|e| format!("写入后端可执行文件失败：{e}"))?;
        }
        Ok(target)
    }

    #[cfg(debug_assertions)]
    {
        let candidates = [
            "../backend/dist/lottery-backend.exe",
            "../backend/dist/lottery-backend",
        ];
        for c in candidates {
            let p = std::path::Path::new(c).canonicalize();
            if let Ok(p) = p {
                if p.exists() {
                    return Ok(p);
                }
            }
        }
        Err("开发模式未找到后端可执行文件，请先在 backend/ 目录执行 python build_sidecar.py".into())
    }
}

/// 启动内嵌的后端进程。
fn spawn_backend(app: &tauri::AppHandle) -> Result<Child, String> {
    let exe_path = extract_backend(app)?;

    let mut cmd = Command::new(&exe_path);
    cmd.stdin(ProcessStdio::null());

    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        const CREATE_NEW_CONSOLE: u32 = 0x0000_0010;
        cmd.creation_flags(CREATE_NEW_CONSOLE);
    }

    let child = cmd
        .spawn()
        .map_err(|e| format!("启动后端失败：{e}"))?;
    Ok(child)
}

/// 通过 TCP 连接探测后端端口是否在监听。
fn port_listening(port: u16) -> bool {
    TcpStream::connect_timeout(
        &format!("127.0.0.1:{port}").parse().unwrap(),
        HEALTH_CHECK_INTERVAL,
    )
    .is_ok()
}

/// 向 /api/health 发 HTTP GET，返回 200 表示后端就绪。
fn health_ok(port: u16) -> bool {
    let addr = format!("127.0.0.1:{port}");
    let Ok(mut stream) = TcpStream::connect_timeout(
        &addr.parse().unwrap(),
        HEALTH_CHECK_INTERVAL,
    ) else {
        return false;
    };
    let _ = stream.set_read_timeout(Some(Duration::from_millis(500)));
    let _ = stream.set_write_timeout(Some(HEALTH_CHECK_INTERVAL));
    let req = format!(
        "GET /api/health HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: close\r\n\r\n"
    );
    if stream.write_all(req.as_bytes()).is_err() {
        return false;
    }
    let mut buf = [0u8; 256];
    let n = stream.read(&mut buf).unwrap_or(0);
    if n == 0 {
        return false;
    }
    let head = String::from_utf8_lossy(&buf[..n]);
    head.starts_with("HTTP/1.1 200") || head.starts_with("HTTP/1.0 200")
}

/// 同步等待后端就绪（端口监听 + /api/health 返回 200）。
fn wait_backend_ready(port: u16) -> bool {
    let start = Instant::now();
    while start.elapsed() < BACKEND_READY_TIMEOUT {
        if port_listening(port) && health_ok(port) {
            return true;
        }
        std::thread::sleep(HEALTH_CHECK_INTERVAL);
    }
    false
}

/// 后端默认端口，与 run_server.py 中的默认保持一致。
const DEFAULT_BACKEND_PORT: u16 = 8000;

/// 把 base64 数据写入文件，返回保存路径。
/// Tauri WebView 下 blob: URL 的下载不可靠，改由 Rust 端落盘。
#[tauri::command]
fn save_download(app: tauri::AppHandle, filename: String, data_base64: String) -> Result<String, String> {
    use tauri_plugin_shell::ShellExt;

    let dir = app
        .path()
        .download_dir()
        .or_else(|_| app.path().app_data_dir())
        .map_err(|e| format!("无法定位下载目录：{e}"))?;
    std::fs::create_dir_all(&dir).map_err(|e| format!("创建下载目录失败：{e}"))?;

    let target = dir.join(&filename);
    let bytes = BASE64
        .decode(data_base64.as_bytes())
        .map_err(|e| format!("Base64 解码失败：{e}"))?;
    std::fs::write(&target, bytes).map_err(|e| format!("写入文件失败：{e}"))?;

    // 在资源管理器中显示该文件（不依赖默认应用）
    #[cfg(windows)]
    {
        let _ = app.shell().command("explorer").args(["/select,", target.to_str().unwrap_or("")]).spawn();
    }
    #[cfg(target_os = "macos")]
    {
        let _ = app.shell().command("open").args(["-R", target.to_str().unwrap_or("")]).spawn();
    }
    #[cfg(all(unix, not(target_os = "macos")))]
    {
        let _ = app.shell().command("xdg-open").args([target.parent().unwrap_or(&dir).to_str().unwrap_or("")]).spawn();
    }

    Ok(target.to_string_lossy().to_string())
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(BackendProcess(Mutex::new(None)))
        .invoke_handler(tauri::generate_handler![save_download])
        .setup(|app| {
            #[cfg(not(debug_assertions))]
            {
                let handle = app.handle().clone();
                match spawn_backend(&handle) {
                    Ok(child) => {
                        let state = app.state::<BackendProcess>();
                        *state.0.lock().unwrap() = Some(child);

                        let port = std::env::var("LOTTERY_PORT")
                            .ok()
                            .and_then(|s| s.parse::<u16>().ok())
                            .unwrap_or(DEFAULT_BACKEND_PORT);
                        if wait_backend_ready(port) {
                            println!("[backend] 已就绪 (port {port})");
                        } else {
                            eprintln!(
                                "[backend] 等待就绪超时（>{:?}），窗口仍将打开，请检查后端日志",
                                BACKEND_READY_TIMEOUT
                            );
                        }
                    }
                    Err(err) => eprintln!("[backend] 启动失败：{err}"),
                }
            }
            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(|app_handle, event| {
            if let RunEvent::ExitRequested { .. } | RunEvent::Exit = event {
                let state = app_handle.state::<BackendProcess>();
                let child = state.0.lock().unwrap().take();
                if let Some(mut child) = child {
                    let _ = child.kill();
                    let _ = child.wait();
                }
            }
        });
}
