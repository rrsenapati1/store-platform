import type {
  StoreRuntimeHardwareAdapter,
  StoreRuntimeHardwareStatus,
} from './storeRuntimeHardwareContract';

function buildBrowserFallbackStatus(): StoreRuntimeHardwareStatus {
  return {
    bridge_state: 'browser_fallback',
    printers: [],
    profile: {
      receipt_printer_name: null,
      label_printer_name: null,
      updated_at: null,
    },
    diagnostics: {
      scanner_capture_state: 'browser_fallback',
      last_print_status: null,
      last_print_message: null,
      last_printed_at: null,
      last_scan_at: null,
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
  };
}
