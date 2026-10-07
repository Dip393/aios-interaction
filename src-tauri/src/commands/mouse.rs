use enigo::{
    Button,
    Coordinate,
    Direction,
    Enigo,
    Mouse,
    Settings,
};
use serde::Serialize;
use std::sync::Mutex;
use tauri::State;

#[derive(Debug, Serialize)]
pub struct MousePosition {
    pub x: i32,
    pub y: i32,
}

#[derive(Debug, Serialize)]
pub struct MouseScreenSize {
    pub width: i32,
    pub height: i32,
}

#[derive(Debug, Serialize)]
pub struct MouseCommandResult {
    pub success: bool,
    pub message: String,
}

pub struct MouseController {
    enigo: Mutex<Enigo>,
}

impl MouseController {
    pub fn new() -> Result<Self, String> {
        let enigo = Enigo::new(&Settings::default())
            .map_err(|error| format!("Failed to initialize mouse controller: {error}"))?;

        Ok(Self {
            enigo: Mutex::new(enigo),
        })
    }
}

#[tauri::command]
pub fn vision_mouse_move(
    state: State<'_, MouseController>,
    x: i32,
    y: i32,
) -> Result<MouseCommandResult, String> {
    if x < 0 || y < 0 {
        return Err("Mouse coordinates cannot be negative.".to_string());
    }

    let mut enigo = state
        .enigo
        .lock()
        .map_err(|_| "Failed to lock mouse controller.".to_string())?;

    enigo
        .move_mouse(x, y, Coordinate::Abs)
        .map_err(|error| format!("Failed to move mouse: {error}"))?;

    Ok(MouseCommandResult {
        success: true,
        message: format!("Mouse moved to ({x}, {y})"),
    })
}

#[tauri::command]
pub fn vision_mouse_click(
    state: State<'_, MouseController>,
) -> Result<MouseCommandResult, String> {
    let mut enigo = state
        .enigo
        .lock()
        .map_err(|_| "Failed to lock mouse controller.".to_string())?;

    enigo
        .button(Button::Left, Direction::Click)
        .map_err(|error| format!("Failed to click mouse: {error}"))?;

    Ok(MouseCommandResult {
        success: true,
        message: "Left mouse button clicked.".to_string(),
    })
}

#[tauri::command]
pub fn vision_mouse_button(
    state: State<'_, MouseController>,
    button: String,
    pressed: bool,
) -> Result<MouseCommandResult, String> {
    let mouse_button = match button.to_lowercase().as_str() {
        "left" => Button::Left,
        "right" => Button::Right,
        "middle" => Button::Middle,
        _ => {
            return Err(
                "Invalid mouse button. Use left, right, or middle."
                    .to_string(),
            )
        }
    };

    let direction = if pressed {
        Direction::Press
    } else {
        Direction::Release
    };

    let mut enigo = state
        .enigo
        .lock()
        .map_err(|_| "Failed to lock mouse controller.".to_string())?;

    enigo
        .button(mouse_button, direction)
        .map_err(|error| format!("Failed to change mouse button state: {error}"))?;

    Ok(MouseCommandResult {
        success: true,
        message: format!(
            "{} mouse button {}.",
            button,
            if pressed { "pressed" } else { "released" }
        ),
    })
}

#[tauri::command]
pub fn vision_mouse_scroll(
    state: State<'_, MouseController>,
    x: i32,
    y: i32,
) -> Result<MouseCommandResult, String> {
    if x == 0 && y == 0 {
        return Ok(MouseCommandResult {
            success: true,
            message: "No scrolling requested.".to_string(),
        });
    }

    let mut enigo = state
        .enigo
        .lock()
        .map_err(|_| "Failed to lock mouse controller.".to_string())?;

    if x != 0 {
        enigo
            .scroll(x, enigo::Axis::Horizontal)
            .map_err(|error| format!("Failed to horizontal scroll: {error}"))?;
    }

    if y != 0 {
        enigo
            .scroll(y, enigo::Axis::Vertical)
            .map_err(|error| format!("Failed to vertical scroll: {error}"))?;
    }

    Ok(MouseCommandResult {
        success: true,
        message: format!("Mouse scrolled by ({x}, {y})."),
    })
}

#[tauri::command]
pub fn vision_mouse_position(
    state: State<'_, MouseController>,
) -> Result<MousePosition, String> {
    let mut enigo = state
        .enigo
        .lock()
        .map_err(|_| "Failed to lock mouse controller.".to_string())?;

    let (x, y) = enigo
        .location()
        .map_err(|error| format!("Failed to get mouse position: {error}"))?;

    Ok(MousePosition { x, y })
}

#[tauri::command]
pub fn vision_mouse_screen_size() -> Result<MouseScreenSize, String> {
    #[cfg(target_os = "windows")]
    {
        use windows_sys::Win32::UI::WindowsAndMessaging::{
            GetSystemMetrics,
            SM_CXSCREEN,
            SM_CYSCREEN,
        };

        let width = unsafe { GetSystemMetrics(SM_CXSCREEN) };
        let height = unsafe { GetSystemMetrics(SM_CYSCREEN) };

        if width <= 0 || height <= 0 {
            return Err("Unable to determine screen size.".to_string());
        }

        return Ok(MouseScreenSize { width, height });
    }

    #[cfg(not(target_os = "windows"))]
    {
        Err(
            "Screen size detection is currently implemented for Windows only."
                .to_string(),
        )
    }
}