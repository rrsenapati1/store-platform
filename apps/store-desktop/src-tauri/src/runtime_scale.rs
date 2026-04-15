use crate::runtime_hardware::StoreRuntimeHardwareProfileRecord;
use serde::{Deserialize, Serialize};
use std::process::Command;

pub trait ScaleBackend {
    fn list_scales(&self) -> Result<Vec<StoreRuntimeScaleRecord>, String>;
    fn read_weight(&mut self, scale_id: &str) -> Result<StoreRuntimeScaleReadResult, String>;
}

#[derive(Default)]
pub struct SystemScaleBackend;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct StoreRuntimeScaleRecord {
    pub id: String,
    pub label: String,
    pub transport: String,
    pub port_name: String,
    pub is_connected: bool,
}

#[derive(Debug, Clone, PartialEq)]
pub struct StoreRuntimeScaleReadResult {
    pub scale_id: String,
    pub value: f64,
    pub unit: String,
    pub message: String,
    pub read_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct ScaleReadBridgePayload {
    scale_id: String,
    value: f64,
    unit: String,
    message: String,
    read_at: String,
}

fn escape_powershell_single_quoted(value: &str) -> String {
    value.replace('\'', "''")
}

fn resolve_scale_port_name(scale_id: &str) -> String {
    if let Some(port_name) = scale_id.strip_prefix("scale-") {
        return port_name.to_ascii_uppercase();
    }
    scale_id.to_string()
}

#[cfg(windows)]
fn run_powershell(script: &str) -> Result<String, String> {
    let output = Command::new("powershell")
        .args(["-NoProfile", "-NonInteractive", "-Command", script])
        .output()
        .map_err(|err| format!("Failed to launch PowerShell for scale bridge: {err}"))?;
    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr).trim().to_string();
        return Err(if stderr.is_empty() {
            format!(
                "Scale bridge PowerShell command failed with status {}",
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
    Err("Windows serial scale bridge is unavailable on this platform".to_string())
}

pub fn list_scales_with_backend<B: ScaleBackend>(
    backend: &B,
) -> Result<Vec<StoreRuntimeScaleRecord>, String> {
    backend.list_scales()
}

pub fn dispatch_scale_weight_read<B: ScaleBackend>(
    backend: &mut B,
    profile: &StoreRuntimeHardwareProfileRecord,
) -> Result<StoreRuntimeScaleReadResult, String> {
    let scale_id = profile
        .preferred_scale_id
        .as_deref()
        .ok_or_else(|| "A preferred scale must be assigned before reading live weight".to_string())?;
    backend.read_weight(scale_id)
}

impl ScaleBackend for SystemScaleBackend {
    fn list_scales(&self) -> Result<Vec<StoreRuntimeScaleRecord>, String> {
        let script = r#"
$records = @()
foreach ($portName in ([System.IO.Ports.SerialPort]::GetPortNames() | Sort-Object)) {
  $records += [PSCustomObject]@{
    id = ('scale-' + $portName.ToLowerInvariant())
    label = "Serial scale ($portName)"
    transport = "serial_com"
    port_name = $portName
    is_connected = $true
  }
}
ConvertTo-Json -InputObject @($records) -Compress
"#;
        let stdout = run_powershell(script)?;
        if stdout.is_empty() {
            return Ok(Vec::new());
        }
        serde_json::from_str::<Vec<StoreRuntimeScaleRecord>>(&stdout)
            .map_err(|err| format!("Failed to parse scale inventory payload: {err}"))
    }

    fn read_weight(&mut self, scale_id: &str) -> Result<StoreRuntimeScaleReadResult, String> {
        let port_name = resolve_scale_port_name(scale_id);
        let script = format!(
            r#"
$portName = '{port_name}'
$port = New-Object System.IO.Ports.SerialPort $portName, 9600, ([System.IO.Ports.Parity]::None), 8, ([System.IO.Ports.StopBits]::One)
$port.ReadTimeout = 1500
$port.WriteTimeout = 1500
$port.NewLine = "`r`n"
try {{
  $port.Open()
  Start-Sleep -Milliseconds 250
  $payload = $port.ReadExisting()
  if ([string]::IsNullOrWhiteSpace($payload)) {{
    try {{
      $payload = $port.ReadLine()
    }} catch {{
      $payload = ''
    }}
  }}
}} finally {{
  if ($port.IsOpen) {{
    $port.Close()
  }}
}}
if ([string]::IsNullOrWhiteSpace($payload)) {{
  throw "No scale payload received from $portName."
}}
$match = [regex]::Match($payload, '(?<value>[+-]?\d+(?:\.\d+)?)\s*(?<unit>kg|g|lb|lbs|oz)?', 'IgnoreCase')
if (-not $match.Success) {{
  throw "Unable to parse a stable weight from $portName payload: $payload"
}}
$value = [double]::Parse($match.Groups['value'].Value, [System.Globalization.CultureInfo]::InvariantCulture)
$unit = if ($match.Groups['unit'].Success -and -not [string]::IsNullOrWhiteSpace($match.Groups['unit'].Value)) {{
  $match.Groups['unit'].Value.ToLowerInvariant()
}} else {{
  'kg'
}}
[PSCustomObject]@{{
  scale_id = $portName
  value = $value
  unit = $unit
  message = ('Captured ' + $value.ToString('0.000', [System.Globalization.CultureInfo]::InvariantCulture) + ' ' + $unit + ' from Serial scale (' + $portName + ')')
  read_at = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds().ToString()
}} | ConvertTo-Json -Compress
"#,
            port_name = escape_powershell_single_quoted(&port_name),
        );

        let stdout = run_powershell(&script)?;
        let payload = serde_json::from_str::<ScaleReadBridgePayload>(&stdout)
            .map_err(|err| format!("Failed to parse scale read payload: {err}"))?;
        Ok(StoreRuntimeScaleReadResult {
            scale_id: scale_id.to_string(),
            value: payload.value,
            unit: payload.unit,
            message: payload.message,
            read_at: payload.read_at,
        })
    }
}

#[cfg(test)]
pub mod tests {
    use super::*;

    #[derive(Default)]
    pub struct FakeScaleBackend {
        pub scales: Vec<StoreRuntimeScaleRecord>,
        pub last_read_scale_id: Option<String>,
    }

    impl ScaleBackend for FakeScaleBackend {
        fn list_scales(&self) -> Result<Vec<StoreRuntimeScaleRecord>, String> {
            if self.scales.is_empty() {
                return Ok(vec![StoreRuntimeScaleRecord {
                    id: "scale-com3".to_string(),
                    label: "Serial scale (COM3)".to_string(),
                    transport: "serial_com".to_string(),
                    port_name: "COM3".to_string(),
                    is_connected: true,
                }]);
            }
            Ok(self.scales.clone())
        }

        fn read_weight(&mut self, scale_id: &str) -> Result<StoreRuntimeScaleReadResult, String> {
            self.last_read_scale_id = Some(scale_id.to_string());
            let port_name = resolve_scale_port_name(scale_id);
            Ok(StoreRuntimeScaleReadResult {
                scale_id: scale_id.to_string(),
                value: 0.5,
                unit: "kg".to_string(),
                message: format!("Captured 0.500 kg from Serial scale ({})", port_name),
                read_at: "1700000000".to_string(),
            })
        }
    }

    #[test]
    fn dispatch_scale_weight_read_requires_assignment() {
        let mut backend = FakeScaleBackend::default();
        let profile = StoreRuntimeHardwareProfileRecord {
            receipt_printer_name: None,
            label_printer_name: None,
            cash_drawer_printer_name: None,
            preferred_scale_id: None,
            preferred_scanner_id: None,
            updated_at: Some("1".to_string()),
        };

        let error = dispatch_scale_weight_read(&mut backend, &profile)
            .expect_err("scale read should fail without assignment");

        assert!(error.contains("scale"));
    }

    #[test]
    fn dispatch_scale_weight_read_uses_the_assigned_scale() {
        let mut backend = FakeScaleBackend::default();
        let profile = StoreRuntimeHardwareProfileRecord {
            receipt_printer_name: None,
            label_printer_name: None,
            cash_drawer_printer_name: None,
            preferred_scale_id: Some("scale-com3".to_string()),
            preferred_scanner_id: None,
            updated_at: Some("1".to_string()),
        };

        let result = dispatch_scale_weight_read(&mut backend, &profile).expect("scale read");

        assert_eq!(backend.last_read_scale_id.as_deref(), Some("scale-com3"));
        assert_eq!(result.value, 0.5);
        assert_eq!(result.unit, "kg");
    }
}
