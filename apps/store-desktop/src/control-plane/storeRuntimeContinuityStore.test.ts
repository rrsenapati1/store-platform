import { describe, expect, test, vi } from 'vitest';
import type { ControlPlaneInventorySnapshotRecord } from '@store/types';
import {
  STORE_RUNTIME_CONTINUITY_KEY,
  createResolvedStoreRuntimeContinuityStore,
  type StoreRuntimeContinuitySnapshot,
} from './storeRuntimeContinuityStore';

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

function buildInventorySnapshot(): ControlPlaneInventorySnapshotRecord[] {
  return [
    {
      product_id: 'product-1',
      product_name: 'Classic Tea',
      sku_code: 'tea-classic-250g',
      stock_on_hand: 24,
      last_entry_type: 'PURCHASE_RECEIPT',
    },
  ];
}

function buildSnapshot(): StoreRuntimeContinuitySnapshot {
  return {
    schema_version: 1,
    authority: 'BRANCH_HUB_CONTINUITY',
    cached_at: '2026-04-14T18:00:00.000Z',
    tenant_id: 'tenant-acme',
    branch_id: 'branch-1',
    branch_code: 'blrflagship',
    hub_device_id: 'device-hub-1',
    next_continuity_invoice_sequence: 2,
    inventory_snapshot: buildInventorySnapshot(),
    offline_sales: [
      {
        continuity_sale_id: 'offline-sale-1',
        continuity_invoice_number: 'OFF-BLRFLAGSHIP-0001',
        tenant_id: 'tenant-acme',
        branch_id: 'branch-1',
        hub_device_id: 'device-hub-1',
        staff_actor_id: 'user-cashier',
        customer_name: 'Walk-in Customer',
        customer_gstin: null,
        invoice_kind: 'B2C',
        irn_status: 'NOT_REQUIRED',
        payment_method: 'Cash',
        subtotal: 388.5,
        cgst_total: 9.25,
        sgst_total: 9.25,
        igst_total: 0,
        grand_total: 388.5,
        issued_offline_at: '2026-04-14T18:00:00.000Z',
        idempotency_key: 'offline-replay-1',
        reconciliation_state: 'PENDING_REPLAY',
        lines: [
          {
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            hsn_sac_code: '0902',
            quantity: 4,
            unit_price: 92.5,
            gst_rate: 5,
            line_subtotal: 370,
            tax_total: 18.5,
            line_total: 388.5,
          },
        ],
        tax_lines: [
          {
            tax_type: 'CGST',
            tax_rate: 2.5,
            taxable_amount: 370,
            tax_amount: 9.25,
          },
          {
            tax_type: 'SGST',
            tax_rate: 2.5,
            taxable_amount: 370,
            tax_amount: 9.25,
          },
        ],
        replayed_sale_id: null,
        replayed_invoice_number: null,
        replay_error: null,
      },
    ],
    conflicts: [],
    last_reconciled_at: null,
  };
}

describe('store runtime continuity store', () => {
  test('round-trips the continuity snapshot through browser storage', async () => {
    const storage = new MemoryStorage();
    const adapter = createResolvedStoreRuntimeContinuityStore({
      browserStorage: () => storage,
      isNativeRuntime: () => false,
    });

    const saved = await adapter.save(buildSnapshot());
    const loaded = await adapter.load();

    expect(saved.authority).toBe('BRANCH_HUB_CONTINUITY');
    expect(loaded?.offline_sales).toHaveLength(1);
    expect(loaded?.next_continuity_invoice_sequence).toBe(2);
    expect(storage.getItem(STORE_RUNTIME_CONTINUITY_KEY)).not.toBeNull();
  });

  test('uses the native bridge when packaged runtime is available', async () => {
    const invoke = vi.fn(async (command: string, payload?: Record<string, unknown>) => {
      if (command === 'cmd_load_store_runtime_continuity') {
        return buildSnapshot();
      }
      if (command === 'cmd_save_store_runtime_continuity') {
        return {
          authority: (payload?.snapshot as StoreRuntimeContinuitySnapshot).authority,
          backend_kind: 'native_sqlite',
          backend_label: 'Native SQLite continuity store',
          cached_at: (payload?.snapshot as StoreRuntimeContinuitySnapshot).cached_at,
          detail: null,
          location: 'C:/Store/store-runtime-continuity.sqlite3',
          snapshot_present: true,
        };
      }
      if (command === 'cmd_get_store_runtime_continuity_status') {
        return {
          authority: 'BRANCH_HUB_CONTINUITY',
          backend_kind: 'native_sqlite',
          backend_label: 'Native SQLite continuity store',
          cached_at: '2026-04-14T18:00:00.000Z',
          detail: null,
          location: 'C:/Store/store-runtime-continuity.sqlite3',
          snapshot_present: true,
        };
      }
      if (command === 'cmd_clear_store_runtime_continuity') {
        return {
          authority: 'BRANCH_HUB_CONTINUITY',
          backend_kind: 'native_sqlite',
          backend_label: 'Native SQLite continuity store',
          cached_at: null,
          detail: null,
          location: 'C:/Store/store-runtime-continuity.sqlite3',
          snapshot_present: false,
        };
      }
      throw new Error(`Unexpected command: ${command}`);
    });

    const adapter = createResolvedStoreRuntimeContinuityStore({
      invoke,
      isNativeRuntime: () => true,
    });

    await expect(adapter.load()).resolves.toEqual(buildSnapshot());
    await expect(adapter.getPersistence()).resolves.toEqual({
      authority: 'BRANCH_HUB_CONTINUITY',
      backend_kind: 'native_sqlite',
      backend_label: 'Native SQLite continuity store',
      cached_at: '2026-04-14T18:00:00.000Z',
      detail: null,
      location: 'C:/Store/store-runtime-continuity.sqlite3',
      snapshot_present: true,
    });

    await adapter.save(buildSnapshot());
    await adapter.clear();

    expect(invoke).toHaveBeenCalledWith('cmd_load_store_runtime_continuity');
    expect(invoke).toHaveBeenCalledWith('cmd_get_store_runtime_continuity_status');
    expect(invoke).toHaveBeenCalledWith('cmd_save_store_runtime_continuity', { snapshot: buildSnapshot() });
    expect(invoke).toHaveBeenCalledWith('cmd_clear_store_runtime_continuity');
  });
});
