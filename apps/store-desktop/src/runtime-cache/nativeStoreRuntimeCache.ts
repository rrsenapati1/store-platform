import { invoke as tauriInvoke } from '@tauri-apps/api/core';
import {
  type StoreRuntimeCacheAdapter,
  type StoreRuntimeCacheInvoke,
  type StoreRuntimeCachePersistence,
  type StoreRuntimeCacheSnapshot,
  isStoreRuntimeCacheSnapshot,
} from './storeRuntimeCacheContract';

export interface NativeStoreRuntimeCacheOptions {
  invoke?: StoreRuntimeCacheInvoke;
}

export function isNativeStoreRuntimeAvailable(): boolean {
  return typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window;
}

function isPersistence(value: unknown): value is StoreRuntimeCachePersistence {
  if (typeof value !== 'object' || value === null) {
    return false;
  }
  const record = value as Record<string, unknown>;
  return typeof record.backend_kind === 'string'
    && typeof record.backend_label === 'string'
    && (typeof record.cached_at === 'string' || record.cached_at === null)
    && (typeof record.detail === 'string' || record.detail === null)
    && (typeof record.location === 'string' || record.location === null)
    && typeof record.snapshot_present === 'boolean';
}

function toPersistence(value: unknown): StoreRuntimeCachePersistence {
  if (isPersistence(value)) {
    return value;
  }
  throw new Error('Native runtime cache bridge returned an invalid persistence payload.');
}

export function createNativeStoreRuntimeCache(options: NativeStoreRuntimeCacheOptions = {}): StoreRuntimeCacheAdapter {
  const invoke = options.invoke ?? tauriInvoke;

  return {
    async load() {
      const result = await invoke('cmd_load_store_runtime_cache');
      if (result === null || typeof result === 'undefined') {
        return null;
      }
      if (!isStoreRuntimeCacheSnapshot(result)) {
        await invoke('cmd_clear_store_runtime_cache');
        return null;
      }
      return result;
    },
    async save(snapshot: StoreRuntimeCacheSnapshot) {
      return toPersistence(await invoke('cmd_save_store_runtime_cache', { snapshot }));
    },
    async clear() {
      return toPersistence(await invoke('cmd_clear_store_runtime_cache'));
    },
    async getPersistence() {
      return toPersistence(await invoke('cmd_get_store_runtime_cache_status'));
    },
  };
}
