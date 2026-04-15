use crate::runtime_paths::runtime_home_dir;
use crate::runtime_printer::{
    dispatch_print_job, list_printers_with_backend, PrinterBackend, StoreRuntimePrintJobInput,
    SystemPrinterBackend,
};
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
    pub scanner_transport: Option<String>,
    pub last_print_status: Option<String>,
    pub last_print_message: Option<String>,
    pub last_printed_at: Option<String>,
    pub last_scan_at: Option<String>,
    pub last_scan_barcode_preview: Option<String>,
    pub scanner_status_message: Option<String>,
    pub scanner_setup_hint: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct StoreRuntimeHardwareStatus {
    pub bridge_state: String,
    pub printers: Vec<StoreRuntimePrinterRecord>,
    pub profile: StoreRuntimeHardwareProfileRecord,
    pub diagnostics: StoreRuntimeHardwareDiagnostics,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
struct StoreRuntimeHardwareStateRecord {
    profile: StoreRuntimeHardwareProfileRecord,
    diagnostics: StoreRuntimeHardwareDiagnostics,
}

#[derive(Default)]
struct EmptyPrinterBackend;

impl PrinterBackend for EmptyPrinterBackend {
    fn list_printers(&self) -> Result<Vec<StoreRuntimePrinterRecord>, String> {
        Ok(Vec::new())
    }

    fn print_text(
        &mut self,
        _printer_name: &str,
        _document_name: &str,
        _contents: &str,
    ) -> Result<(), String> {
        Err("Empty printer backend cannot dispatch print jobs".to_string())
    }
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
        scanner_transport: Some("keyboard_wedge".to_string()),
        last_print_status: None,
        last_print_message: None,
        last_printed_at: None,
        last_scan_at: None,
        last_scan_barcode_preview: None,
        scanner_status_message: Some("Ready for external scanner input".to_string()),
        scanner_setup_hint: Some(
            "Connect a keyboard-wedge scanner and scan into the active packaged terminal."
                .to_string(),
        ),
    }
}

fn default_hardware_state() -> StoreRuntimeHardwareStateRecord {
    StoreRuntimeHardwareStateRecord {
        profile: default_hardware_profile(),
        diagnostics: default_hardware_diagnostics(),
    }
}

fn resolve_hardware_status(
    bridge_state: &str,
    printers: Vec<StoreRuntimePrinterRecord>,
    state: StoreRuntimeHardwareStateRecord,
) -> StoreRuntimeHardwareStatus {
    StoreRuntimeHardwareStatus {
        bridge_state: bridge_state.to_string(),
        printers,
        profile: state.profile,
        diagnostics: state.diagnostics,
    }
}

fn load_hardware_state(path: &Path) -> Result<StoreRuntimeHardwareStateRecord, String> {
    if !path.exists() {
        return Ok(default_hardware_state());
    }
    let raw = fs::read_to_string(path).map_err(|err| format!("Failed to read {}: {err}", path.display()))?;
    match serde_json::from_str::<StoreRuntimeHardwareStateRecord>(&raw) {
        Ok(state) => Ok(state),
        Err(_) => {
            clear_hardware_profile(path)?;
            Ok(default_hardware_state())
        }
    }
}

fn save_hardware_state(path: &Path, state: &StoreRuntimeHardwareStateRecord) -> Result<(), String> {
    let encoded = serde_json::to_string_pretty(state)
        .map_err(|err| format!("Failed to encode runtime hardware state {}: {err}", path.display()))?;
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|err| format!("Failed to prepare {}: {err}", parent.display()))?;
    }
    let temp_path = path.with_extension("tmp");
    fs::write(&temp_path, encoded)
        .map_err(|err| format!("Failed to write {}: {err}", temp_path.display()))?;
    fs::rename(&temp_path, path)
        .map_err(|err| format!("Failed to finalize {}: {err}", path.display()))
}

fn save_hardware_profile_to_path(
    path: &Path,
    profile: StoreRuntimeHardwareProfileInput,
) -> Result<StoreRuntimeHardwareStatus, String> {
    let mut state = load_hardware_state(path)?;
    state.profile = StoreRuntimeHardwareProfileRecord {
        receipt_printer_name: profile.receipt_printer_name,
        label_printer_name: profile.label_printer_name,
        updated_at: Some(current_timestamp_string()),
    };
    save_hardware_state(path, &state)?;
    load_hardware_status(path)
}

fn clear_hardware_profile(path: &Path) -> Result<(), String> {
    if !path.exists() {
        return Ok(());
    }
    fs::remove_file(path).map_err(|err| format!("Failed to remove {}: {err}", path.display()))
}

fn load_hardware_status(path: &Path) -> Result<StoreRuntimeHardwareStatus, String> {
    load_hardware_status_with_backend(path, &EmptyPrinterBackend)
}

fn load_hardware_status_with_backend<B: PrinterBackend>(
    path: &Path,
    backend: &B,
) -> Result<StoreRuntimeHardwareStatus, String> {
    let state = load_hardware_state(path)?;
    match list_printers_with_backend(backend) {
        Ok(printers) => Ok(resolve_hardware_status("ready", printers, state)),
        Err(error) => {
            let mut degraded_state = state;
            degraded_state.diagnostics.last_print_message = Some(error);
            Ok(resolve_hardware_status("unavailable", Vec::new(), degraded_state))
        }
    }
}

fn dispatch_print_job_with_backend<B: PrinterBackend>(
    path: &Path,
    backend: &mut B,
    job: StoreRuntimePrintJobInput,
) -> Result<StoreRuntimeHardwareStatus, String> {
    let mut state = load_hardware_state(path)?;
    match dispatch_print_job(backend, &state.profile, job) {
        Ok(result) => {
            state.diagnostics.last_print_status = Some("completed".to_string());
            state.diagnostics.last_print_message = Some(result.message);
            state.diagnostics.last_printed_at = Some(result.printed_at);
            save_hardware_state(path, &state)?;
            load_hardware_status_with_backend(path, backend)
        }
        Err(error) => {
            state.diagnostics.last_print_status = Some("failed".to_string());
            state.diagnostics.last_print_message = Some(error.clone());
            save_hardware_state(path, &state)?;
            Err(error)
        }
    }
}

#[tauri::command]
pub fn cmd_get_store_runtime_hardware_status() -> Result<StoreRuntimeHardwareStatus, String> {
    load_hardware_status_with_backend(&runtime_hardware_path(), &SystemPrinterBackend)
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

#[tauri::command]
pub fn cmd_dispatch_store_runtime_print_job(
    job: StoreRuntimePrintJobInput,
) -> Result<StoreRuntimeHardwareStatus, String> {
    dispatch_print_job_with_backend(&runtime_hardware_path(), &mut SystemPrinterBackend, job)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::runtime_printer::StoreRuntimePrintJobInput;
    use crate::runtime_paths::runtime_home_test_guard;
    use std::env;
    use std::fs;
    use uuid::Uuid;

    #[derive(Default)]
    struct FakePrinterBackend {
        printers: Vec<StoreRuntimePrinterRecord>,
    }

    impl PrinterBackend for FakePrinterBackend {
        fn list_printers(&self) -> Result<Vec<StoreRuntimePrinterRecord>, String> {
            Ok(self.printers.clone())
        }

        fn print_text(
            &mut self,
            _printer_name: &str,
            _document_name: &str,
            _contents: &str,
        ) -> Result<(), String> {
            Ok(())
        }
    }

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
        assert_eq!(status.diagnostics.scanner_transport.as_deref(), Some("keyboard_wedge"));
        assert_eq!(status.diagnostics.last_scan_barcode_preview, None);
        assert_eq!(
            status.diagnostics.scanner_status_message.as_deref(),
            Some("Ready for external scanner input")
        );
        assert_eq!(
            status.diagnostics.scanner_setup_hint.as_deref(),
            Some("Connect a keyboard-wedge scanner and scan into the active packaged terminal.")
        );

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

    #[test]
    fn runtime_hardware_dispatch_updates_last_print_diagnostics() {
        let _guard = runtime_home_test_guard()
            .lock()
            .expect("lock runtime-home guard");
        let previous_runtime_home = env::var("STORE_RUNTIME_HOME").ok();
        let runtime_home = env::temp_dir().join(format!(
            "store-runtime-hardware-dispatch-{}",
            Uuid::new_v4()
        ));
        fs::create_dir_all(&runtime_home).expect("create runtime home");
        env::set_var(
            "STORE_RUNTIME_HOME",
            runtime_home.to_string_lossy().to_string(),
        );

        let mut backend = FakePrinterBackend {
            printers: vec![StoreRuntimePrinterRecord {
                name: "Thermal-01".to_string(),
                label: "Thermal-01".to_string(),
                is_default: true,
                is_online: Some(true),
            }],
            ..Default::default()
        };

        save_hardware_profile_to_path(
            &runtime_hardware_path(),
            StoreRuntimeHardwareProfileInput {
                receipt_printer_name: Some("Thermal-01".to_string()),
                label_printer_name: None,
            },
        ).expect("save hardware profile");

        let status = dispatch_print_job_with_backend(
            &runtime_hardware_path(),
            &mut backend,
            StoreRuntimePrintJobInput {
                job_id: "print-job-1".to_string(),
                job_type: "SALES_INVOICE".to_string(),
                document_number: Some("SINV-0001".to_string()),
                receipt_lines: Some(vec![
                    "STORE TAX INVOICE".to_string(),
                    "Grand Total: 388.50".to_string(),
                ]),
                labels: None,
            },
        ).expect("dispatch print job");

        assert_eq!(status.diagnostics.last_print_status.as_deref(), Some("completed"));
        assert_eq!(status.diagnostics.last_print_message.as_deref(), Some("Printed SALES_INVOICE on Thermal-01"));
        assert!(status.diagnostics.last_printed_at.is_some());

        if let Some(value) = previous_runtime_home {
            env::set_var("STORE_RUNTIME_HOME", value);
        } else {
            env::remove_var("STORE_RUNTIME_HOME");
        }
        let _ = fs::remove_dir_all(runtime_home);
    }
}
