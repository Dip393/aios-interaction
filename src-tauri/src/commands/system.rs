use serde::Serialize;
use std::env;
use std::process::Command;

#[derive(Debug, Serialize, Clone)]
pub struct SystemInfo {
    pub os: String,
    pub architecture: String,
    pub family: String,
    pub hostname: Option<String>,
    pub username: Option<String>,
    pub home_directory: Option<String>,
    pub current_directory: Option<String>,
    pub temp_directory: Option<String>,
    pub executable: Option<String>,
}

#[derive(Debug, Serialize, Clone)]
pub struct CommandResult {
    pub success: bool,
    pub stdout: String,
    pub stderr: String,
    pub exit_code: Option<i32>,
}

#[derive(Debug, Serialize, Clone)]
pub struct SystemStatus {
    pub available: bool,
    pub platform: String,
    pub architecture: String,
}

#[tauri::command]
pub fn get_system_info() -> Result<SystemInfo, String> {
    Ok(SystemInfo {
        os: env::consts::OS.to_string(),
        architecture: env::consts::ARCH.to_string(),
        family: env::consts::FAMILY.to_string(),
        hostname: hostname(),
        username: username(),
        home_directory: env::var("HOME")
            .or_else(|_| env::var("USERPROFILE"))
            .ok(),
        current_directory: env::current_dir()
            .ok()
            .map(|path| path.to_string_lossy().to_string()),
        temp_directory: env::temp_dir()
            .to_string_lossy()
            .to_string()
            .into(),
        executable: env::current_exe()
            .ok()
            .map(|path| path.to_string_lossy().to_string()),
    })
}

#[tauri::command]
pub fn get_system_status() -> Result<SystemStatus, String> {
    Ok(SystemStatus {
        available: true,
        platform: env::consts::OS.to_string(),
        architecture: env::consts::ARCH.to_string(),
    })
}

/// Opens a URL using the operating system's default handler.
///
/// This intentionally accepts only http/https URLs.
#[tauri::command]
pub fn open_url(url: String) -> Result<(), String> {
    let trimmed = url.trim();

    if !(trimmed.starts_with("https://") || trimmed.starts_with("http://")) {
        return Err("Only HTTP and HTTPS URLs are allowed.".to_string());
    }

    #[cfg(target_os = "windows")]
    {
        Command::new("cmd")
            .args(["/C", "start", "", trimmed])
            .spawn()
            .map_err(|error| format!("Failed to open URL: {error}"))?;
    }

    #[cfg(target_os = "macos")]
    {
        Command::new("open")
            .arg(trimmed)
            .spawn()
            .map_err(|error| format!("Failed to open URL: {error}"))?;
    }

    #[cfg(target_os = "linux")]
    {
        Command::new("xdg-open")
            .arg(trimmed)
            .spawn()
            .map_err(|error| format!("Failed to open URL: {error}"))?;
    }

    Ok(())
}

/// Opens a directory or file with the operating system's default handler.
#[tauri::command]
pub fn open_path(path: String) -> Result<(), String> {
    let target = std::path::PathBuf::from(path);

    if !target.exists() {
        return Err("The requested path does not exist.".to_string());
    }

    #[cfg(target_os = "windows")]
    {
        Command::new("explorer")
            .arg(&target)
            .spawn()
            .map_err(|error| format!("Failed to open path: {error}"))?;
    }

    #[cfg(target_os = "macos")]
    {
        Command::new("open")
            .arg(&target)
            .spawn()
            .map_err(|error| format!("Failed to open path: {error}"))?;
    }

    #[cfg(target_os = "linux")]
    {
        Command::new("xdg-open")
            .arg(&target)
            .spawn()
            .map_err(|error| format!("Failed to open path: {error}"))?;
    }

    Ok(())
}

fn hostname() -> Option<String> {
    #[cfg(target_os = "windows")]
    {
        env::var("COMPUTERNAME").ok()
    }

    #[cfg(not(target_os = "windows"))]
    {
        env::var("HOSTNAME").ok()
    }
}

fn username() -> Option<String> {
    env::var("USERNAME")
        .or_else(|_| env::var("USER"))
        .ok()
}