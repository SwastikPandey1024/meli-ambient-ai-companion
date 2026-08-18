use std::fs;
use std::path::PathBuf;
use tauri::{AppHandle, Manager};

use crate::types::PersistedWindowState;

pub fn get_persistence_path(app: &AppHandle) -> Option<PathBuf> {
    if let Ok(app_dir) = app.path().app_config_dir() {
        let _ = fs::create_dir_all(&app_dir);
        Some(app_dir.join("window_state.json"))
    } else {
        None
    }
}

pub fn load_state_from_disk(app: &AppHandle) -> PersistedWindowState {
    if let Some(path) = get_persistence_path(app) {
        if path.exists() {
            if let Ok(content) = fs::read_to_string(&path) {
                if let Ok(state) = serde_json::from_str::<PersistedWindowState>(&content) {
                    return state;
                }
            }
        }
    }
    PersistedWindowState::default()
}

pub fn save_state_to_disk(app: &AppHandle, state: &PersistedWindowState) -> Result<(), String> {
    if let Some(path) = get_persistence_path(app) {
        let serialized = serde_json::to_string_pretty(state).map_err(|e| e.to_string())?;
        fs::write(&path, serialized).map_err(|e| e.to_string())?;
        Ok(())
    } else {
        Err("Could not determine app config directory".to_string())
    }
}

#[tauri::command]
pub fn get_window_state(app: AppHandle) -> PersistedWindowState {
    load_state_from_disk(&app)
}

#[tauri::command]
pub fn save_window_state(app: AppHandle, state: PersistedWindowState) -> Result<(), String> {
    save_state_to_disk(&app, &state)
}
