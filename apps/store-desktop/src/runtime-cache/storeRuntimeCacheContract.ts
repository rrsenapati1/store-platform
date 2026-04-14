import type {
  ControlPlaneActor,
  ControlPlaneBranchCatalogItem,
  ControlPlaneBranchRecord,
  ControlPlaneDeviceRecord,
  ControlPlaneExchange,
  ControlPlaneInventorySnapshotRecord,
  ControlPlanePrintJob,
  ControlPlaneRuntimeHeartbeat,
  ControlPlaneSale,
  ControlPlaneSaleRecord,
  ControlPlaneSaleReturn,
  ControlPlaneTenant,
} from '@store/types';

export const STORE_RUNTIME_CACHE_KEY = 'store.runtime-cache.v1';
export const STORE_RUNTIME_CACHE_SCHEMA_VERSION = 1;

export type StoreRuntimeCacheBackendKind = 'browser_storage' | 'native_sqlite' | 'unavailable';

interface StoreRuntimePendingMutationBase {
  id: string;
  tenant_id: string;
  branch_id: string;
  device_id: string;
  status: 'PENDING';
  created_at: string;
}

export interface StoreRuntimePendingHeartbeatMutation extends StoreRuntimePendingMutationBase {
  mutation_type: 'HEARTBEAT';
}

export interface StoreRuntimePendingSalesInvoicePrintMutation extends StoreRuntimePendingMutationBase {
  mutation_type: 'PRINT_SALES_INVOICE';
  reference_id: string;
  document_number: string;
  copies: number;
}

export interface StoreRuntimePendingCreditNotePrintMutation extends StoreRuntimePendingMutationBase {
  mutation_type: 'PRINT_CREDIT_NOTE';
  reference_id: string;
  document_number: string;
  copies: number;
}

export type StoreRuntimePendingMutation =
  | StoreRuntimePendingHeartbeatMutation
  | StoreRuntimePendingSalesInvoicePrintMutation
  | StoreRuntimePendingCreditNotePrintMutation;

export interface StoreRuntimeCacheSnapshot {
  schema_version: typeof STORE_RUNTIME_CACHE_SCHEMA_VERSION;
  cached_at: string;
  authority: 'CONTROL_PLANE_ONLY';
  actor: ControlPlaneActor | null;
  tenant: ControlPlaneTenant | null;
  branches: ControlPlaneBranchRecord[];
  branch_catalog_items: ControlPlaneBranchCatalogItem[];
  inventory_snapshot: ControlPlaneInventorySnapshotRecord[];
  sales: ControlPlaneSaleRecord[];
  runtime_devices: ControlPlaneDeviceRecord[];
  selected_runtime_device_id: string;
  runtime_heartbeat: ControlPlaneRuntimeHeartbeat | null;
  print_jobs: ControlPlanePrintJob[];
  latest_print_job: ControlPlanePrintJob | null;
  latest_sale: ControlPlaneSale | null;
  latest_sale_return: ControlPlaneSaleReturn | null;
  latest_exchange: ControlPlaneExchange | null;
  pending_mutations: StoreRuntimePendingMutation[];
}

export interface StoreRuntimeCachePersistence {
  backend_kind: StoreRuntimeCacheBackendKind;
  backend_label: string;
  cached_at: string | null;
  detail: string | null;
  location: string | null;
  snapshot_present: boolean;
}

export interface StoreRuntimeCacheAdapter {
  load(): Promise<StoreRuntimeCacheSnapshot | null>;
  save(snapshot: StoreRuntimeCacheSnapshot): Promise<StoreRuntimeCachePersistence>;
  clear(): Promise<StoreRuntimeCachePersistence>;
  getPersistence(): Promise<StoreRuntimeCachePersistence>;
}

export type StoreRuntimeCacheInvoke = (command: string, payload?: Record<string, unknown>) => Promise<unknown>;

export type StorageLike = Pick<Storage, 'getItem' | 'setItem' | 'removeItem'>;

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

export function isStorageLike(value: unknown): value is StorageLike {
  return isObject(value)
    && typeof value.getItem === 'function'
    && typeof value.setItem === 'function'
    && typeof value.removeItem === 'function';
}

export function isStoreRuntimeCacheSnapshot(value: unknown): value is StoreRuntimeCacheSnapshot {
  if (!isObject(value)) {
    return false;
  }
  if (value.schema_version !== STORE_RUNTIME_CACHE_SCHEMA_VERSION || value.authority !== 'CONTROL_PLANE_ONLY') {
    return false;
  }
  return Array.isArray(value.branches)
    && Array.isArray(value.branch_catalog_items)
    && Array.isArray(value.inventory_snapshot)
    && Array.isArray(value.sales)
    && Array.isArray(value.runtime_devices)
    && Array.isArray(value.print_jobs)
    && Array.isArray(value.pending_mutations);
}
