use tauri::{AppHandle, Manager, Position, Size, WebviewWindow};

use crate::persistence::{load_state_from_disk, save_state_to_disk};

pub fn clamp_bounds_to_monitor(
    window: &WebviewWindow,
    target_x: i32,
    target_y: i32,
    target_width: u32,
    target_height: u32,
) -> (i32, i32, u32, u32) {
    if let Ok(Some(monitor)) = window.current_monitor() {
        let mon_pos = monitor.position();
        let mon_size = monitor.size();
        let mon_scale = monitor.scale_factor();

        let mon_width_logical = (mon_size.width as f64 / mon_scale) as i32;
        let mon_height_logical = (mon_size.height as f64 / mon_scale) as i32;
        let mon_x_logical = (mon_pos.x as f64 / mon_scale) as i32;
        let mon_y_logical = (mon_pos.y as f64 / mon_scale) as i32;

        let w = target_width.max(200) as i32;
        let h = target_height.max(300) as i32;

        let min_x = mon_x_logical;
        let max_x = mon_x_logical + mon_width_logical - w;
        let min_y = mon_y_logical;
        let max_y = mon_y_logical + mon_height_logical - h;

        let safe_x = target_x.clamp(min_x, max_x.max(min_x));
        let safe_y = target_y.clamp(min_y, max_y.max(min_y));

        (safe_x, safe_y, w as u32, h as u32)
    } else {
        (target_x.max(0), target_y.max(0), target_width, target_height)
    }
}

#[tauri::command]
pub fn start_drag(window: WebviewWindow) -> Result<(), String> {
    window.start_dragging().map_err(|e| e.to_string())
}

#[tauri::command]
pub fn set_window_size(app: AppHandle, width: u32, height: u32) -> Result<(), String> {
    if let Some(window) = app.get_webview_window("main") {
        window
            .set_size(Size::Logical(tauri::LogicalSize {
                width: width as f64,
                height: height as f64,
            }))
            .map_err(|e| e.to_string())?;

        let mut state = load_state_from_disk(&app);
        state.width = width;
        state.height = height;
        let _ = save_state_to_disk(&app, &state);
        Ok(())
    } else {
        Err("Main window not found".to_string())
    }
}

#[tauri::command]
pub fn set_window_position(app: AppHandle, x: i32, y: i32) -> Result<(), String> {
    if let Some(window) = app.get_webview_window("main") {
        window
            .set_position(Position::Logical(tauri::LogicalPosition {
                x: x as f64,
                y: y as f64,
            }))
            .map_err(|e| e.to_string())?;

        let mut state = load_state_from_disk(&app);
        state.x = x;
        state.y = y;
        let _ = save_state_to_disk(&app, &state);
        Ok(())
    } else {
        Err("Main window not found".to_string())
    }
}

#[tauri::command]
pub fn set_always_on_top(app: AppHandle, enabled: bool) -> Result<(), String> {
    if let Some(window) = app.get_webview_window("main") {
        window.set_always_on_top(enabled).map_err(|e| e.to_string())?;

        let mut state = load_state_from_disk(&app);
        state.always_on_top = enabled;
        let _ = save_state_to_disk(&app, &state);
        Ok(())
    } else {
        Err("Main window not found".to_string())
    }
}

#[tauri::command]
pub fn toggle_window_visibility(app: AppHandle) -> Result<(), String> {
    if let Some(window) = app.get_webview_window("main") {
        let is_visible = window.is_visible().unwrap_or(true);
        if is_visible {
            window.hide().map_err(|e| e.to_string())?;
        } else {
            window.show().map_err(|e| e.to_string())?;
            let _ = window.set_focus();
        }

        let mut state = load_state_from_disk(&app);
        state.visible = !is_visible;
        let _ = save_state_to_disk(&app, &state);
        Ok(())
    } else {
        Err("Main window not found".to_string())
    }
}

#[tauri::command]
pub fn show_window(app: AppHandle) -> Result<(), String> {
    if let Some(window) = app.get_webview_window("main") {
        window.show().map_err(|e| e.to_string())?;
        let _ = window.set_focus();

        let mut state = load_state_from_disk(&app);
        state.visible = true;
        let _ = save_state_to_disk(&app, &state);
        Ok(())
    } else {
        Err("Main window not found".to_string())
    }
}

#[tauri::command]
pub fn hide_window(app: AppHandle) -> Result<(), String> {
    if let Some(window) = app.get_webview_window("main") {
        window.hide().map_err(|e| e.to_string())?;

        let mut state = load_state_from_disk(&app);
        state.visible = false;
        let _ = save_state_to_disk(&app, &state);
        Ok(())
    } else {
        Err("Main window not found".to_string())
    }
}
