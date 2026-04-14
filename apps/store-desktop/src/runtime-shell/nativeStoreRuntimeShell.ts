import { invoke as tauriInvoke } from '@tauri-apps/api/core';
import type {
  StoreRuntimeShellAdapter,
  StoreRuntimeShellInvoke,
  StoreRuntimeShellStatus,
} from './storeRuntimeShellContract';
import { isStoreRuntimeShellStatus } from './storeRuntimeShellContract';

export interface NativeStoreRuntimeShellOptions {
  invoke?: StoreRuntimeShellInvoke;
}

export function isNativeStoreRuntimeShellAvailable(): boolean {
  return typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window;
}

function toRuntimeShellStatus(value: unknown): StoreRuntimeShellStatus {
  if (isStoreRuntimeShellStatus(value)) {
    return {
      ...value,
      hub_service_state: value.hub_service_state ?? null,
      hub_service_url: value.hub_service_url ?? null,
      hub_manifest_url: value.hub_manifest_url ?? null,
    };
  }
  throw new Error('Native runtime shell bridge returned an invalid payload.');
}

export function createNativeStoreRuntimeShell(options: NativeStoreRuntimeShellOptions = {}): StoreRuntimeShellAdapter {
  const invoke = options.invoke ?? tauriInvoke;

  return {
    async getStatus() {
      return toRuntimeShellStatus(await invoke('cmd_get_store_runtime_shell_status'));
    },
  };
}
