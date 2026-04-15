use crate::runtime_hardware::StoreRuntimeHardwareProfileRecord;
use std::process::Command;
use std::time::{SystemTime, UNIX_EPOCH};

pub trait CashDrawerBackend {
    fn open_drawer(
        &mut self,
        printer_name: &str,
    ) -> Result<StoreRuntimeCashDrawerDispatchResult, String>;
}

#[derive(Default)]
pub struct SystemCashDrawerBackend;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct StoreRuntimeCashDrawerDispatchResult {
    pub printer_name: String,
    pub message: String,
    pub opened_at: String,
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
        .map_err(|err| format!("Failed to launch PowerShell for cash drawer bridge: {err}"))?;
    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr).trim().to_string();
        return Err(if stderr.is_empty() {
            format!(
                "Cash drawer bridge PowerShell command failed with status {}",
                output.status
            )
        } else {
            stderr
        });
    }
    Ok(String::from_utf8_lossy(&output.stdout).trim().to_string())
}

#[cfg(not(windows))]
fn run_powershell(_script: &str) -> Result<String, String> {
    Err("Windows cash drawer bridge is unavailable on this platform".to_string())
}

pub fn dispatch_cash_drawer_open<B: CashDrawerBackend>(
    backend: &mut B,
    profile: &StoreRuntimeHardwareProfileRecord,
) -> Result<StoreRuntimeCashDrawerDispatchResult, String> {
    let printer_name = profile
        .cash_drawer_printer_name
        .as_deref()
        .ok_or_else(|| "A cash drawer printer must be assigned before opening the drawer".to_string())?;
    backend.open_drawer(printer_name)
}

impl CashDrawerBackend for SystemCashDrawerBackend {
    fn open_drawer(
        &mut self,
        printer_name: &str,
    ) -> Result<StoreRuntimeCashDrawerDispatchResult, String> {
        let script = format!(
            r#"
$printerName = '{printer_name}';
if (-not ('StoreCashDrawerPrinterBridge' -as [type])) {{
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;

public static class StoreCashDrawerPrinterBridge {{
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    public class DOCINFOW {{
        [MarshalAs(UnmanagedType.LPWStr)]
        public string pDocName;
        [MarshalAs(UnmanagedType.LPWStr)]
        public string pOutputFile;
        [MarshalAs(UnmanagedType.LPWStr)]
        public string pDataType;
    }}

    [DllImport("winspool.drv", EntryPoint="OpenPrinterW", SetLastError=true, CharSet=CharSet.Unicode)]
    public static extern bool OpenPrinter(string pPrinterName, out IntPtr phPrinter, IntPtr pDefault);

    [DllImport("winspool.drv", EntryPoint="ClosePrinter", SetLastError=true)]
    public static extern bool ClosePrinter(IntPtr hPrinter);

    [DllImport("winspool.drv", EntryPoint="StartDocPrinterW", SetLastError=true, CharSet=CharSet.Unicode)]
    public static extern int StartDocPrinter(IntPtr hPrinter, int level, [In] DOCINFOW docInfo);

    [DllImport("winspool.drv", EntryPoint="EndDocPrinter", SetLastError=true)]
    public static extern bool EndDocPrinter(IntPtr hPrinter);

    [DllImport("winspool.drv", EntryPoint="StartPagePrinter", SetLastError=true)]
    public static extern bool StartPagePrinter(IntPtr hPrinter);

    [DllImport("winspool.drv", EntryPoint="EndPagePrinter", SetLastError=true)]
    public static extern bool EndPagePrinter(IntPtr hPrinter);

    [DllImport("winspool.drv", EntryPoint="WritePrinter", SetLastError=true)]
    public static extern bool WritePrinter(IntPtr hPrinter, byte[] bytes, int count, out int written);

    public static void OpenCashDrawer(string printerName) {{
        IntPtr printerHandle;
        if (!OpenPrinter(printerName, out printerHandle, IntPtr.Zero)) {{
            throw new InvalidOperationException("OpenPrinter failed: " + Marshal.GetLastWin32Error());
        }}

        var docInfo = new DOCINFOW {{
            pDocName = "Store cash drawer pulse",
            pDataType = "RAW"
        }};

        var docStarted = false;
        var pageStarted = false;
        try {{
            if (StartDocPrinter(printerHandle, 1, docInfo) == 0) {{
                throw new InvalidOperationException("StartDocPrinter failed: " + Marshal.GetLastWin32Error());
            }}
            docStarted = true;

            if (!StartPagePrinter(printerHandle)) {{
                throw new InvalidOperationException("StartPagePrinter failed: " + Marshal.GetLastWin32Error());
            }}
            pageStarted = true;

            var pulseBytes = new byte[] {{ 27, 112, 0, 25, 250 }};
            int written;
            if (!WritePrinter(printerHandle, pulseBytes, pulseBytes.Length, out written)) {{
                throw new InvalidOperationException("WritePrinter failed: " + Marshal.GetLastWin32Error());
            }}
            if (written != pulseBytes.Length) {{
                throw new InvalidOperationException("WritePrinter wrote " + written + " bytes instead of " + pulseBytes.Length);
            }}
        }}
        finally {{
            if (pageStarted) {{
                EndPagePrinter(printerHandle);
            }}
            if (docStarted) {{
                EndDocPrinter(printerHandle);
            }}
            ClosePrinter(printerHandle);
        }}
    }}
}}
"@ | Out-Null
}}
[StoreCashDrawerPrinterBridge]::OpenCashDrawer($printerName)
"#,
            printer_name = escape_powershell_single_quoted(printer_name),
        );

        run_powershell(&script)?;
        Ok(StoreRuntimeCashDrawerDispatchResult {
            printer_name: printer_name.to_string(),
            message: format!("Opened cash drawer through {}", printer_name),
            opened_at: current_timestamp_string(),
        })
    }
}

#[cfg(test)]
pub mod tests {
    use super::*;

    #[derive(Default)]
    pub struct FakeCashDrawerBackend {
        pub opened_printer_name: Option<String>,
    }

    impl CashDrawerBackend for FakeCashDrawerBackend {
        fn open_drawer(
            &mut self,
            printer_name: &str,
        ) -> Result<StoreRuntimeCashDrawerDispatchResult, String> {
            self.opened_printer_name = Some(printer_name.to_string());
            Ok(StoreRuntimeCashDrawerDispatchResult {
                printer_name: printer_name.to_string(),
                message: format!("Opened cash drawer through {}", printer_name),
                opened_at: "1700000000".to_string(),
            })
        }
    }

    #[test]
    fn dispatch_cash_drawer_open_requires_assignment() {
        let mut backend = FakeCashDrawerBackend::default();
        let profile = StoreRuntimeHardwareProfileRecord {
            receipt_printer_name: Some("Thermal-01".to_string()),
            label_printer_name: None,
            cash_drawer_printer_name: None,
            preferred_scale_id: None,
            preferred_scanner_id: None,
            updated_at: Some("1".to_string()),
        };

        let error = dispatch_cash_drawer_open(&mut backend, &profile)
            .expect_err("cash drawer open should fail without assignment");

        assert!(error.contains("cash drawer printer"));
    }

    #[test]
    fn dispatch_cash_drawer_open_uses_assigned_printer() {
        let mut backend = FakeCashDrawerBackend::default();
        let profile = StoreRuntimeHardwareProfileRecord {
            receipt_printer_name: Some("Thermal-01".to_string()),
            label_printer_name: None,
            cash_drawer_printer_name: Some("Thermal-01".to_string()),
            preferred_scale_id: None,
            preferred_scanner_id: None,
            updated_at: Some("1".to_string()),
        };

        let result = dispatch_cash_drawer_open(&mut backend, &profile).expect("cash drawer open");

        assert_eq!(backend.opened_printer_name.as_deref(), Some("Thermal-01"));
        assert_eq!(result.printer_name, "Thermal-01");
        assert_eq!(result.message, "Opened cash drawer through Thermal-01");
    }
}
