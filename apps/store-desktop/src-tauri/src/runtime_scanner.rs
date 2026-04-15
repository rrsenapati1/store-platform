use serde::{Deserialize, Serialize};

pub trait ScannerBackend {
    fn list_scanners(&self) -> Result<Vec<StoreRuntimeScannerRecord>, String>;
}

#[derive(Default)]
pub struct SystemScannerBackend;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct StoreRuntimeScannerRecord {
    pub id: String,
    pub label: String,
    pub transport: String,
    pub vendor_name: Option<String>,
    pub product_name: Option<String>,
    pub serial_number: Option<String>,
    pub is_connected: bool,
}

#[cfg(windows)]
fn contains_scanner_keyword(value: &str) -> bool {
    let normalized = value.trim().to_ascii_lowercase();
    [
        "scanner",
        "barcode",
        "imager",
        "zebra",
        "symbol",
        "honeywell",
        "datalogic",
        "socket",
        "newland",
        "cipherlab",
        "opticon",
        "scan engine",
        "nls",
    ]
    .iter()
    .any(|keyword| normalized.contains(keyword))
}

#[cfg(windows)]
fn build_scanner_label(
    vendor_name: Option<&str>,
    product_name: Option<&str>,
    vendor_id: u16,
    product_id: u16,
) -> String {
    match (vendor_name, product_name) {
        (Some(vendor), Some(product))
            if !vendor.trim().is_empty()
                && !product.trim().is_empty()
                && vendor.trim() != product.trim() =>
        {
            format!("{} {}", vendor.trim(), product.trim())
        }
        (_, Some(product)) if !product.trim().is_empty() => product.trim().to_string(),
        (Some(vendor), _) if !vendor.trim().is_empty() => vendor.trim().to_string(),
        _ => format!("HID scanner {:04x}:{:04x}", vendor_id, product_id),
    }
}

#[cfg(windows)]
fn build_scanner_id(device: &hidapi::DeviceInfo, fallback_index: usize) -> String {
    let identity = device
        .serial_number()
        .filter(|value| !value.trim().is_empty())
        .map(|value| value.trim().to_string())
        .unwrap_or_else(|| device.path().to_string_lossy().replace('\\', "/"));
    format!(
        "{:04x}:{:04x}:{}:{}:{}",
        device.vendor_id(),
        device.product_id(),
        device.usage_page(),
        device.interface_number(),
        if identity.is_empty() {
            format!("scanner-{fallback_index}")
        } else {
            identity
        }
    )
}

#[cfg(windows)]
fn scanner_transport(bus_type: hidapi::BusType) -> String {
    match bus_type {
        hidapi::BusType::Usb => "usb_hid",
        hidapi::BusType::Bluetooth => "bluetooth_hid",
        _ => "unknown",
    }
    .to_string()
}

#[cfg(windows)]
fn is_scanner_candidate(device: &hidapi::DeviceInfo) -> bool {
    let vendor_name = device.manufacturer_string().unwrap_or_default();
    let product_name = device.product_string().unwrap_or_default();
    contains_scanner_keyword(vendor_name)
        || contains_scanner_keyword(product_name)
        || device.usage_page() == 0x8c
}

#[cfg(windows)]
fn list_system_scanners() -> Result<Vec<StoreRuntimeScannerRecord>, String> {
    let hid_api = hidapi::HidApi::new()
        .map_err(|error| format!("Failed to initialize HID scanner discovery: {error}"))?;
    let mut scanners = hid_api
        .device_list()
        .enumerate()
        .filter(|(_, device)| is_scanner_candidate(device))
        .map(|(index, device)| {
            let vendor_name = device.manufacturer_string().map(|value| value.to_string());
            let product_name = device.product_string().map(|value| value.to_string());
            let serial_number = device.serial_number().map(|value| value.to_string());
            StoreRuntimeScannerRecord {
                id: build_scanner_id(device, index),
                label: build_scanner_label(
                    vendor_name.as_deref(),
                    product_name.as_deref(),
                    device.vendor_id(),
                    device.product_id(),
                ),
                transport: scanner_transport(device.bus_type()),
                vendor_name,
                product_name,
                serial_number,
                is_connected: true,
            }
        })
        .collect::<Vec<_>>();
    scanners.sort_by(|left, right| left.label.cmp(&right.label));
    Ok(scanners)
}

#[cfg(not(windows))]
fn list_system_scanners() -> Result<Vec<StoreRuntimeScannerRecord>, String> {
    Err("Windows HID scanner discovery is unavailable on this platform".to_string())
}

impl ScannerBackend for SystemScannerBackend {
    fn list_scanners(&self) -> Result<Vec<StoreRuntimeScannerRecord>, String> {
        list_system_scanners()
    }
}

pub fn list_scanners_with_backend<B: ScannerBackend>(
    backend: &B,
) -> Result<Vec<StoreRuntimeScannerRecord>, String> {
    backend.list_scanners()
}
