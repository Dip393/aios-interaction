use serde::Serialize;
use tauri::{AppHandle, Emitter};

#[derive(Debug, Serialize, Clone)]
pub struct NotificationResult {
    pub success: bool,
    pub title: String,
    pub body: String,
}

#[tauri::command]
pub fn show_notification(
    app: AppHandle,
    title: String,
    body: String,
) -> Result<NotificationResult, String> {
    let title = sanitize_notification_text(&title);
    let body = sanitize_notification_text(&body);

    if title.is_empty() {
        return Err("Notification title cannot be empty.".to_string());
    }

    /*
     * We emit an application event here instead of hard-coding a specific
     * operating-system notification provider.
     *
     * The frontend can listen for:
     *
     *   "aios://notification"
     *
     * and display a native/web notification depending on the platform.
     *
     * A dedicated Tauri notification plugin can later replace this bridge
     * without changing the AIOS command API.
     */
    app.emit(
        "aios://notification",
        serde_json::json!({
            "title": title,
            "body": body,
        }),
    )
    .map_err(|error| format!("Failed to emit notification event: {error}"))?;

    Ok(NotificationResult {
        success: true,
        title,
        body,
    })
}

#[tauri::command]
pub fn notification_permission_status() -> Result<String, String> {
    /*
     * Permission management is intentionally kept outside the core command
     * layer because native permission APIs differ between platforms.
     */
    Ok("unknown".to_string())
}

fn sanitize_notification_text(value: &str) -> String {
    value
        .trim()
        .chars()
        .filter(|character| *character != '\0')
        .take(4000)
        .collect()
}