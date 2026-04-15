import type {
  StoreRuntimeHardwareAdapter,
  StoreRuntimeHardwareStatus,
} from './storeRuntimeHardwareContract';

function buildBrowserFallbackStatus(): StoreRuntimeHardwareStatus {
  return {
    bridge_state: 'browser_fallback',
    scanners: [],
    printers: [],
    profile: {
      receipt_printer_name: null,
      label_printer_name: null,
      preferred_scanner_id: null,
      updated_at: null,
    },
    diagnostics: {
      scanner_capture_state: 'browser_fallback',
      scanner_transport: 'unknown',
      last_print_status: null,
      last_print_message: null,
      last_printed_at: null,
      last_scan_at: null,
      last_scan_barcode_preview: null,
      scanner_status_message: 'Scanner capture diagnostics require the packaged desktop runtime.',
      scanner_setup_hint: 'Open the packaged desktop runtime for wedge-scanner capture.',
    },
  };
}

export function createBrowserStoreRuntimeHardware(): StoreRuntimeHardwareAdapter {
  return {
    async getStatus() {
      return buildBrowserFallbackStatus();
    },
    async saveProfile() {
      return buildBrowserFallbackStatus();
    },
    async dispatchPrintJob() {
      return buildBrowserFallbackStatus();
    },
    async recordScannerActivity() {
      return buildBrowserFallbackStatus();
    },
  };
}
