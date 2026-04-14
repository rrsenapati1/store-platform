import { invoke as tauriInvoke } from '@tauri-apps/api/core';
import type { ControlPlaneInventorySnapshotRecord } from '@store/types';

export const STORE_RUNTIME_CONTINUITY_KEY = 'store.runtime-continuity.v1';
export const STORE_RUNTIME_CONTINUITY_SCHEMA_VERSION = 1;

export type StoreRuntimeOfflineSaleLineRecord = {
  product_id: string;
  product_name: string;
  sku_code: string;
  hsn_sac_code?: string;
  quantity: number;
  unit_price: number;
  gst_rate: number;
  line_subtotal: number;
  tax_total: number;
  line_total: number;
};

export type StoreRuntimeOfflineSaleTaxLineRecord = {
  tax_type: string;
  tax_rate: number;
  taxable_amount: number;
  tax_amount: number;
};

export type StoreRuntimeOfflineSaleRecord = {
  continuity_sale_id: string;
  continuity_invoice_number: string;
  tenant_id: string;
  branch_id: string;
  hub_device_id: string;
  staff_actor_id: string;
  customer_name: string;
  customer_gstin?: string | null;
  invoice_kind: string;
  irn_status: string;
  payment_method: string;
  subtotal: number;
  cgst_total: number;
  sgst_total: number;
  igst_total: number;
  grand_total: number;
  issued_offline_at: string;
  idempotency_key: string;
  reconciliation_state: 'PENDING_REPLAY' | 'REPLAYING' | 'RECONCILED' | 'CONFLICT' | 'REJECTED';
  lines: StoreRuntimeOfflineSaleLineRecord[];
  tax_lines: StoreRuntimeOfflineSaleTaxLineRecord[];
  replayed_sale_id?: string | null;
  replayed_invoice_number?: string | null;
  replay_error?: string | null;
};

export type StoreRuntimeOfflineConflictRecord = {
  continuity_sale_id: string;
  reason: string;
  message: string;
  recorded_at: string;
};

export interface StoreRuntimeContinuitySnapshot {
  schema_version: typeof STORE_RUNTIME_CONTINUITY_SCHEMA_VERSION;
  authority: 'BRANCH_HUB_CONTINUITY';
  cached_at: string;
  tenant_id: string;
  branch_id: string;
  branch_code: string;
  hub_device_id: string;
  next_continuity_invoice_sequence: number;
  inventory_snapshot: ControlPlaneInventorySnapshotRecord[];
  offline_sales: StoreRuntimeOfflineSaleRecord[];
  conflicts: StoreRuntimeOfflineConflictRecord[];
  last_reconciled_at: string | null;
}

export interface StoreRuntimeContinuityPersistence {
  authority: 'BRANCH_HUB_CONTINUITY';
  backend_kind: 'browser_storage' | 'native_sqlite';
  backend_label: string;
  cached_at: string | null;
  detail: string | null;
  location: string | null;
  snapshot_present: boolean;
}

export interface StoreRuntimeContinuityAdapter {
  load(): Promise<StoreRuntimeContinuitySnapshot | null>;
  save(snapshot: StoreRuntimeContinuitySnapshot): Promise<StoreRuntimeContinuityPersistence>;
  clear(): Promise<StoreRuntimeContinuityPersistence>;
  getPersistence(): Promise<StoreRuntimeContinuityPersistence>;
}

type StorageLike = Pick<Storage, 'getItem' | 'setItem' | 'removeItem'>;
type StorageResolver = () => StorageLike | null | undefined;
type ContinuityInvoke = (command: string, payload?: Record<string, unknown>) => Promise<unknown>;

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

function isStorageLike(value: unknown): value is StorageLike {
  return isObject(value)
    && typeof value.getItem === 'function'
    && typeof value.setItem === 'function'
    && typeof value.removeItem === 'function';
}

function isOfflineSaleLineRecord(value: unknown): value is StoreRuntimeOfflineSaleLineRecord {
  if (!isObject(value)) {
    return false;
  }
  return typeof value.product_id === 'string'
    && typeof value.product_name === 'string'
    && typeof value.sku_code === 'string'
    && typeof value.quantity === 'number'
    && typeof value.unit_price === 'number'
    && typeof value.gst_rate === 'number'
    && typeof value.line_subtotal === 'number'
    && typeof value.tax_total === 'number'
    && typeof value.line_total === 'number';
}

function isOfflineSaleTaxLineRecord(value: unknown): value is StoreRuntimeOfflineSaleTaxLineRecord {
  if (!isObject(value)) {
    return false;
  }
  return typeof value.tax_type === 'string'
    && typeof value.tax_rate === 'number'
    && typeof value.taxable_amount === 'number'
    && typeof value.tax_amount === 'number';
}

function isOfflineSaleRecord(value: unknown): value is StoreRuntimeOfflineSaleRecord {
  if (!isObject(value)) {
    return false;
  }
  return typeof value.continuity_sale_id === 'string'
    && typeof value.continuity_invoice_number === 'string'
    && typeof value.tenant_id === 'string'
    && typeof value.branch_id === 'string'
    && typeof value.hub_device_id === 'string'
    && typeof value.staff_actor_id === 'string'
    && typeof value.customer_name === 'string'
    && (typeof value.customer_gstin === 'string' || value.customer_gstin === null || typeof value.customer_gstin === 'undefined')
    && typeof value.invoice_kind === 'string'
    && typeof value.irn_status === 'string'
    && typeof value.payment_method === 'string'
    && typeof value.subtotal === 'number'
    && typeof value.cgst_total === 'number'
    && typeof value.sgst_total === 'number'
    && typeof value.igst_total === 'number'
    && typeof value.grand_total === 'number'
    && typeof value.issued_offline_at === 'string'
    && typeof value.idempotency_key === 'string'
    && typeof value.reconciliation_state === 'string'
    && Array.isArray(value.lines)
    && value.lines.every(isOfflineSaleLineRecord)
    && Array.isArray(value.tax_lines)
    && value.tax_lines.every(isOfflineSaleTaxLineRecord)
    && (typeof value.replayed_sale_id === 'string' || value.replayed_sale_id === null || typeof value.replayed_sale_id === 'undefined')
    && (typeof value.replayed_invoice_number === 'string' || value.replayed_invoice_number === null || typeof value.replayed_invoice_number === 'undefined')
    && (typeof value.replay_error === 'string' || value.replay_error === null || typeof value.replay_error === 'undefined');
}

function isOfflineConflictRecord(value: unknown): value is StoreRuntimeOfflineConflictRecord {
  if (!isObject(value)) {
    return false;
  }
  return typeof value.continuity_sale_id === 'string'
    && typeof value.reason === 'string'
    && typeof value.message === 'string'
    && typeof value.recorded_at === 'string';
}

export function isStoreRuntimeContinuitySnapshot(value: unknown): value is StoreRuntimeContinuitySnapshot {
  if (!isObject(value)) {
    return false;
  }
  return value.schema_version === STORE_RUNTIME_CONTINUITY_SCHEMA_VERSION
    && value.authority === 'BRANCH_HUB_CONTINUITY'
    && typeof value.cached_at === 'string'
    && typeof value.tenant_id === 'string'
    && typeof value.branch_id === 'string'
    && typeof value.branch_code === 'string'
    && typeof value.hub_device_id === 'string'
    && typeof value.next_continuity_invoice_sequence === 'number'
    && Array.isArray(value.inventory_snapshot)
    && Array.isArray(value.offline_sales)
    && value.offline_sales.every(isOfflineSaleRecord)
    && Array.isArray(value.conflicts)
    && value.conflicts.every(isOfflineConflictRecord)
    && (typeof value.last_reconciled_at === 'string' || value.last_reconciled_at === null);
}

function isPersistence(value: unknown): value is StoreRuntimeContinuityPersistence {
  if (!isObject(value)) {
    return false;
  }
  return value.authority === 'BRANCH_HUB_CONTINUITY'
    && typeof value.backend_kind === 'string'
    && typeof value.backend_label === 'string'
    && (typeof value.cached_at === 'string' || value.cached_at === null)
    && (typeof value.detail === 'string' || value.detail === null)
    && (typeof value.location === 'string' || value.location === null)
    && typeof value.snapshot_present === 'boolean';
}

function toPersistence(value: unknown): StoreRuntimeContinuityPersistence {
  if (isPersistence(value)) {
    return value;
  }
  throw new Error('Runtime continuity bridge returned an invalid persistence payload.');
}

function buildBrowserPersistence(args: {
  cachedAt: string | null;
  snapshotPresent: boolean;
}): StoreRuntimeContinuityPersistence {
  return {
    authority: 'BRANCH_HUB_CONTINUITY',
    backend_kind: 'browser_storage',
    backend_label: 'Browser continuity storage',
    cached_at: args.cachedAt,
    detail: null,
    location: STORE_RUNTIME_CONTINUITY_KEY,
    snapshot_present: args.snapshotPresent,
  };
}

function resolveBrowserStorage(): StorageLike | null {
  if (typeof window === 'undefined') {
    return null;
  }
  return isStorageLike(window.localStorage) ? window.localStorage : null;
}

function createBrowserStoreRuntimeContinuityStore(
  resolveStorage: StorageResolver = resolveBrowserStorage,
): StoreRuntimeContinuityAdapter {
  return {
    async load() {
      const storage = resolveStorage();
      if (!storage) {
        return null;
      }
      const raw = storage.getItem(STORE_RUNTIME_CONTINUITY_KEY);
      if (!raw) {
        return null;
      }
      try {
        const parsed = JSON.parse(raw) as unknown;
        if (!isStoreRuntimeContinuitySnapshot(parsed)) {
          storage.removeItem(STORE_RUNTIME_CONTINUITY_KEY);
          return null;
        }
        return parsed;
      } catch {
        storage.removeItem(STORE_RUNTIME_CONTINUITY_KEY);
        return null;
      }
    },
    async save(snapshot) {
      const storage = resolveStorage();
      if (storage) {
        storage.setItem(STORE_RUNTIME_CONTINUITY_KEY, JSON.stringify(snapshot));
      }
      return buildBrowserPersistence({
        cachedAt: snapshot.cached_at,
        snapshotPresent: Boolean(storage),
      });
    },
    async clear() {
      resolveStorage()?.removeItem(STORE_RUNTIME_CONTINUITY_KEY);
      return buildBrowserPersistence({
        cachedAt: null,
        snapshotPresent: false,
      });
    },
    async getPersistence() {
      const snapshot = await this.load();
      return buildBrowserPersistence({
        cachedAt: snapshot?.cached_at ?? null,
        snapshotPresent: Boolean(snapshot),
      });
    },
  };
}

function isNativeStoreRuntimeAvailable(): boolean {
  return typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window;
}

function createNativeStoreRuntimeContinuityStore(options: {
  invoke?: ContinuityInvoke;
} = {}): StoreRuntimeContinuityAdapter {
  const invoke = options.invoke ?? tauriInvoke;

  return {
    async load() {
      const result = await invoke('cmd_load_store_runtime_continuity');
      if (result === null || typeof result === 'undefined') {
        return null;
      }
      if (!isStoreRuntimeContinuitySnapshot(result)) {
        await invoke('cmd_clear_store_runtime_continuity');
        return null;
      }
      return result;
    },
    async save(snapshot) {
      return toPersistence(await invoke('cmd_save_store_runtime_continuity', { snapshot }));
    },
    async clear() {
      return toPersistence(await invoke('cmd_clear_store_runtime_continuity'));
    },
    async getPersistence() {
      return toPersistence(await invoke('cmd_get_store_runtime_continuity_status'));
    },
  };
}

export function createResolvedStoreRuntimeContinuityStore(options: {
  browserStorage?: StorageResolver;
  invoke?: ContinuityInvoke;
  isNativeRuntime?: () => boolean;
} = {}): StoreRuntimeContinuityAdapter {
  const browserAdapter = createBrowserStoreRuntimeContinuityStore(
    options.browserStorage ?? resolveBrowserStorage,
  );
  if (!(options.isNativeRuntime ?? isNativeStoreRuntimeAvailable)()) {
    return browserAdapter;
  }
  return createNativeStoreRuntimeContinuityStore({ invoke: options.invoke });
}
