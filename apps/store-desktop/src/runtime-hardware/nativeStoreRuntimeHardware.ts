import { invoke as tauriInvoke } from '@tauri-apps/api/core';
import { createBrowserStoreRuntimeHardware } from './browserStoreRuntimeHardware';
import type {
  StoreRuntimeHardwareAdapter,
  StoreRuntimeHardwareInvoke,
  StoreRuntimeHardwarePrintJobInput,
  StoreRuntimeHardwareProfileInput,
  StoreRuntimeHardwareStatus,
} from './storeRuntimeHardwareContract';
import { isStoreRuntimeHardwareStatus } from './storeRuntimeHardwareContract';

export interface NativeStoreRuntimeHardwareOptions {
  invoke?: StoreRuntimeHardwareInvoke;
}

export function isNativeStoreRuntimeHardwareAvailable(): boolean {
  return typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window;
}

function shouldFallbackToBrowserHardware(error: unknown) {
  if (!(error instanceof Error)) {
    return false;
  }
  return /Unexpected command:\s*cmd_(get|save)_store_runtime_hardware_|Unexpected command:\s*cmd_dispatch_store_runtime_print_job/i.test(
    error.message,
  );
}

function toHardwareStatus(value: unknown): StoreRuntimeHardwareStatus {
  if (isStoreRuntimeHardwareStatus(value)) {
    return value;
  }
  throw new Error('Native runtime hardware bridge returned an invalid payload.');
}

export function createNativeStoreRuntimeHardware(options: NativeStoreRuntimeHardwareOptions = {}): StoreRuntimeHardwareAdapter {
  const invoke = options.invoke ?? tauriInvoke;
  const browserFallback = createBrowserStoreRuntimeHardware();

  return {
    async getStatus() {
      try {
        return toHardwareStatus(await invoke('cmd_get_store_runtime_hardware_status'));
      } catch (error) {
        if (shouldFallbackToBrowserHardware(error)) {
          return browserFallback.getStatus();
        }
        throw error;
      }
    },
    async saveProfile(profile: StoreRuntimeHardwareProfileInput) {
      try {
        return toHardwareStatus(await invoke('cmd_save_store_runtime_hardware_profile', {
          receipt_printer_name: profile.receipt_printer_name,
          label_printer_name: profile.label_printer_name,
        }));
      } catch (error) {
        if (shouldFallbackToBrowserHardware(error)) {
          return browserFallback.saveProfile(profile);
        }
        throw error;
      }
    },
    async dispatchPrintJob(job: StoreRuntimeHardwarePrintJobInput) {
      try {
        return toHardwareStatus(await invoke('cmd_dispatch_store_runtime_print_job', {
          job,
        }));
      } catch (error) {
        if (shouldFallbackToBrowserHardware(error)) {
          return browserFallback.dispatchPrintJob(job);
        }
        throw error;
      }
    },
  };
}
