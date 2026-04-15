import type {
  StoreRuntimeHardwareAdapter,
  StoreRuntimeHardwareStatus,
} from './storeRuntimeHardwareContract';

function buildBrowserFallbackStatus(): StoreRuntimeHardwareStatus {
  return {
    bridge_state: 'browser_fallback',
    scales: [],
    scanners: [],
    printers: [],
    profile: {
      receipt_printer_name: null,
      label_printer_name: null,
      cash_drawer_printer_name: null,
      preferred_scale_id: null,
      preferred_scanner_id: null,
      updated_at: null,
    },
    diagnostics: {
      scale_capture_state: 'browser_fallback',
      scanner_capture_state: 'browser_fallback',
      scanner_transport: 'unknown',
      last_print_status: null,
      last_print_message: null,
      last_printed_at: null,
      last_cash_drawer_status: null,
      last_cash_drawer_message: null,
      last_cash_drawer_opened_at: null,
      last_weight_value: null,
      last_weight_unit: null,
      last_weight_status: null,
      last_weight_message: null,
      last_weight_read_at: null,
      last_scan_at: null,
      last_scan_barcode_preview: null,
      scale_status_message: 'Weighing scale support requires the packaged desktop runtime.',
      scale_setup_hint: 'Open the packaged desktop runtime to assign and read a local serial scale.',
      cash_drawer_status_message: 'Cash drawer controls require the packaged desktop runtime.',
      cash_drawer_setup_hint: 'Open the packaged desktop runtime to assign a local printer-backed cash drawer.',
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
    async openCashDrawer() {
      return buildBrowserFallbackStatus();
    },
    async readScaleWeight() {
      return buildBrowserFallbackStatus();
    },
    async recordScannerActivity() {
      return buildBrowserFallbackStatus();
    },
  };
}
