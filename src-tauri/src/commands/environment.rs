use serde::{Deserialize, Serialize};
use std::env;
use std::path::PathBuf;
use tauri::Manager;

#[derive(Debug, Serialize, Clone)]
pub struct EnvironmentInfo {
    pub os: String,
    pub architecture: String,
    pub family: String,
    pub current_directory: Option<String>,
    pub home_directory: Option<String>,
    pub temp_directory: String,
    pub app_data_directory: Option<String>,
    pub config_directory: Option<String>,
    pub executable_directory: Option<String>,
}

#[derive(Debug, Serialize, Clone)]
pub struct EnvironmentVariable {
    pub key: String,
    pub value: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct EnvironmentVariableRequest {
    pub key: String,
}

#[derive(Debug, Serialize, Clone)]
pub struct EnvironmentStatus {
    pub ready: bool,
    pub platform: String,
    pub architecture: String,
}

#[tauri::command]
pub fn get_environment_info(
    app: tauri::AppHandle,
) -> Result<EnvironmentInfo, String> {
    let app_data_directory = app
        .path()
        .app_data_dir()
        .ok()
        .map(|path| path.to_string_lossy().to_string());

    let config_directory = app
        .path()
        .app_config_dir()
        .ok()
        .map(|path| path.to_string_lossy().to_string());

    let executable_directory = env::current_exe()
        .ok()
        .and_then(|path| path.parent().map(PathBuf::from))
        .map(|path| path.to_string_lossy().to_string());

    Ok(EnvironmentInfo {
        os: env::consts::OS.to_string(),
        architecture: env::consts::ARCH.to_string(),
        family: env::consts::FAMILY.to_string(),
        current_directory: env::current_dir()
            .ok()
            .map(|path| path.to_string_lossy().to_string()),
        home_directory: env::var("HOME")
            .or_else(|_| env::var("USERPROFILE"))
            .ok(),
        temp_directory: env::temp_dir()
            .to_string_lossy()
            .to_string(),
        app_data_directory,
        config_directory,
        executable_directory,
    })
}

#[tauri::command]
pub fn get_environment_status() -> Result<EnvironmentStatus, String> {
    Ok(EnvironmentStatus {
        ready: true,
        platform: env::consts::OS.to_string(),
        architecture: env::consts::ARCH.to_string(),
    })
}

#[tauri::command]
pub fn get_environment_variable(
    request: EnvironmentVariableRequest,
) -> Result<EnvironmentVariable, String> {
    let key = request.key.trim();

    if key.is_empty() {
        return Err("Environment variable key cannot be empty.".to_string());
    }

    if !is_safe_environment_key(key) {
        return Err("Invalid environment variable key.".to_string());
    }

    Ok(EnvironmentVariable {
        key: key.to_string(),
        value: env::var(key).ok(),
    })
}

/// Returns only explicitly requested environment variables.
///
/// This prevents accidentally exposing the complete process environment
/// to the frontend.
#[tauri::command]
pub fn get_environment_variables(
    keys: Vec<String>,
) -> Result<Vec<EnvironmentVariable>, String> {
    if keys.len() > 100 {
        return Err("Too many environment variable keys requested.".to_string());
    }

    let mut result = Vec::new();

    for key in keys {
        let key = key.trim();

        if key.is_empty() {
            continue;
        }

        if !is_safe_environment_key(key) {
            continue;
        }

        result.push(EnvironmentVariable {
            key: key.to_string(),
            value: env::var(key).ok(),
        });
    }

    Ok(result)
}

fn is_safe_environment_key(key: &str) -> bool {
    key.chars().enumerate().all(|(index, character)| {
        if index == 0 {
            character.is_ascii_alphabetic() || character == '_'
        } else {
            character.is_ascii_alphanumeric() || character == '_'
        }
    })
}