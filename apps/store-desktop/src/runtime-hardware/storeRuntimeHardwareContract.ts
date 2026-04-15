export type StoreRuntimeHardwareBridgeState = 'ready' | 'unavailable' | 'browser_fallback';
export type StoreRuntimeScannerCaptureState = 'ready' | 'unavailable' | 'browser_fallback' | 'attention_required';
export type StoreRuntimeScannerTransport = 'keyboard_wedge' | 'usb_hid' | 'bluetooth_hid' | 'unknown';

export interface StoreRuntimePrinterRecord {
  name: string;
  label: string;
  is_default: boolean;
  is_online: boolean | null;
}

export interface StoreRuntimeBarcodeLabel {
  sku_code: string;
  product_name: string;
  barcode: string;
  price_label: string;
}

export interface StoreRuntimeScannerRecord {
  id: string;
  label: string;
  transport: StoreRuntimeScannerTransport;
  vendor_name: string | null;
  product_name: string | null;
  serial_number: string | null;
  is_connected: boolean;
}

export interface StoreRuntimeHardwareProfile {
  receipt_printer_name: string | null;
  label_printer_name: string | null;
  preferred_scanner_id: string | null;
  updated_at: string | null;
}

export interface StoreRuntimeHardwareProfileInput {
  receipt_printer_name: string | null;
  label_printer_name: string | null;
  preferred_scanner_id: string | null;
}

export interface StoreRuntimeHardwareDiagnostics {
  scanner_capture_state: StoreRuntimeScannerCaptureState;
  scanner_transport: StoreRuntimeScannerTransport;
  last_print_status: string | null;
  last_print_message: string | null;
  last_printed_at: string | null;
  last_scan_at: string | null;
  last_scan_barcode_preview: string | null;
  scanner_status_message: string | null;
  scanner_setup_hint: string | null;
}

export interface StoreRuntimeHardwareStatus {
  bridge_state: StoreRuntimeHardwareBridgeState;
  scanners: StoreRuntimeScannerRecord[];
  printers: StoreRuntimePrinterRecord[];
  profile: StoreRuntimeHardwareProfile;
  diagnostics: StoreRuntimeHardwareDiagnostics;
}

export interface StoreRuntimeHardwarePrintJobInput {
  job_id: string;
  job_type: string;
  document_number: string | null;
  receipt_lines: string[] | null;
  labels: StoreRuntimeBarcodeLabel[] | null;
}

export interface StoreRuntimeHardwareScannerActivityInput {
  barcode_preview: string;
  scanner_transport: StoreRuntimeScannerTransport | null;
}

export interface StoreRuntimeHardwareAdapter {
  getStatus(): Promise<StoreRuntimeHardwareStatus>;
  saveProfile(profile: StoreRuntimeHardwareProfileInput): Promise<StoreRuntimeHardwareStatus>;
  dispatchPrintJob(job: StoreRuntimeHardwarePrintJobInput): Promise<StoreRuntimeHardwareStatus>;
  recordScannerActivity(activity: StoreRuntimeHardwareScannerActivityInput): Promise<StoreRuntimeHardwareStatus>;
}

export type StoreRuntimeHardwareInvoke = (command: string, payload?: Record<string, unknown>) => Promise<unknown>;

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

function isPrinterRecord(value: unknown): value is StoreRuntimePrinterRecord {
  return isObject(value)
    && typeof value.name === 'string'
    && typeof value.label === 'string'
    && typeof value.is_default === 'boolean'
    && (typeof value.is_online === 'boolean' || value.is_online === null);
}

function isHardwareProfile(value: unknown): value is StoreRuntimeHardwareProfile {
  return isObject(value)
    && (typeof value.receipt_printer_name === 'string' || value.receipt_printer_name === null)
    && (typeof value.label_printer_name === 'string' || value.label_printer_name === null)
    && (typeof value.preferred_scanner_id === 'string' || value.preferred_scanner_id === null)
    && (typeof value.updated_at === 'string' || value.updated_at === null);
}

function isScannerRecord(value: unknown): value is StoreRuntimeScannerRecord {
  return isObject(value)
    && typeof value.id === 'string'
    && typeof value.label === 'string'
    && (
      value.transport === 'keyboard_wedge'
      || value.transport === 'usb_hid'
      || value.transport === 'bluetooth_hid'
      || value.transport === 'unknown'
    )
    && (typeof value.vendor_name === 'string' || value.vendor_name === null)
    && (typeof value.product_name === 'string' || value.product_name === null)
    && (typeof value.serial_number === 'string' || value.serial_number === null)
    && typeof value.is_connected === 'boolean';
}

function isHardwareDiagnostics(value: unknown): value is StoreRuntimeHardwareDiagnostics {
  return isObject(value)
    && (
      value.scanner_capture_state === 'ready'
      || value.scanner_capture_state === 'unavailable'
      || value.scanner_capture_state === 'browser_fallback'
      || value.scanner_capture_state === 'attention_required'
    )
    && (
      value.scanner_transport === 'keyboard_wedge'
      || value.scanner_transport === 'usb_hid'
      || value.scanner_transport === 'bluetooth_hid'
      || value.scanner_transport === 'unknown'
    )
    && (typeof value.last_print_status === 'string' || value.last_print_status === null)
    && (typeof value.last_print_message === 'string' || value.last_print_message === null)
    && (typeof value.last_printed_at === 'string' || value.last_printed_at === null)
    && (typeof value.last_scan_at === 'string' || value.last_scan_at === null)
    && (typeof value.last_scan_barcode_preview === 'string' || value.last_scan_barcode_preview === null)
    && (typeof value.scanner_status_message === 'string' || value.scanner_status_message === null)
    && (typeof value.scanner_setup_hint === 'string' || value.scanner_setup_hint === null);
}

export function isStoreRuntimeHardwareStatus(value: unknown): value is StoreRuntimeHardwareStatus {
  return isObject(value)
    && (value.bridge_state === 'ready' || value.bridge_state === 'unavailable' || value.bridge_state === 'browser_fallback')
    && Array.isArray(value.scanners)
    && value.scanners.every((scanner) => isScannerRecord(scanner))
    && Array.isArray(value.printers)
    && value.printers.every((printer) => isPrinterRecord(printer))
    && isHardwareProfile(value.profile)
    && isHardwareDiagnostics(value.diagnostics);
}
