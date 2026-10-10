// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::{Manager, WebviewUrl, WebviewWindowBuilder};

#[tauri::command]
fn open_lottery_window(
    app: tauri::AppHandle,
    event_id: u32,
) -> Result<(), String> {
    let label = format!("lottery-{}", event_id);
    if let Some(existing) = app.get_webview_window(&label) {
        let _ = existing.set_focus();
        return Ok(());
    }
    // CustomProtocol 接受完整 URL（含 tauri:// scheme 和 hash 路由）
    // External 不支持 tauri://，App(PathBuf) 无法携带 hash
    let url_str = format!("tauri://localhost/index.html#/lottery/{}", event_id);
    let url: tauri::Url = url_str
        .parse()
        .expect("大屏 URL 解析失败");
    WebviewWindowBuilder::new(
        &app,
        &label,
        WebviewUrl::CustomProtocol(url),
    )
    .title("抽奖大屏")
    .inner_size(1280.0, 800.0)
    .resizable(true)
    .center()
    .build()
    .map_err(|e| e.to_string())?;
    Ok(())
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![open_lottery_window])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
