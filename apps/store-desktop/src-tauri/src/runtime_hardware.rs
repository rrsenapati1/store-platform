use crate::runtime_paths::runtime_home_dir;
use crate::runtime_cash_drawer::{
    dispatch_cash_drawer_open, CashDrawerBackend, SystemCashDrawerBackend,
};
use crate::runtime_printer::{
    dispatch_print_job, list_printers_with_backend, PrinterBackend, StoreRuntimePrintJobInput,
    SystemPrinterBackend,
};
use crate::runtime_scanner::{
    list_scanners_with_backend, ScannerBackend, StoreRuntimeScannerRecord, SystemScannerBackend,
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
    pub cash_drawer_printer_name: Option<String>,
    pub preferred_scanner_id: Option<String>,
    pub updated_at: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct StoreRuntimeHardwareProfileInput {
    pub receipt_printer_name: Option<String>,
    pub label_printer_name: Option<String>,
    pub cash_drawer_printer_name: Option<String>,
    pub preferred_scanner_id: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct StoreRuntimeHardwareDiagnostics {
    pub scanner_capture_state: String,
    pub scanner_transport: Option<String>,
    pub last_print_status: Option<String>,
    pub last_print_message: Option<String>,
    pub last_printed_at: Option<String>,
    pub last_cash_drawer_status: Option<String>,
    pub last_cash_drawer_message: Option<String>,
    pub last_cash_drawer_opened_at: Option<String>,
    pub last_scan_at: Option<String>,
    pub last_scan_barcode_preview: Option<String>,
    pub cash_drawer_status_message: Option<String>,
    pub cash_drawer_setup_hint: Option<String>,
    pub scanner_status_message: Option<String>,
    pub scanner_setup_hint: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct StoreRuntimeHardwareStatus {
    pub bridge_state: String,
    pub scanners: Vec<StoreRuntimeScannerRecord>,
    pub printers: Vec<StoreRuntimePrinterRecord>,
    pub profile: StoreRuntimeHardwareProfileRecord,
    pub diagnostics: StoreRuntimeHardwareDiagnostics,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct StoreRuntimeScannerActivityInput {
    pub barcode_preview: String,
    pub scanner_transport: Option<String>,
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

#[derive(Default)]
struct EmptyScannerBackend;

impl ScannerBackend for EmptyScannerBackend {
    fn list_scanners(&self) -> Result<Vec<StoreRuntimeScannerRecord>, String> {
        Ok(Vec::new())
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
        cash_drawer_printer_name: None,
        preferred_scanner_id: None,
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
        last_cash_drawer_status: None,
        last_cash_drawer_message: None,
        last_cash_drawer_opened_at: None,
        last_scan_at: None,
        last_scan_barcode_preview: None,
        cash_drawer_status_message: Some(
            "Assign a local receipt printer to enable cash drawer pulses.".to_string(),
        ),
        cash_drawer_setup_hint: Some(
            "Use a receipt printer with a connected RJ11 cash drawer.".to_string(),
        ),
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
    scanners: Vec<StoreRuntimeScannerRecord>,
    printers: Vec<StoreRuntimePrinterRecord>,
    state: StoreRuntimeHardwareStateRecord,
) -> StoreRuntimeHardwareStatus {
    StoreRuntimeHardwareStatus {
        bridge_state: bridge_state.to_string(),
        scanners,
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
        cash_drawer_printer_name: profile.cash_drawer_printer_name,
        preferred_scanner_id: profile.preferred_scanner_id,
        updated_at: Some(current_timestamp_string()),
    };
    save_hardware_state(path, &state)?;
    load_hardware_status(path)
}

fn save_hardware_profile_with_backends<P: PrinterBackend, S: ScannerBackend>(
    path: &Path,
    profile: StoreRuntimeHardwareProfileInput,
    printer_backend: &P,
    scanner_backend: &S,
) -> Result<StoreRuntimeHardwareStatus, String> {
    let mut state = load_hardware_state(path)?;
    state.profile = StoreRuntimeHardwareProfileRecord {
        receipt_printer_name: profile.receipt_printer_name,
        label_printer_name: profile.label_printer_name,
        cash_drawer_printer_name: profile.cash_drawer_printer_name,
        preferred_scanner_id: profile.preferred_scanner_id,
        updated_at: Some(current_timestamp_string()),
    };
    save_hardware_state(path, &state)?;
    load_hardware_status_with_backends(path, printer_backend, scanner_backend)
}

fn record_scanner_activity_to_path(
    path: &Path,
    activity: StoreRuntimeScannerActivityInput,
) -> Result<StoreRuntimeHardwareStatus, String> {
    let mut state = load_hardware_state(path)?;
    state.diagnostics.last_scan_at = Some(current_timestamp_string());
    state.diagnostics.last_scan_barcode_preview = Some(activity.barcode_preview);
    if let Some(scanner_transport) = activity.scanner_transport {
        state.diagnostics.scanner_transport = Some(scanner_transport);
    }
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
    load_hardware_status_with_backends(path, &EmptyPrinterBackend, &EmptyScannerBackend)
}

fn resolve_cash_drawer_diagnostics(
    state: &mut StoreRuntimeHardwareStateRecord,
    printers: &[StoreRuntimePrinterRecord],
    printer_error: Option<&str>,
) {
    if let Some(error) = printer_error {
        state.diagnostics.cash_drawer_status_message = Some(error.to_string());
        state.diagnostics.cash_drawer_setup_hint = Some(
            "Reconnect the assigned receipt printer or restart the packaged terminal to retry cash drawer access."
                .to_string(),
        );
        return;
    }

    if let Some(printer_name) = state.profile.cash_drawer_printer_name.as_deref() {
        if let Some(printer) = printers.iter().find(|candidate| candidate.name == printer_name) {
            if printer.is_online == Some(false) {
                state.diagnostics.cash_drawer_status_message = Some(format!(
                    "Assigned cash drawer printer is offline: {}.",
                    printer.label
                ));
                state.diagnostics.cash_drawer_setup_hint = Some(
                    "Reconnect the assigned receipt printer or choose another local printer for the cash drawer."
                        .to_string(),
                );
                return;
            }

            if state.diagnostics.last_cash_drawer_status.as_deref() == Some("failed") {
                state.diagnostics.cash_drawer_status_message =
                    state.diagnostics.last_cash_drawer_message.clone();
                state.diagnostics.cash_drawer_setup_hint = Some(
                    "Retry after confirming the drawer cable and receipt printer power are both healthy."
                        .to_string(),
                );
                return;
            }

            if state.diagnostics.last_cash_drawer_status.as_deref() == Some("opened") {
                state.diagnostics.cash_drawer_status_message =
                    Some(format!("Cash drawer pulse sent to {}.", printer.label));
                state.diagnostics.cash_drawer_setup_hint = Some(
                    "Close the drawer fully before the next manual open action.".to_string(),
                );
                return;
            }

            state.diagnostics.cash_drawer_status_message =
                Some(format!("Cash drawer is assigned to {}.", printer.label));
            state.diagnostics.cash_drawer_setup_hint = Some(
                "Open the assigned cash drawer only after a cashier confirms the sale state."
                    .to_string(),
            );
            return;
        }

        state.diagnostics.cash_drawer_status_message = Some(format!(
            "Assigned cash drawer printer not discovered: {}.",
            printer_name
        ));
        state.diagnostics.cash_drawer_setup_hint = Some(
            "Reconnect the assigned receipt printer or choose another discovered local printer."
                .to_string(),
        );
        return;
    }

    state.diagnostics.cash_drawer_status_message =
        Some("Assign a local receipt printer to enable cash drawer pulses.".to_string());
    state.diagnostics.cash_drawer_setup_hint =
        Some("Use a receipt printer with a connected RJ11 cash drawer.".to_string());
}

fn resolve_scanner_diagnostics(
    state: &mut StoreRuntimeHardwareStateRecord,
    scanners: &[StoreRuntimeScannerRecord],
    scanner_error: Option<&str>,
) {
    if let Some(error) = scanner_error {
        state.diagnostics.scanner_capture_state = "unavailable".to_string();
        state.diagnostics.scanner_transport = Some("unknown".to_string());
        state.diagnostics.scanner_status_message = Some(error.to_string());
        state.diagnostics.scanner_setup_hint = Some(
            "Reconnect the HID scanner or restart the packaged terminal to retry scanner discovery."
                .to_string(),
        );
        return;
    }

    if let Some(preferred_scanner_id) = state.profile.preferred_scanner_id.as_deref() {
        if let Some(scanner) = scanners
            .iter()
            .find(|candidate| candidate.id == preferred_scanner_id && candidate.is_connected)
        {
            state.diagnostics.scanner_capture_state = "ready".to_string();
            state.diagnostics.scanner_transport = Some(scanner.transport.clone());
            state.diagnostics.scanner_status_message =
                Some(format!("Preferred HID scanner connected: {}", scanner.label));
            state.diagnostics.scanner_setup_hint = Some(
                "Scan into the active packaged terminal to keep HID activity diagnostics current."
                    .to_string(),
            );
            return;
        }

        state.diagnostics.scanner_capture_state = "attention_required".to_string();
        state.diagnostics.scanner_transport = Some("unknown".to_string());
        state.diagnostics.scanner_status_message =
            Some("Preferred HID scanner not connected".to_string());
        state.diagnostics.scanner_setup_hint = Some(
            "Reconnect the preferred scanner or choose a different local scanner.".to_string(),
        );
        return;
    }

    if let Some(scanner) = scanners.iter().find(|candidate| candidate.is_connected) {
        state.diagnostics.scanner_capture_state = "ready".to_string();
        state.diagnostics.scanner_transport = Some(scanner.transport.clone());
        state.diagnostics.scanner_status_message = Some(format!(
            "{} HID scanner candidate{} discovered. Assign one for stronger presence diagnostics.",
            scanners.len(),
            if scanners.len() == 1 { "" } else { "s" }
        ));
        state.diagnostics.scanner_setup_hint = Some(
            "Use the barcode lookup section to choose a preferred local scanner.".to_string(),
        );
        return;
    }

    if state.diagnostics.last_scan_at.is_some()
        && state
            .diagnostics
            .scanner_transport
            .as_deref()
            .is_some_and(|value| value != "unknown")
    {
        state.diagnostics.scanner_capture_state = "ready".to_string();
        state.diagnostics.scanner_status_message = Some(
            "Recent scanner activity recorded. HID inventory is not currently exposing a local scanner candidate."
                .to_string(),
        );
        state.diagnostics.scanner_setup_hint = Some(
            "Reconnect the scanner or rescan in the active packaged terminal if HID inventory stays empty."
                .to_string(),
        );
        return;
    }

    state.diagnostics.scanner_capture_state = "ready".to_string();
    state.diagnostics.scanner_transport = Some("keyboard_wedge".to_string());
    state.diagnostics.scanner_status_message = Some(
        "No HID scanner candidates discovered yet. Keyboard-wedge scanning still works."
            .to_string(),
    );
    state.diagnostics.scanner_setup_hint = Some(
        "Connect a USB/Bluetooth HID scanner or keep using wedge scanning in the active packaged terminal."
            .to_string(),
    );
}

fn load_hardware_status_with_backends<B: PrinterBackend, S: ScannerBackend>(
    path: &Path,
    printer_backend: &B,
    scanner_backend: &S,
) -> Result<StoreRuntimeHardwareStatus, String> {
    let mut state = load_hardware_state(path)?;
    let scanner_result = list_scanners_with_backend(scanner_backend);
    let printer_result = list_printers_with_backend(printer_backend);
    let scanners = match scanner_result.as_ref() {
        Ok(records) => records.clone(),
        Err(_) => Vec::new(),
    };
    let printers = match printer_result.as_ref() {
        Ok(records) => records.clone(),
        Err(_) => Vec::new(),
    };
    resolve_cash_drawer_diagnostics(
        &mut state,
        &printers,
        printer_result.as_ref().err().map(|value| value.as_str()),
    );
    resolve_scanner_diagnostics(
        &mut state,
        &scanners,
        scanner_result.as_ref().err().map(|value| value.as_str()),
    );

    if let Err(error) = printer_result {
        state.diagnostics.last_print_message = Some(error);
        return Ok(resolve_hardware_status(
            "unavailable",
            scanners,
            printers,
            state,
        ));
    }

    if scanner_result.is_err() {
        return Ok(resolve_hardware_status(
            "unavailable",
            scanners,
            printers,
            state,
        ));
    }

    Ok(resolve_hardware_status("ready", scanners, printers, state))
}

#[cfg(test)]
fn load_hardware_status_with_backends_for_tests<B: PrinterBackend, S: ScannerBackend>(
    printer_backend: &B,
    scanner_backend: &S,
    state: StoreRuntimeHardwareStateRecord,
) -> Result<StoreRuntimeHardwareStatus, String> {
    let mut next_state = state;
    let scanner_result = list_scanners_with_backend(scanner_backend);
    let scanners = match scanner_result.as_ref() {
        Ok(records) => records.clone(),
        Err(_) => Vec::new(),
    };
    let printers = list_printers_with_backend(printer_backend)?;
    resolve_cash_drawer_diagnostics(&mut next_state, &printers, None);
    resolve_scanner_diagnostics(
        &mut next_state,
        &scanners,
        scanner_result.as_ref().err().map(|value| value.as_str()),
    );
    Ok(resolve_hardware_status("ready", scanners, printers, next_state))
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
            load_hardware_status_with_backends(path, backend, &SystemScannerBackend)
        }
        Err(error) => {
            state.diagnostics.last_print_status = Some("failed".to_string());
            state.diagnostics.last_print_message = Some(error.clone());
            save_hardware_state(path, &state)?;
            Err(error)
        }
    }
}

fn open_cash_drawer_with_backends<D: CashDrawerBackend, P: PrinterBackend, S: ScannerBackend>(
    path: &Path,
    drawer_backend: &mut D,
    printer_backend: &P,
    scanner_backend: &S,
) -> Result<StoreRuntimeHardwareStatus, String> {
    let mut next_state = load_hardware_state(path)?;
    match dispatch_cash_drawer_open(drawer_backend, &next_state.profile) {
        Ok(result) => {
            next_state.diagnostics.last_cash_drawer_status = Some("opened".to_string());
            next_state.diagnostics.last_cash_drawer_message = Some(result.message);
            next_state.diagnostics.last_cash_drawer_opened_at = Some(result.opened_at);
            save_hardware_state(path, &next_state)?;
            load_hardware_status_with_backends(path, printer_backend, scanner_backend)
        }
        Err(error) => {
            next_state.diagnostics.last_cash_drawer_status = Some("failed".to_string());
            next_state.diagnostics.last_cash_drawer_message = Some(error.clone());
            save_hardware_state(path, &next_state)?;
            let _ = load_hardware_status_with_backends(path, printer_backend, scanner_backend);
            Err(error)
        }
    }
}

#[cfg(test)]
fn open_cash_drawer_with_backend<D: CashDrawerBackend>(
    path: &Path,
    drawer_backend: &mut D,
) -> Result<StoreRuntimeHardwareStatus, String> {
    open_cash_drawer_with_backends(
        path,
        drawer_backend,
        &EmptyPrinterBackend,
        &EmptyScannerBackend,
    )
}

#[tauri::command]
pub fn cmd_get_store_runtime_hardware_status() -> Result<StoreRuntimeHardwareStatus, String> {
    load_hardware_status_with_backends(
        &runtime_hardware_path(),
        &SystemPrinterBackend,
        &SystemScannerBackend,
    )
}

#[tauri::command]
pub fn cmd_save_store_runtime_hardware_profile(
    profile: StoreRuntimeHardwareProfileInput,
) -> Result<StoreRuntimeHardwareStatus, String> {
    save_hardware_profile_with_backends(
        &runtime_hardware_path(),
        profile,
        &SystemPrinterBackend,
        &SystemScannerBackend,
    )
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

#[tauri::command]
pub fn cmd_open_store_runtime_cash_drawer() -> Result<StoreRuntimeHardwareStatus, String> {
    open_cash_drawer_with_backends(
        &runtime_hardware_path(),
        &mut SystemCashDrawerBackend,
        &SystemPrinterBackend,
        &SystemScannerBackend,
    )
}

#[tauri::command]
pub fn cmd_record_store_runtime_scanner_activity(
    activity: StoreRuntimeScannerActivityInput,
) -> Result<StoreRuntimeHardwareStatus, String> {
    record_scanner_activity_to_path(&runtime_hardware_path(), activity)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::runtime_printer::StoreRuntimePrintJobInput;
    use crate::runtime_paths::runtime_home_test_guard;
    use crate::runtime_scanner::{ScannerBackend, StoreRuntimeScannerRecord};
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

    #[derive(Default)]
    struct FakeScannerBackend {
        scanners: Vec<StoreRuntimeScannerRecord>,
    }

    impl ScannerBackend for FakeScannerBackend {
        fn list_scanners(&self) -> Result<Vec<StoreRuntimeScannerRecord>, String> {
            Ok(self.scanners.clone())
        }
    }

    #[test]
    fn runtime_hardware_status_defaults_to_empty_profile() {
        let _guard = runtime_home_test_guard()
            .lock()
            .unwrap_or_else(|poisoned| poisoned.into_inner());
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
        assert_eq!(status.scanners.len(), 0);
        assert_eq!(status.printers.len(), 0);
        assert_eq!(status.profile.receipt_printer_name, None);
        assert_eq!(status.profile.label_printer_name, None);
        assert_eq!(status.profile.cash_drawer_printer_name, None);
        assert_eq!(status.profile.preferred_scanner_id, None);
        assert_eq!(status.diagnostics.scanner_capture_state, "ready");
        assert_eq!(status.diagnostics.scanner_transport.as_deref(), Some("keyboard_wedge"));
        assert_eq!(status.diagnostics.last_cash_drawer_status, None);
        assert_eq!(status.diagnostics.last_cash_drawer_message, None);
        assert_eq!(status.diagnostics.last_cash_drawer_opened_at, None);
        assert_eq!(
            status.diagnostics.cash_drawer_status_message.as_deref(),
            Some("Assign a local receipt printer to enable cash drawer pulses.")
        );
        assert_eq!(
            status.diagnostics.cash_drawer_setup_hint.as_deref(),
            Some("Use a receipt printer with a connected RJ11 cash drawer.")
        );
        assert_eq!(status.diagnostics.last_scan_barcode_preview, None);
        assert_eq!(
            status.diagnostics.scanner_status_message.as_deref(),
            Some("No HID scanner candidates discovered yet. Keyboard-wedge scanning still works.")
        );
        assert_eq!(
            status.diagnostics.scanner_setup_hint.as_deref(),
            Some("Connect a USB/Bluetooth HID scanner or keep using wedge scanning in the active packaged terminal.")
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
            .unwrap_or_else(|poisoned| poisoned.into_inner());
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
                cash_drawer_printer_name: Some("Thermal-01".to_string()),
                preferred_scanner_id: Some("scanner-zebra-1".to_string()),
            },
        )
        .expect("save hardware profile");
        let loaded = load_hardware_status(&runtime_hardware_path()).expect("load hardware status");

        assert_eq!(saved.profile.receipt_printer_name.as_deref(), Some("Thermal-01"));
        assert_eq!(saved.profile.label_printer_name.as_deref(), Some("Label-01"));
        assert_eq!(saved.profile.cash_drawer_printer_name.as_deref(), Some("Thermal-01"));
        assert_eq!(saved.profile.preferred_scanner_id.as_deref(), Some("scanner-zebra-1"));
        assert_eq!(loaded.profile.receipt_printer_name.as_deref(), Some("Thermal-01"));
        assert_eq!(loaded.profile.label_printer_name.as_deref(), Some("Label-01"));
        assert_eq!(loaded.profile.cash_drawer_printer_name.as_deref(), Some("Thermal-01"));
        assert_eq!(loaded.profile.preferred_scanner_id.as_deref(), Some("scanner-zebra-1"));
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
            .unwrap_or_else(|poisoned| poisoned.into_inner());
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
                cash_drawer_printer_name: Some("Thermal-01".to_string()),
                preferred_scanner_id: None,
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

    #[test]
    fn runtime_hardware_marks_preferred_scanner_missing_as_attention_required() {
        let state = StoreRuntimeHardwareStateRecord {
            profile: StoreRuntimeHardwareProfileRecord {
                receipt_printer_name: None,
                label_printer_name: None,
                cash_drawer_printer_name: None,
                preferred_scanner_id: Some("scanner-zebra-1".to_string()),
                updated_at: Some("1".to_string()),
            },
            diagnostics: default_hardware_diagnostics(),
        };
        let printer_backend = FakePrinterBackend::default();
        let scanner_backend = FakeScannerBackend {
            scanners: vec![StoreRuntimeScannerRecord {
                id: "scanner-blue-1".to_string(),
                label: "Socket Mobile S740".to_string(),
                transport: "bluetooth_hid".to_string(),
                vendor_name: Some("Socket Mobile".to_string()),
                product_name: Some("S740".to_string()),
                serial_number: Some("SO-001".to_string()),
                is_connected: true,
            }],
        };

        let status = load_hardware_status_with_backends_for_tests(&printer_backend, &scanner_backend, state)
            .expect("load hardware status");

        assert_eq!(status.diagnostics.scanner_capture_state, "attention_required");
        assert_eq!(status.diagnostics.scanner_transport.as_deref(), Some("unknown"));
        assert!(status
            .diagnostics
            .scanner_status_message
            .as_deref()
            .is_some_and(|value| value.contains("Preferred HID scanner not connected")));
    }

    #[test]
    fn runtime_hardware_records_scanner_activity_in_native_store() {
        let _guard = runtime_home_test_guard()
            .lock()
            .unwrap_or_else(|poisoned| poisoned.into_inner());
        let previous_runtime_home = env::var("STORE_RUNTIME_HOME").ok();
        let runtime_home = env::temp_dir().join(format!(
            "store-runtime-hardware-scanner-{}",
            Uuid::new_v4()
        ));
        fs::create_dir_all(&runtime_home).expect("create runtime home");
        env::set_var(
            "STORE_RUNTIME_HOME",
            runtime_home.to_string_lossy().to_string(),
        );

        let status = record_scanner_activity_to_path(
            &runtime_hardware_path(),
            StoreRuntimeScannerActivityInput {
                barcode_preview: "ACMETEA".to_string(),
                scanner_transport: Some("usb_hid".to_string()),
            },
        )
        .expect("record scanner activity");

        assert_eq!(status.diagnostics.last_scan_barcode_preview.as_deref(), Some("ACMETEA"));
        assert_eq!(status.diagnostics.scanner_transport.as_deref(), Some("usb_hid"));
        assert!(status.diagnostics.last_scan_at.is_some());

        if let Some(value) = previous_runtime_home {
            env::set_var("STORE_RUNTIME_HOME", value);
        } else {
            env::remove_var("STORE_RUNTIME_HOME");
        }
        let _ = fs::remove_dir_all(runtime_home);
    }

    #[test]
    fn runtime_hardware_open_cash_drawer_requires_assignment_and_records_diagnostics() {
        let _guard = runtime_home_test_guard()
            .lock()
            .unwrap_or_else(|poisoned| poisoned.into_inner());
        let previous_runtime_home = env::var("STORE_RUNTIME_HOME").ok();
        let runtime_home = env::temp_dir().join(format!(
            "store-runtime-hardware-cash-drawer-{}",
            Uuid::new_v4()
        ));
        fs::create_dir_all(&runtime_home).expect("create runtime home");
        env::set_var(
            "STORE_RUNTIME_HOME",
            runtime_home.to_string_lossy().to_string(),
        );

        let error = open_cash_drawer_with_backend(
            &runtime_hardware_path(),
            &mut crate::runtime_cash_drawer::tests::FakeCashDrawerBackend::default(),
        )
        .expect_err("cash drawer open should fail without assignment");
        assert!(error.contains("cash drawer"));

        save_hardware_profile_to_path(
            &runtime_hardware_path(),
            StoreRuntimeHardwareProfileInput {
                receipt_printer_name: Some("Thermal-01".to_string()),
                label_printer_name: None,
                cash_drawer_printer_name: Some("Thermal-01".to_string()),
                preferred_scanner_id: None,
            },
        )
        .expect("save hardware profile");

        let status = open_cash_drawer_with_backend(
            &runtime_hardware_path(),
            &mut crate::runtime_cash_drawer::tests::FakeCashDrawerBackend::default(),
        )
        .expect("cash drawer open");

        assert_eq!(status.diagnostics.last_cash_drawer_status.as_deref(), Some("opened"));
        assert_eq!(
            status.diagnostics.last_cash_drawer_message.as_deref(),
            Some("Opened cash drawer through Thermal-01")
        );
        assert!(status.diagnostics.last_cash_drawer_opened_at.is_some());

        if let Some(value) = previous_runtime_home {
            env::set_var("STORE_RUNTIME_HOME", value);
        } else {
            env::remove_var("STORE_RUNTIME_HOME");
        }
        let _ = fs::remove_dir_all(runtime_home);
    }
}
