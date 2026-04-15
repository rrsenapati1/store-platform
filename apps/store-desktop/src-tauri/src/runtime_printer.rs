use crate::runtime_hardware::{StoreRuntimeHardwareProfileRecord, StoreRuntimePrinterRecord};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::env;
use std::fs;
use std::process::Command;
use std::time::{SystemTime, UNIX_EPOCH};
use uuid::Uuid;

pub trait PrinterBackend {
    fn list_printers(&self) -> Result<Vec<StoreRuntimePrinterRecord>, String>;
    fn print_text(
        &mut self,
        printer_name: &str,
        document_name: &str,
        contents: &str,
    ) -> Result<(), String>;
}

#[derive(Default)]
pub struct SystemPrinterBackend;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct StoreRuntimeBarcodeLabel {
    pub sku_code: String,
    pub product_name: String,
    pub barcode: String,
    pub price_label: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct StoreRuntimePrintJobInput {
    pub job_id: String,
    pub job_type: String,
    pub document_number: Option<String>,
    pub receipt_lines: Option<Vec<String>>,
    pub labels: Option<Vec<StoreRuntimeBarcodeLabel>>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct StoreRuntimePrintDispatchResult {
    pub printer_name: String,
    pub message: String,
    pub printed_at: String,
}

fn current_timestamp_string() -> String {
    let seconds = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs();
    seconds.to_string()
}

fn escape_powershell_single_quoted(value: &str) -> String {
    value.replace('\'', "''")
}

#[cfg(windows)]
fn run_powershell(script: &str) -> Result<String, String> {
    let output = Command::new("powershell")
        .args(["-NoProfile", "-NonInteractive", "-Command", script])
        .output()
        .map_err(|err| format!("Failed to launch PowerShell for printer bridge: {err}"))?;
    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr).trim().to_string();
        return Err(if stderr.is_empty() {
            format!("Printer bridge PowerShell command failed with status {}", output.status)
        } else {
            stderr
        });
    }
    Ok(String::from_utf8_lossy(&output.stdout).trim().to_string())
}

#[cfg(not(windows))]
fn run_powershell(_script: &str) -> Result<String, String> {
    Err("Windows printer bridge is unavailable on this platform".to_string())
}

fn parse_printer_records(raw: &str) -> Result<Vec<StoreRuntimePrinterRecord>, String> {
    if raw.is_empty() {
        return Ok(Vec::new());
    }

    fn to_record(value: &Value) -> Result<StoreRuntimePrinterRecord, String> {
        let object = value
            .as_object()
            .ok_or_else(|| "Printer bridge returned a non-object printer record".to_string())?;
        let name = object
            .get("Name")
            .and_then(Value::as_str)
            .ok_or_else(|| "Printer bridge returned a printer without a name".to_string())?
            .to_string();
        let is_default = object.get("Default").and_then(Value::as_bool).unwrap_or(false);
        let is_online = object
            .get("WorkOffline")
            .and_then(Value::as_bool)
            .map(|work_offline| !work_offline);
        Ok(StoreRuntimePrinterRecord {
            label: name.clone(),
            name,
            is_default,
            is_online,
        })
    }

    let value: Value = serde_json::from_str(raw)
        .map_err(|err| format!("Failed to decode printer discovery response: {err}"))?;
    match value {
        Value::Array(records) => records.iter().map(to_record).collect(),
        Value::Object(_) => Ok(vec![to_record(&value)?]),
        Value::Null => Ok(Vec::new()),
        _ => Err("Printer bridge returned an unsupported discovery payload".to_string()),
    }
}

fn resolve_printer_name<'a>(
    profile: &'a StoreRuntimeHardwareProfileRecord,
    job_type: &str,
) -> Result<&'a str, String> {
    match job_type {
        "SALES_INVOICE" | "CREDIT_NOTE" => profile
            .receipt_printer_name
            .as_deref()
            .ok_or_else(|| "A receipt printer must be assigned before invoice printing".to_string()),
        "BARCODE_LABEL" => profile
            .label_printer_name
            .as_deref()
            .ok_or_else(|| "A label printer must be assigned before barcode label printing".to_string()),
        _ => Err(format!("Unsupported packaged-runtime print job type: {job_type}")),
    }
}

fn render_label_text(labels: &[StoreRuntimeBarcodeLabel]) -> String {
    labels
        .iter()
        .map(|label| {
            [
                label.product_name.as_str(),
                label.sku_code.as_str(),
                label.barcode.as_str(),
                label.price_label.as_str(),
            ]
            .join("\n")
        })
        .collect::<Vec<_>>()
        .join("\n\n-----\n\n")
}

fn render_print_job_contents(job: &StoreRuntimePrintJobInput) -> Result<String, String> {
    match job.job_type.as_str() {
        "SALES_INVOICE" | "CREDIT_NOTE" => job
            .receipt_lines
            .as_ref()
            .filter(|lines| !lines.is_empty())
            .map(|lines| lines.join("\n"))
            .ok_or_else(|| format!("{} print job is missing receipt lines", job.job_type)),
        "BARCODE_LABEL" => job
            .labels
            .as_ref()
            .filter(|labels| !labels.is_empty())
            .map(|labels| render_label_text(labels))
            .ok_or_else(|| "BARCODE_LABEL print job is missing label payload".to_string()),
        _ => Err(format!("Unsupported packaged-runtime print job type: {}", job.job_type)),
    }
}

pub fn list_printers_with_backend<B: PrinterBackend>(
    backend: &B,
) -> Result<Vec<StoreRuntimePrinterRecord>, String> {
    backend.list_printers()
}

pub fn dispatch_print_job<B: PrinterBackend>(
    backend: &mut B,
    profile: &StoreRuntimeHardwareProfileRecord,
    job: StoreRuntimePrintJobInput,
) -> Result<StoreRuntimePrintDispatchResult, String> {
    let printer_name = resolve_printer_name(profile, &job.job_type)?.to_string();
    let document_name = job
        .document_number
        .clone()
        .unwrap_or_else(|| job.job_id.clone());
    let contents = render_print_job_contents(&job)?;
    backend.print_text(&printer_name, &document_name, &contents)?;
    Ok(StoreRuntimePrintDispatchResult {
        printer_name: printer_name.clone(),
        message: format!("Printed {} on {}", job.job_type, printer_name),
        printed_at: current_timestamp_string(),
    })
}

impl PrinterBackend for SystemPrinterBackend {
    fn list_printers(&self) -> Result<Vec<StoreRuntimePrinterRecord>, String> {
        let raw = run_powershell(
            "Get-Printer | Select-Object Name, Default, WorkOffline | ConvertTo-Json -Compress",
        )?;
        parse_printer_records(&raw)
    }

    fn print_text(
        &mut self,
        printer_name: &str,
        document_name: &str,
        contents: &str,
    ) -> Result<(), String> {
        let temp_path = env::temp_dir().join(format!(
            "store-runtime-print-{}-{}.txt",
            document_name.replace(|character: char| !character.is_ascii_alphanumeric(), "-"),
            Uuid::new_v4()
        ));
        fs::write(&temp_path, contents)
            .map_err(|err| format!("Failed to write temporary print file: {err}"))?;
        let script = format!(
            "$content = Get-Content -Path '{}' -Raw; $content | Out-Printer -Name '{}'",
            escape_powershell_single_quoted(&temp_path.to_string_lossy()),
            escape_powershell_single_quoted(printer_name),
        );
        let result = run_powershell(&script);
        let _ = fs::remove_file(&temp_path);
        result.map(|_| ())
    }
}

#[cfg(test)]
pub mod tests {
    use super::*;
    use crate::runtime_hardware::{StoreRuntimeHardwareProfileRecord, StoreRuntimePrinterRecord};

    #[derive(Default)]
    pub struct FakePrinterBackend {
        pub printers: Vec<StoreRuntimePrinterRecord>,
        pub dispatched_printer: Option<String>,
        pub dispatched_document: Option<String>,
        pub dispatched_contents: Option<String>,
    }

    impl PrinterBackend for FakePrinterBackend {
        fn list_printers(&self) -> Result<Vec<StoreRuntimePrinterRecord>, String> {
            Ok(self.printers.clone())
        }

        fn print_text(
            &mut self,
            printer_name: &str,
            document_name: &str,
            contents: &str,
        ) -> Result<(), String> {
            self.dispatched_printer = Some(printer_name.to_string());
            self.dispatched_document = Some(document_name.to_string());
            self.dispatched_contents = Some(contents.to_string());
            Ok(())
        }
    }

    #[test]
    fn list_printers_uses_backend_results() {
        let backend = FakePrinterBackend {
            printers: vec![StoreRuntimePrinterRecord {
                name: "Thermal-01".to_string(),
                label: "Thermal-01".to_string(),
                is_default: true,
                is_online: Some(true),
            }],
            ..Default::default()
        };

        let printers = list_printers_with_backend(&backend).expect("list printers");

        assert_eq!(printers.len(), 1);
        assert_eq!(printers[0].name, "Thermal-01");
        assert!(printers[0].is_default);
    }

    #[test]
    fn dispatch_print_job_uses_receipt_printer_for_invoice_jobs() {
        let mut backend = FakePrinterBackend::default();
        let profile = StoreRuntimeHardwareProfileRecord {
            receipt_printer_name: Some("Thermal-01".to_string()),
            label_printer_name: Some("Label-01".to_string()),
            cash_drawer_printer_name: None,
            preferred_scale_id: None,
            preferred_scanner_id: None,
            updated_at: Some("1".to_string()),
        };

        dispatch_print_job(
            &mut backend,
            &profile,
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
        )
        .expect("dispatch print job");

        assert_eq!(backend.dispatched_printer.as_deref(), Some("Thermal-01"));
        assert_eq!(backend.dispatched_document.as_deref(), Some("SINV-0001"));
        assert!(backend
            .dispatched_contents
            .as_deref()
            .is_some_and(|value| value.contains("Grand Total: 388.50")));
    }

    #[test]
    fn dispatch_print_job_requires_matching_printer_assignment() {
        let mut backend = FakePrinterBackend::default();
        let profile = StoreRuntimeHardwareProfileRecord {
            receipt_printer_name: Some("Thermal-01".to_string()),
            label_printer_name: None,
            cash_drawer_printer_name: None,
            preferred_scale_id: None,
            preferred_scanner_id: None,
            updated_at: Some("1".to_string()),
        };

        let error = dispatch_print_job(
            &mut backend,
            &profile,
            StoreRuntimePrintJobInput {
                job_id: "print-job-2".to_string(),
                job_type: "BARCODE_LABEL".to_string(),
                document_number: Some("LBL-0001".to_string()),
                receipt_lines: None,
                labels: Some(vec![StoreRuntimeBarcodeLabel {
                    sku_code: "sku-1".to_string(),
                    product_name: "Classic Tea".to_string(),
                    barcode: "ACMETEACLASSIC".to_string(),
                    price_label: "Rs. 89.00".to_string(),
                }]),
            },
        )
        .expect_err("label print should fail without configured label printer");

        assert!(error.contains("label printer"));
    }
}
