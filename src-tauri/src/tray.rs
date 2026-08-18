use tauri::{
    menu::{Menu, MenuItem, Submenu},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
    AppHandle, Emitter, Manager,
};

pub fn setup_tray(app: &AppHandle) -> Result<(), Box<dyn std::error::Error>> {
    let show_i = MenuItem::with_id(app, "show", "Show Meli", true, None::<&str>)?;
    let hide_i = MenuItem::with_id(app, "hide", "Hide Meli", true, None::<&str>)?;
    let chat_i = MenuItem::with_id(app, "chat", "Open Chat", true, None::<&str>)?;
    let top_i = MenuItem::with_id(app, "toggle_top", "Toggle Always on Top", true, None::<&str>)?;

    let size_s = MenuItem::with_id(app, "size_compact", "Small (250px)", true, None::<&str>)?;
    let size_m = MenuItem::with_id(app, "size_default", "Medium (340px)", true, None::<&str>)?;
    let size_l = MenuItem::with_id(app, "size_large", "Large (430px)", true, None::<&str>)?;

    let size_sub = Submenu::with_items(app, "Size", true, &[&size_s, &size_m, &size_l])?;
    let quit_i = MenuItem::with_id(app, "quit", "Quit Meli", true, None::<&str>)?;

    let menu = Menu::with_items(
        app,
        &[
            &show_i,
            &hide_i,
            &chat_i,
            &top_i,
            &size_sub,
            &quit_i,
        ],
    )?;

    let tray_icon = app
        .default_window_icon()
        .cloned()
        .ok_or("No default window icon available")?;

    TrayIconBuilder::new()
        .icon(tray_icon)
        .tooltip("Meli — Ambient AI Companion")
        .menu(&menu)
        .show_menu_on_left_click(false)
        .on_menu_event(|app, event| {
            match event.id.as_ref() {
                "show" => {
                    if let Some(w) = app.get_webview_window("main") {
                        let _ = w.show();
                        let _ = w.set_focus();
                    }
                }
                "hide" => {
                    if let Some(w) = app.get_webview_window("main") {
                        let _ = w.hide();
                    }
                }
                "chat" => {
                    if let Some(w) = app.get_webview_window("main") {
                        let _ = w.show();
                        let _ = w.set_focus();
                    }
                    let _ = app.emit("tray_event", serde_json::json!({ "action": "toggle_chat" }));
                }
                "toggle_top" => {
                    if let Some(w) = app.get_webview_window("main") {
                        if let Ok(is_top) = w.is_always_on_top() {
                            let _ = w.set_always_on_top(!is_top);
                        }
                    }
                }
                "size_compact" => {
                    let _ = app.emit("tray_event", serde_json::json!({ "action": "set_size", "sizePreset": "compact" }));
                }
                "size_default" => {
                    let _ = app.emit("tray_event", serde_json::json!({ "action": "set_size", "sizePreset": "default" }));
                }
                "size_large" => {
                    let _ = app.emit("tray_event", serde_json::json!({ "action": "set_size", "sizePreset": "large" }));
                }
                "quit" => {
                    app.exit(0);
                }
                _ => {}
            }
        })
        .on_tray_icon_event(|tray, event| {
            if let TrayIconEvent::Click {
                button: MouseButton::Left,
                button_state: MouseButtonState::Up,
                ..
            } = event
            {
                let app = tray.app_handle();
                if let Some(w) = app.get_webview_window("main") {
                    if w.is_visible().unwrap_or(false) {
                        let _ = w.hide();
                    } else {
                        let _ = w.show();
                        let _ = w.set_focus();
                    }
                }
            }
        })
        .build(app)?;

    Ok(())
}
