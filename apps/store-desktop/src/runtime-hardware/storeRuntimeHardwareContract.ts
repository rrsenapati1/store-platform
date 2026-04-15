export type StoreRuntimeHardwareBridgeState = 'ready' | 'unavailable' | 'browser_fallback';
export type StoreRuntimeScannerCaptureState = 'ready' | 'unavailable' | 'browser_fallback' | 'attention_required';
export type StoreRuntimeScannerTransport = 'keyboard_wedge' | 'unknown';

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

export interface StoreRuntimeHardwareProfile {
  receipt_printer_name: string | null;
  label_printer_name: string | null;
  updated_at: string | null;
}

export interface StoreRuntimeHardwareProfileInput {
  receipt_printer_name: string | null;
  label_printer_name: string | null;
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

export interface StoreRuntimeHardwareAdapter {
  getStatus(): Promise<StoreRuntimeHardwareStatus>;
  saveProfile(profile: StoreRuntimeHardwareProfileInput): Promise<StoreRuntimeHardwareStatus>;
  dispatchPrintJob(job: StoreRuntimeHardwarePrintJobInput): Promise<StoreRuntimeHardwareStatus>;
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
    && (typeof value.updated_at === 'string' || value.updated_at === null);
}

function isHardwareDiagnostics(value: unknown): value is StoreRuntimeHardwareDiagnostics {
  return isObject(value)
    && (
      value.scanner_capture_state === 'ready'
      || value.scanner_capture_state === 'unavailable'
      || value.scanner_capture_state === 'browser_fallback'
      || value.scanner_capture_state === 'attention_required'
    )
    && (value.scanner_transport === 'keyboard_wedge' || value.scanner_transport === 'unknown')
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
    && Array.isArray(value.printers)
    && value.printers.every((printer) => isPrinterRecord(printer))
    && isHardwareProfile(value.profile)
    && isHardwareDiagnostics(value.diagnostics);
}
