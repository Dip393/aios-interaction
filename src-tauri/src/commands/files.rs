use serde::Serialize;
use std::fs;
use std::path::{Path, PathBuf};

#[derive(Debug, Serialize, Clone)]
pub struct FileInfo {
    pub path: String,
    pub name: String,
    pub is_file: bool,
    pub is_directory: bool,
    pub size: u64,
    pub readonly: bool,
}

#[derive(Debug, Serialize, Clone)]
pub struct DirectoryEntry {
    pub name: String,
    pub path: String,
    pub is_file: bool,
    pub is_directory: bool,
    pub size: u64,
}

#[derive(Debug, Serialize, Clone)]
pub struct FileOperationResult {
    pub success: bool,
    pub path: String,
    pub message: String,
}

#[tauri::command]
pub fn file_exists(path: String) -> Result<bool, String> {
    Ok(Path::new(&path).exists())
}

#[tauri::command]
pub fn read_file(path: String) -> Result<String, String> {
    validate_path(&path)?;

    fs::read_to_string(&path)
        .map_err(|error| format!("Failed to read file: {error}"))
}

#[tauri::command]
pub fn write_file(path: String, content: String) -> Result<FileOperationResult, String> {
    validate_path(&path)?;

    let target = PathBuf::from(&path);

    if let Some(parent) = target.parent() {
        if !parent.as_os_str().is_empty() {
            fs::create_dir_all(parent)
                .map_err(|error| format!("Failed to create parent directory: {error}"))?;
        }
    }

    fs::write(&target, content)
        .map_err(|error| format!("Failed to write file: {error}"))?;

    Ok(FileOperationResult {
        success: true,
        path,
        message: "File written successfully.".to_string(),
    })
}

#[tauri::command]
pub fn create_directory(path: String) -> Result<FileOperationResult, String> {
    validate_path(&path)?;

    fs::create_dir_all(&path)
        .map_err(|error| format!("Failed to create directory: {error}"))?;

    Ok(FileOperationResult {
        success: true,
        path,
        message: "Directory created successfully.".to_string(),
    })
}

#[tauri::command]
pub fn list_directory(path: String) -> Result<Vec<DirectoryEntry>, String> {
    validate_path(&path)?;

    let directory = Path::new(&path);

    if !directory.exists() {
        return Err("Directory does not exist.".to_string());
    }

    if !directory.is_dir() {
        return Err("Provided path is not a directory.".to_string());
    }

    let entries = fs::read_dir(directory)
        .map_err(|error| format!("Failed to read directory: {error}"))?;

    let mut result = Vec::new();

    for entry in entries {
        let entry = entry
            .map_err(|error| format!("Failed to read directory entry: {error}"))?;

        let metadata = entry
            .metadata()
            .map_err(|error| format!("Failed to read metadata: {error}"))?;

        let entry_path = entry.path();

        result.push(DirectoryEntry {
            name: entry.file_name().to_string_lossy().to_string(),
            path: entry_path.to_string_lossy().to_string(),
            is_file: metadata.is_file(),
            is_directory: metadata.is_dir(),
            size: if metadata.is_file() {
                metadata.len()
            } else {
                0
            },
        });
    }

    result.sort_by(|a, b| {
        a.is_file
            .cmp(&b.is_file)
            .then_with(|| a.name.to_lowercase().cmp(&b.name.to_lowercase()))
    });

    Ok(result)
}

#[tauri::command]
pub fn get_file_info(path: String) -> Result<FileInfo, String> {
    validate_path(&path)?;

    let target = Path::new(&path);

    let metadata = fs::metadata(target)
        .map_err(|error| format!("Failed to read metadata: {error}"))?;

    let name = target
        .file_name()
        .map(|value| value.to_string_lossy().to_string())
        .unwrap_or_else(|| target.to_string_lossy().to_string());

    Ok(FileInfo {
        path,
        name,
        is_file: metadata.is_file(),
        is_directory: metadata.is_dir(),
        size: if metadata.is_file() {
            metadata.len()
        } else {
            0
        },
        readonly: metadata.permissions().readonly(),
    })
}

#[tauri::command]
pub fn copy_file(
    source: String,
    destination: String,
) -> Result<FileOperationResult, String> {
    validate_path(&source)?;
    validate_path(&destination)?;

    let source_path = Path::new(&source);

    if !source_path.exists() {
        return Err("Source path does not exist.".to_string());
    }

    if !source_path.is_file() {
        return Err("Source path is not a file.".to_string());
    }

    let destination_path = PathBuf::from(&destination);

    if let Some(parent) = destination_path.parent() {
        if !parent.as_os_str().is_empty() {
            fs::create_dir_all(parent)
                .map_err(|error| format!("Failed to create destination directory: {error}"))?;
        }
    }

    fs::copy(source_path, &destination_path)
        .map_err(|error| format!("Failed to copy file: {error}"))?;

    Ok(FileOperationResult {
        success: true,
        path: destination,
        message: "File copied successfully.".to_string(),
    })
}

#[tauri::command]
pub fn move_file(
    source: String,
    destination: String,
) -> Result<FileOperationResult, String> {
    validate_path(&source)?;
    validate_path(&destination)?;

    let source_path = Path::new(&source);

    if !source_path.exists() {
        return Err("Source path does not exist.".to_string());
    }

    let destination_path = PathBuf::from(&destination);

    if let Some(parent) = destination_path.parent() {
        if !parent.as_os_str().is_empty() {
            fs::create_dir_all(parent)
                .map_err(|error| format!("Failed to create destination directory: {error}"))?;
        }
    }

    fs::rename(source_path, &destination_path)
        .map_err(|error| format!("Failed to move path: {error}"))?;

    Ok(FileOperationResult {
        success: true,
        path: destination,
        message: "Path moved successfully.".to_string(),
    })
}

#[tauri::command]
pub fn delete_file(path: String) -> Result<FileOperationResult, String> {
    validate_path(&path)?;

    let target = Path::new(&path);

    if !target.exists() {
        return Err("Path does not exist.".to_string());
    }

    if target.is_dir() {
        return Err(
            "Directory deletion is disabled through this command. Use a dedicated directory deletion flow."
                .to_string(),
        );
    }

    fs::remove_file(target)
        .map_err(|error| format!("Failed to delete file: {error}"))?;

    Ok(FileOperationResult {
        success: true,
        path,
        message: "File deleted successfully.".to_string(),
    })
}

fn validate_path(path: &str) -> Result<(), String> {
    let trimmed = path.trim();

    if trimmed.is_empty() {
        return Err("Path cannot be empty.".to_string());
    }

    if trimmed.contains('\0') {
        return Err("Path contains an invalid null character.".to_string());
    }

    Ok(())
}