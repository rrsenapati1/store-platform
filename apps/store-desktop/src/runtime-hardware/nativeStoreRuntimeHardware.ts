import { invoke as tauriInvoke } from '@tauri-apps/api/core';
import type {
  StoreRuntimeHardwareAdapter,
  StoreRuntimeHardwareInvoke,
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

function toHardwareStatus(value: unknown): StoreRuntimeHardwareStatus {
  if (isStoreRuntimeHardwareStatus(value)) {
    return value;
  }
  throw new Error('Native runtime hardware bridge returned an invalid payload.');
}

export function createNativeStoreRuntimeHardware(options: NativeStoreRuntimeHardwareOptions = {}): StoreRuntimeHardwareAdapter {
  const invoke = options.invoke ?? tauriInvoke;

  return {
    async getStatus() {
      return toHardwareStatus(await invoke('cmd_get_store_runtime_hardware_status'));
    },
    async saveProfile(profile: StoreRuntimeHardwareProfileInput) {
      return toHardwareStatus(await invoke('cmd_save_store_runtime_hardware_profile', {
        receipt_printer_name: profile.receipt_printer_name,
        label_printer_name: profile.label_printer_name,
      }));
    },
  };
}
