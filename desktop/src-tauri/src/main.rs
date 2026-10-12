// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::sync::Mutex;
use tauri::{Manager, RunEvent};
use tauri_plugin_shell::process::CommandChild;
use tauri_plugin_shell::ShellExt;

/// 保存后端 sidecar 子进程句柄，退出时统一关闭。
struct BackendProcess(Mutex<Option<CommandChild>>);

/// 启动后端 sidecar（打包后的 FastAPI 可执行文件）。
fn spawn_backend(app: &tauri::AppHandle) -> Result<CommandChild, String> {
    let sidecar = app
        .shell()
        .sidecar("lottery-backend")
        .map_err(|e| format!("找不到后端 sidecar：{e}"))?;

    let (mut rx, child) = sidecar
        .spawn()
        .map_err(|e| format!("启动后端失败：{e}"))?;

    // 转发后端日志到控制台，便于排查
    tauri::async_runtime::spawn(async move {
        use tauri_plugin_shell::process::CommandEvent;
        while let Some(event) = rx.recv().await {
            match event {
                CommandEvent::Stdout(line) => {
                    println!("[backend] {}", String::from_utf8_lossy(&line));
                }
                CommandEvent::Stderr(line) => {
                    eprintln!("[backend] {}", String::from_utf8_lossy(&line));
                }
                CommandEvent::Terminated(payload) => {
                    eprintln!("[backend] 进程退出：{:?}", payload);
                }
                _ => {}
            }
        }
    });

    Ok(child)
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(BackendProcess(Mutex::new(None)))
        .setup(|app| {
            // 开发模式下后端通常由开发者手动启动，这里仅在 release 打包后自动拉起
            #[cfg(not(debug_assertions))]
            {
                match spawn_backend(app.handle()) {
                    Ok(child) => {
                        let state = app.state::<BackendProcess>();
                        *state.0.lock().unwrap() = Some(child);
                    }
                    Err(err) => eprintln!("[backend] 启动失败：{err}"),
                }
            }
            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(|app_handle, event| {
            // 应用退出时关闭后端进程
            if let RunEvent::ExitRequested { .. } | RunEvent::Exit = event {
                let state = app_handle.state::<BackendProcess>();
                let child = state.0.lock().unwrap().take();
                if let Some(child) = child {
                    let _ = child.kill();
                }
            }
        });
}
