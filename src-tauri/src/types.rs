use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct PersistedWindowState {
    pub x: i32,
    pub y: i32,
    pub width: u32,
    pub height: u32,
    pub size_preset: String,
    pub always_on_top: bool,
    pub visible: bool,
}

impl Default for PersistedWindowState {
    fn default() -> Self {
        Self {
            x: 100,
            y: 100,
            width: 280,
            height: 420,
            size_preset: "compact".to_string(),
            always_on_top: true,
            visible: true,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct PlatformInfo {
    pub os: String,
    pub arch: String,
    pub version: String,
    pub is_tauri: bool,
}
