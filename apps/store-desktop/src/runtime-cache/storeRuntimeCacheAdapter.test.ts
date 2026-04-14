import { describe, expect, test, vi } from 'vitest';
import { STORE_RUNTIME_CACHE_KEY, createResolvedStoreRuntimeCache, type StoreRuntimeCacheSnapshot } from './storeRuntimeCache';

function buildSnapshot(): StoreRuntimeCacheSnapshot {
  return {
    schema_version: 1,
    cached_at: '2026-04-14T05:00:00.000Z',
    authority: 'CONTROL_PLANE_ONLY',
    actor: null,
    tenant: null,
    branches: [],
    branch_catalog_items: [],
    inventory_snapshot: [],
    sales: [],
    runtime_devices: [],
    selected_runtime_device_id: '',
    runtime_heartbeat: null,
    print_jobs: [],
    latest_print_job: null,
    latest_sale: null,
    latest_sale_return: null,
    latest_exchange: null,
    pending_mutations: [],
  };
}

describe('resolved store runtime cache adapter', () => {
  test('uses native sqlite bridge when packaged runtime is available', async () => {
    const invoke = vi.fn(async (command: string, payload?: Record<string, unknown>) => {
      if (command === 'cmd_load_store_runtime_cache') {
        return buildSnapshot();
      }
      if (command === 'cmd_get_store_runtime_cache_status') {
        return {
          backend_kind: 'native_sqlite',
          backend_label: 'Native SQLite runtime cache',
          cached_at: '2026-04-14T05:00:00.000Z',
          detail: null,
          location: 'C:/Store/runtime-cache.sqlite3',
          snapshot_present: true,
        };
      }
      if (command === 'cmd_save_store_runtime_cache') {
        return {
          backend_kind: 'native_sqlite',
          backend_label: 'Native SQLite runtime cache',
          cached_at: (payload?.snapshot as StoreRuntimeCacheSnapshot).cached_at,
          detail: null,
          location: 'C:/Store/runtime-cache.sqlite3',
          snapshot_present: true,
        };
      }
      if (command === 'cmd_clear_store_runtime_cache') {
        return {
          backend_kind: 'native_sqlite',
          backend_label: 'Native SQLite runtime cache',
          cached_at: null,
          detail: null,
          location: 'C:/Store/runtime-cache.sqlite3',
          snapshot_present: false,
        };
      }
      throw new Error(`Unexpected command: ${command}`);
    });
    const storage = {
      getItem: vi.fn(() => null),
      setItem: vi.fn(),
      removeItem: vi.fn(),
    };
    const adapter = createResolvedStoreRuntimeCache({
      browserStorage: () => storage,
      invoke,
      isNativeRuntime: () => true,
    });

    await expect(adapter.load()).resolves.toEqual(buildSnapshot());
    await expect(adapter.getPersistence()).resolves.toEqual({
      backend_kind: 'native_sqlite',
      backend_label: 'Native SQLite runtime cache',
      cached_at: '2026-04-14T05:00:00.000Z',
      detail: null,
      location: 'C:/Store/runtime-cache.sqlite3',
      snapshot_present: true,
    });

    await adapter.save(buildSnapshot());
    await adapter.clear();

    expect(invoke).toHaveBeenCalledWith('cmd_load_store_runtime_cache');
    expect(invoke).toHaveBeenCalledWith('cmd_get_store_runtime_cache_status');
    expect(invoke).toHaveBeenCalledWith('cmd_save_store_runtime_cache', { snapshot: buildSnapshot() });
    expect(invoke).toHaveBeenCalledWith('cmd_clear_store_runtime_cache');
    expect(storage.setItem).not.toHaveBeenCalled();
  });

  test('falls back to browser storage in the web shell', async () => {
    const storage = {
      getItem: vi.fn(() => JSON.stringify(buildSnapshot())),
      setItem: vi.fn(),
      removeItem: vi.fn(),
    };
    const adapter = createResolvedStoreRuntimeCache({
      browserStorage: () => storage,
      isNativeRuntime: () => false,
    });

    await expect(adapter.load()).resolves.toEqual(buildSnapshot());

    expect(storage.getItem).toHaveBeenCalledWith(STORE_RUNTIME_CACHE_KEY);
  });
});
