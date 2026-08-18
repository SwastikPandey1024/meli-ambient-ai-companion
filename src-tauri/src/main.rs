// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod persistence;
mod tray;
mod types;
mod window_manager;

use persistence::{get_window_state, load_state_from_disk, save_window_state};
use tauri::{Manager, Position, Size};
use types::PlatformInfo;
use window_manager::{
    clamp_bounds_to_monitor, hide_window, set_always_on_top, set_window_position, set_window_size,
    show_window, start_drag, toggle_window_visibility,
};

#[tauri::command]
fn get_platform_info() -> PlatformInfo {
    PlatformInfo {
        os: std::env::consts::OS.to_string(),
        arch: std::env::consts::ARCH.to_string(),
        version: env!("CARGO_PKG_VERSION").to_string(),
        is_tauri: true,
    }
}

fn main() {
    tauri::Builder::default()
        .setup(|app| {
            // 1. Setup System Tray
            if let Err(e) = tray::setup_tray(app.handle()) {
                eprintln!("[Tauri] Tray initialization warning: {}", e);
            }

            // 2. Load Persisted State & Safely Clamp to Monitor
            let handle = app.handle().clone();
            if let Some(window) = handle.get_webview_window("main") {
                let state = load_state_from_disk(&handle);
                let (safe_x, safe_y, safe_w, safe_h) = clamp_bounds_to_monitor(
                    &window,
                    state.x,
                    state.y,
                    state.width,
                    state.height,
                );

                let _ = window.set_position(Position::Logical(tauri::LogicalPosition {
                    x: safe_x as f64,
                    y: safe_y as f64,
                }));
                let _ = window.set_size(Size::Logical(tauri::LogicalSize {
                    width: safe_w as f64,
                    height: safe_h as f64,
                }));
                let _ = window.set_always_on_top(state.always_on_top);

                // Always make window visible and bring to focus on startup
                let _ = window.show();
                let _ = window.set_focus();
            }

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            get_platform_info,
            get_window_state,
            save_window_state,
            start_drag,
            set_window_size,
            set_window_position,
            set_always_on_top,
            toggle_window_visibility,
            show_window,
            hide_window,
        ])
        .run(tauri::generate_context!())
        .expect("error while running Meli companion application");
}
