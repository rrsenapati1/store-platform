mod runtime_paths;
mod runtime_cache;
mod runtime_control_plane_origin;
mod runtime_hub_identity;
mod runtime_hub_service;
mod runtime_spoke_registry;
mod runtime_local_auth;
mod runtime_session;
mod runtime_shell;

use runtime_cache::{
    cmd_clear_store_runtime_cache, cmd_get_store_runtime_cache_status, cmd_load_store_runtime_cache,
    cmd_save_store_runtime_cache,
};
use runtime_hub_identity::{
    cmd_clear_store_runtime_hub_identity, cmd_load_store_runtime_hub_identity,
    cmd_save_store_runtime_hub_identity,
};
use runtime_local_auth::{
    cmd_clear_store_runtime_local_auth, cmd_load_store_runtime_local_auth,
    cmd_save_store_runtime_local_auth,
};
use runtime_session::{
    cmd_clear_store_runtime_session, cmd_load_store_runtime_session, cmd_save_store_runtime_session,
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
            cmd_load_store_runtime_session,
            cmd_save_store_runtime_session,
            cmd_clear_store_runtime_session,
            cmd_load_store_runtime_hub_identity,
            cmd_save_store_runtime_hub_identity,
            cmd_clear_store_runtime_hub_identity,
            cmd_load_store_runtime_local_auth,
            cmd_save_store_runtime_local_auth,
            cmd_clear_store_runtime_local_auth,
            cmd_get_store_runtime_shell_status,
        ])
        .run(tauri::generate_context!())
        .expect("failed to run store desktop runtime shell");
}
