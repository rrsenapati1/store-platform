use crate::runtime_paths::runtime_home_dir;
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};

const STORE_RUNTIME_HARDWARE_FILE_NAME: &str = "store-runtime-hardware.json";

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct StoreRuntimePrinterRecord {
    pub name: String,
    pub label: String,
    pub is_default: bool,
    pub is_online: Option<bool>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct StoreRuntimeHardwareProfileRecord {
    pub receipt_printer_name: Option<String>,
    pub label_printer_name: Option<String>,
    pub updated_at: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct StoreRuntimeHardwareProfileInput {
    pub receipt_printer_name: Option<String>,
    pub label_printer_name: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct StoreRuntimeHardwareDiagnostics {
    pub scanner_capture_state: String,
    pub last_print_status: Option<String>,
    pub last_print_message: Option<String>,
    pub last_printed_at: Option<String>,
    pub last_scan_at: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct StoreRuntimeHardwareStatus {
    pub bridge_state: String,
    pub printers: Vec<StoreRuntimePrinterRecord>,
    pub profile: StoreRuntimeHardwareProfileRecord,
    pub diagnostics: StoreRuntimeHardwareDiagnostics,
}

fn runtime_hardware_path() -> PathBuf {
    runtime_home_dir().join(STORE_RUNTIME_HARDWARE_FILE_NAME)
}

fn current_timestamp_string() -> String {
    let seconds = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs();
    seconds.to_string()
}

fn default_hardware_profile() -> StoreRuntimeHardwareProfileRecord {
    StoreRuntimeHardwareProfileRecord {
        receipt_printer_name: None,
        label_printer_name: None,
        updated_at: None,
    }
}

fn default_hardware_diagnostics() -> StoreRuntimeHardwareDiagnostics {
    StoreRuntimeHardwareDiagnostics {
        scanner_capture_state: "ready".to_string(),
        last_print_status: None,
        last_print_message: None,
        last_printed_at: None,
        last_scan_at: None,
    }
}

fn resolve_hardware_status(profile: StoreRuntimeHardwareProfileRecord) -> StoreRuntimeHardwareStatus {
    StoreRuntimeHardwareStatus {
        bridge_state: "ready".to_string(),
        printers: Vec::new(),
        profile,
        diagnostics: default_hardware_diagnostics(),
    }
}

fn load_hardware_profile(path: &Path) -> Result<StoreRuntimeHardwareProfileRecord, String> {
    if !path.exists() {
        return Ok(default_hardware_profile());
    }
    let raw = fs::read_to_string(path).map_err(|err| format!("Failed to read {}: {err}", path.display()))?;
    match serde_json::from_str::<StoreRuntimeHardwareProfileRecord>(&raw) {
        Ok(profile) => Ok(profile),
        Err(_) => {
            clear_hardware_profile(path)?;
            Ok(default_hardware_profile())
        }
    }
}

fn save_hardware_profile_to_path(
    path: &Path,
    profile: StoreRuntimeHardwareProfileInput,
) -> Result<StoreRuntimeHardwareStatus, String> {
    let next_profile = StoreRuntimeHardwareProfileRecord {
        receipt_printer_name: profile.receipt_printer_name,
        label_printer_name: profile.label_printer_name,
        updated_at: Some(current_timestamp_string()),
    };
    let encoded = serde_json::to_string_pretty(&next_profile)
        .map_err(|err| format!("Failed to encode runtime hardware profile {}: {err}", path.display()))?;
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|err| format!("Failed to prepare {}: {err}", parent.display()))?;
    }
    let temp_path = path.with_extension("tmp");
    fs::write(&temp_path, encoded)
        .map_err(|err| format!("Failed to write {}: {err}", temp_path.display()))?;
    fs::rename(&temp_path, path)
        .map_err(|err| format!("Failed to finalize {}: {err}", path.display()))?;
    Ok(resolve_hardware_status(next_profile))
}

fn clear_hardware_profile(path: &Path) -> Result<(), String> {
    if !path.exists() {
        return Ok(());
    }
    fs::remove_file(path).map_err(|err| format!("Failed to remove {}: {err}", path.display()))
}

fn load_hardware_status(path: &Path) -> Result<StoreRuntimeHardwareStatus, String> {
    Ok(resolve_hardware_status(load_hardware_profile(path)?))
}

#[tauri::command]
pub fn cmd_get_store_runtime_hardware_status() -> Result<StoreRuntimeHardwareStatus, String> {
    load_hardware_status(&runtime_hardware_path())
}

#[tauri::command]
pub fn cmd_save_store_runtime_hardware_profile(
    profile: StoreRuntimeHardwareProfileInput,
) -> Result<StoreRuntimeHardwareStatus, String> {
    save_hardware_profile_to_path(&runtime_hardware_path(), profile)
}

#[tauri::command]
pub fn cmd_clear_store_runtime_hardware_profile() -> Result<(), String> {
    clear_hardware_profile(&runtime_hardware_path())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::runtime_paths::runtime_home_test_guard;
    use std::env;
    use std::fs;
    use uuid::Uuid;

    #[test]
    fn runtime_hardware_status_defaults_to_empty_profile() {
        let _guard = runtime_home_test_guard()
            .lock()
            .expect("lock runtime-home guard");
        let previous_runtime_home = env::var("STORE_RUNTIME_HOME").ok();
        let runtime_home = env::temp_dir().join(format!(
            "store-runtime-hardware-store-{}",
            Uuid::new_v4()
        ));
        fs::create_dir_all(&runtime_home).expect("create runtime home");
        env::set_var(
            "STORE_RUNTIME_HOME",
            runtime_home.to_string_lossy().to_string(),
        );

        let status = load_hardware_status(&runtime_hardware_path()).expect("load hardware status");

        assert_eq!(status.bridge_state, "ready");
        assert_eq!(status.printers.len(), 0);
        assert_eq!(status.profile.receipt_printer_name, None);
        assert_eq!(status.profile.label_printer_name, None);
        assert_eq!(status.diagnostics.scanner_capture_state, "ready");

        if let Some(value) = previous_runtime_home {
            env::set_var("STORE_RUNTIME_HOME", value);
        } else {
            env::remove_var("STORE_RUNTIME_HOME");
        }
        let _ = fs::remove_dir_all(runtime_home);
    }

    #[test]
    fn runtime_hardware_profile_round_trips_through_native_store() {
        let _guard = runtime_home_test_guard()
            .lock()
            .expect("lock runtime-home guard");
        let previous_runtime_home = env::var("STORE_RUNTIME_HOME").ok();
        let runtime_home = env::temp_dir().join(format!(
            "store-runtime-hardware-store-round-trip-{}",
            Uuid::new_v4()
        ));
        fs::create_dir_all(&runtime_home).expect("create runtime home");
        env::set_var(
            "STORE_RUNTIME_HOME",
            runtime_home.to_string_lossy().to_string(),
        );

        let saved = save_hardware_profile_to_path(
            &runtime_hardware_path(),
            StoreRuntimeHardwareProfileInput {
                receipt_printer_name: Some("Thermal-01".to_string()),
                label_printer_name: Some("Label-01".to_string()),
            },
        )
        .expect("save hardware profile");
        let loaded = load_hardware_status(&runtime_hardware_path()).expect("load hardware status");

        assert_eq!(saved.profile.receipt_printer_name.as_deref(), Some("Thermal-01"));
        assert_eq!(saved.profile.label_printer_name.as_deref(), Some("Label-01"));
        assert_eq!(loaded.profile.receipt_printer_name.as_deref(), Some("Thermal-01"));
        assert_eq!(loaded.profile.label_printer_name.as_deref(), Some("Label-01"));
        assert!(loaded.profile.updated_at.is_some());

        if let Some(value) = previous_runtime_home {
            env::set_var("STORE_RUNTIME_HOME", value);
        } else {
            env::remove_var("STORE_RUNTIME_HOME");
        }
        let _ = fs::remove_dir_all(runtime_home);
    }
}
