import { describe, expect, test } from 'vitest';
import type {
  ControlPlaneActor,
  ControlPlaneBranchCatalogItem,
  ControlPlaneBranchRecord,
  ControlPlaneDeviceRecord,
  ControlPlaneInventorySnapshotRecord,
  ControlPlaneSaleRecord,
  ControlPlaneTenant,
} from '@store/types';
import {
  STORE_RUNTIME_CACHE_KEY,
  createBrowserStoreRuntimeCache,
  type StoreRuntimeCacheSnapshot,
} from './storeRuntimeCache';

class MemoryStorage implements Storage {
  private readonly data = new Map<string, string>();

  get length() {
    return this.data.size;
  }

  clear(): void {
    this.data.clear();
  }

  getItem(key: string): string | null {
    return this.data.get(key) ?? null;
  }

  key(index: number): string | null {
    return Array.from(this.data.keys())[index] ?? null;
  }

  removeItem(key: string): void {
    this.data.delete(key);
  }

  setItem(key: string, value: string): void {
    this.data.set(key, value);
  }
}

function buildSnapshot(): StoreRuntimeCacheSnapshot {
  const actor: ControlPlaneActor = {
    user_id: 'user-cashier',
    email: 'cashier@acme.local',
    full_name: 'Counter Cashier',
    is_platform_admin: false,
    tenant_memberships: [],
    branch_memberships: [{ tenant_id: 'tenant-acme', branch_id: 'branch-1', role_name: 'cashier', status: 'ACTIVE' }],
  };
  const tenant: ControlPlaneTenant = {
    id: 'tenant-acme',
    name: 'Acme Retail',
    slug: 'acme-retail',
    status: 'ACTIVE',
    onboarding_status: 'BRANCH_READY',
  };
  const branches: ControlPlaneBranchRecord[] = [
    { branch_id: 'branch-1', tenant_id: 'tenant-acme', name: 'Bengaluru Flagship', code: 'blr-flagship', status: 'ACTIVE' },
  ];
  const branchCatalogItems: ControlPlaneBranchCatalogItem[] = [
    {
      id: 'catalog-item-1',
      tenant_id: 'tenant-acme',
      branch_id: 'branch-1',
      product_id: 'product-1',
      product_name: 'Classic Tea',
      sku_code: 'tea-classic-250g',
      barcode: '8901234567890',
      hsn_sac_code: '0902',
      gst_rate: 5,
      mrp: 120,
      category_code: 'TEA',
      base_selling_price: 92.5,
      selling_price_override: null,
      effective_selling_price: 92.5,
      availability_status: 'ACTIVE',
    },
  ];
  const inventorySnapshot: ControlPlaneInventorySnapshotRecord[] = [
    { product_id: 'product-1', product_name: 'Classic Tea', sku_code: 'tea-classic-250g', stock_on_hand: 24, last_entry_type: 'PURCHASE_RECEIPT' },
  ];
  const sales: ControlPlaneSaleRecord[] = [
    {
      sale_id: 'sale-1',
      invoice_number: 'SINV-BLRFLAGSHIP-0001',
      customer_name: 'Acme Traders',
      invoice_kind: 'B2B',
      irn_status: 'IRN_PENDING',
      payment_method: 'UPI',
      grand_total: 388.5,
      promotion_campaign_id: null,
      promotion_code_id: null,
      promotion_code: null,
      promotion_discount_amount: 0,
      store_credit_amount: 0,
      loyalty_points_redeemed: 0,
      loyalty_discount_amount: 0,
      loyalty_points_earned: 388,
      issued_on: '2026-04-13',
    },
  ];
  const runtimeDevices: ControlPlaneDeviceRecord[] = [
    {
      id: 'device-1',
      tenant_id: 'tenant-acme',
      branch_id: 'branch-1',
      device_name: 'Counter Desktop 1',
      device_code: 'counter-1',
      session_surface: 'store_desktop',
      runtime_profile: 'desktop_spoke',
      status: 'ACTIVE',
      assigned_staff_profile_id: null,
      assigned_staff_full_name: null,
      last_seen_at: '2026-04-13T23:10:00',
    },
  ];

  return {
    schema_version: 1,
    cached_at: '2026-04-13T23:12:00',
    authority: 'CONTROL_PLANE_ONLY',
    actor,
    tenant,
    branches,
    branch_catalog_items: branchCatalogItems,
    inventory_snapshot: inventorySnapshot,
    sales,
    runtime_devices: runtimeDevices,
    selected_runtime_device_id: 'device-1',
    runtime_heartbeat: {
      device_id: 'device-1',
      status: 'ACTIVE',
      last_seen_at: '2026-04-13T23:10:00',
      queued_job_count: 1,
    },
    print_jobs: [],
    latest_print_job: null,
    latest_sale: null,
    latest_sale_return: null,
    latest_exchange: null,
    pending_mutations: [],
  };
}

describe('store runtime cache browser adapter', () => {
  test('round-trips the cache snapshot without persisting session secrets', async () => {
    const storage = new MemoryStorage();
    const cache = createBrowserStoreRuntimeCache(() => storage);
    const snapshot = buildSnapshot();

    const persistence = await cache.save(snapshot);
    const loaded = await cache.load();

    expect(loaded).toEqual(snapshot);
    expect(persistence.backend_kind).toBe('browser_storage');
    expect(persistence.snapshot_present).toBe(true);
    expect(storage.getItem(STORE_RUNTIME_CACHE_KEY)).not.toContain('session-cashier');
  });

  test('drops malformed or incompatible cached payloads instead of treating them as authority', async () => {
    const storage = new MemoryStorage();
    const cache = createBrowserStoreRuntimeCache(() => storage);
    storage.setItem(STORE_RUNTIME_CACHE_KEY, JSON.stringify({ schema_version: 99, actor: { email: 'wrong@shape' } }));

    await expect(cache.load()).resolves.toBeNull();
    expect(storage.getItem(STORE_RUNTIME_CACHE_KEY)).toBeNull();
  });

  test('reports persistence metadata for browser storage', async () => {
    const storage = new MemoryStorage();
    const cache = createBrowserStoreRuntimeCache(() => storage);

    expect(await cache.getPersistence()).toEqual({
      backend_kind: 'browser_storage',
      backend_label: 'Browser local storage',
      cached_at: null,
      detail: null,
      location: STORE_RUNTIME_CACHE_KEY,
      snapshot_present: false,
    });

    await cache.save(buildSnapshot());

    await expect(cache.getPersistence()).resolves.toEqual({
      backend_kind: 'browser_storage',
      backend_label: 'Browser local storage',
      cached_at: '2026-04-13T23:12:00',
      detail: null,
      location: STORE_RUNTIME_CACHE_KEY,
      snapshot_present: true,
    });
  });
});
