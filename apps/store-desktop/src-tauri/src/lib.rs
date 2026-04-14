mod runtime_paths;
mod runtime_cache;
mod runtime_shell;

use runtime_cache::{
    cmd_clear_store_runtime_cache, cmd_get_store_runtime_cache_status, cmd_load_store_runtime_cache,
    cmd_save_store_runtime_cache,
};
use runtime_shell::cmd_get_store_runtime_shell_status;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            cmd_load_store_runtime_cache,
            cmd_save_store_runtime_cache,
            cmd_clear_store_runtime_cache,
            cmd_get_store_runtime_cache_status,
            cmd_get_store_runtime_shell_status,
        ])
        .run(tauri::generate_context!())
        .expect("failed to run store desktop runtime shell");
}
