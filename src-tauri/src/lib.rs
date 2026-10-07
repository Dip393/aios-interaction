#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod commands;

pub fn run() {
    tauri::Builder::default()
        // Native mouse controller state
        .manage(
            commands::MouseController::new()
                .expect("Failed to initialize native mouse controller"),
        )
        .invoke_handler(tauri::generate_handler![
            // System
            commands::get_system_info,
            commands::get_system_status,
            commands::open_url,
            commands::open_path,

            // Files
            commands::file_exists,
            commands::read_file,
            commands::write_file,
            commands::create_directory,
            commands::list_directory,
            commands::get_file_info,
            commands::copy_file,
            commands::move_file,
            commands::delete_file,

            // Notifications
            commands::show_notification,
            commands::notification_permission_status,

            // Environment
            commands::get_environment_info,
            commands::get_environment_status,
            commands::get_environment_variable,
            commands::get_environment_variables,

            // Vision / Native Mouse Control
            commands::vision_mouse_move,
            commands::vision_mouse_click,
            commands::vision_mouse_button,
            commands::vision_mouse_scroll,
            commands::vision_mouse_position,
            commands::vision_mouse_screen_size,
        ])
        .run(tauri::generate_context!())
        .expect("error while running AIOS");
}