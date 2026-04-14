/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { App } from '../App';
import { STORE_RUNTIME_CACHE_KEY } from '../runtime-cache/storeRuntimeCache';

type MockResponse = {
  ok: boolean;
  status: number;
  json: () => Promise<unknown>;
};

function jsonResponse(body: unknown, status = 200): MockResponse {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  };
}

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

describe('store runtime cache boundary', () => {
  const originalFetch = globalThis.fetch;
  const originalLocalStorage = globalThis.localStorage;

  beforeEach(() => {
    Object.defineProperty(globalThis, 'localStorage', {
      configurable: true,
      value: new MemoryStorage(),
    });
    localStorage.setItem(
      STORE_RUNTIME_CACHE_KEY,
      JSON.stringify({
        schema_version: 1,
        cached_at: '2026-04-13T22:45:00',
        authority: 'CONTROL_PLANE_ONLY',
        actor: {
          user_id: 'user-cashier',
          email: 'cashier@acme.local',
          full_name: 'Counter Cashier',
          is_platform_admin: false,
          tenant_memberships: [],
          branch_memberships: [{ tenant_id: 'tenant-acme', branch_id: 'branch-1', role_name: 'cashier', status: 'ACTIVE' }],
        },
        tenant: {
          id: 'tenant-acme',
          name: 'Acme Retail',
          slug: 'acme-retail',
          status: 'ACTIVE',
          onboarding_status: 'BRANCH_READY',
        },
        branches: [{ branch_id: 'branch-1', tenant_id: 'tenant-acme', name: 'Cached Flagship', code: 'blr-cache', status: 'ACTIVE' }],
        branch_catalog_items: [
          {
            id: 'catalog-item-1',
            tenant_id: 'tenant-acme',
            branch_id: 'branch-1',
            product_id: 'product-1',
            product_name: 'Cached Tea',
            sku_code: 'tea-cache-250g',
            barcode: '8901234567890',
            hsn_sac_code: '0902',
            gst_rate: 5,
            base_selling_price: 91,
            selling_price_override: null,
            effective_selling_price: 91,
            availability_status: 'ACTIVE',
          },
        ],
        inventory_snapshot: [
          {
            product_id: 'product-1',
            product_name: 'Cached Tea',
            sku_code: 'tea-cache-250g',
            stock_on_hand: 11,
            last_entry_type: 'SALE',
          },
        ],
        sales: [],
        runtime_devices: [
          {
            id: 'device-1',
            tenant_id: 'tenant-acme',
            branch_id: 'branch-1',
            device_name: 'Cached Counter Desktop',
            device_code: 'counter-1',
            session_surface: 'store_desktop',
            status: 'ACTIVE',
            assigned_staff_profile_id: null,
            assigned_staff_full_name: null,
            last_seen_at: '2026-04-13T22:44:00',
          },
        ],
        selected_runtime_device_id: 'device-1',
        runtime_heartbeat: null,
        print_jobs: [],
        latest_print_job: null,
        latest_sale: null,
        latest_sale_return: null,
        latest_exchange: null,
        pending_mutations: [],
      }),
    );

    const responses = [
      jsonResponse({ access_token: 'session-cashier', token_type: 'Bearer' }),
      jsonResponse({
        user_id: 'user-cashier',
        email: 'cashier@acme.local',
        full_name: 'Counter Cashier',
        is_platform_admin: false,
        tenant_memberships: [],
        branch_memberships: [{ tenant_id: 'tenant-acme', branch_id: 'branch-1', role_name: 'cashier', status: 'ACTIVE' }],
      }),
      jsonResponse({
        id: 'tenant-acme',
        name: 'Acme Retail',
        slug: 'acme-retail',
        status: 'ACTIVE',
        onboarding_status: 'BRANCH_READY',
      }),
      jsonResponse({
        records: [{ branch_id: 'branch-1', tenant_id: 'tenant-acme', name: 'Bengaluru Flagship', code: 'blr-flagship', status: 'ACTIVE' }],
      }),
      jsonResponse({
        records: [
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
            base_selling_price: 92.5,
            selling_price_override: null,
            effective_selling_price: 92.5,
            availability_status: 'ACTIVE',
          },
        ],
      }),
      jsonResponse({
        records: [
          {
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            stock_on_hand: 24,
            last_entry_type: 'PURCHASE_RECEIPT',
          },
        ],
      }),
      jsonResponse({ records: [] }),
      jsonResponse({
        records: [
          {
            id: 'device-1',
            tenant_id: 'tenant-acme',
            branch_id: 'branch-1',
            device_name: 'Counter Desktop 1',
            device_code: 'counter-1',
            session_surface: 'store_desktop',
            status: 'ACTIVE',
            assigned_staff_profile_id: null,
            assigned_staff_full_name: null,
            last_seen_at: '2026-04-13T23:10:00',
          },
        ],
      }),
    ];

    globalThis.fetch = vi.fn(async () => {
      const next = responses.shift();
      if (!next) {
        throw new Error('Unexpected fetch call');
      }
      return next as never;
    }) as typeof fetch;
  });

  afterEach(() => {
    localStorage.clear();
    globalThis.fetch = originalFetch;
    Object.defineProperty(globalThis, 'localStorage', {
      configurable: true,
      value: originalLocalStorage,
    });
    vi.restoreAllMocks();
  });

  test('hydrates cached runtime posture before session bootstrap and rewrites it with live control-plane data', async () => {
    render(<App />);

    expect(await screen.findByText('Counter Cashier')).toBeInTheDocument();
    expect(await screen.findByText('Cached Flagship')).toBeInTheDocument();
    expect(await screen.findByText(/Cached Tea/)).toBeInTheDocument();
    expect(screen.getAllByText('Cached').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Control plane only').length).toBeGreaterThan(0);

    fireEvent.change(screen.getByLabelText('Korsenex token'), {
      target: { value: 'stub:sub=cashier-1;email=cashier@acme.local;name=Counter Cashier' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Start runtime session' }));

    expect(await screen.findByText('Bengaluru Flagship')).toBeInTheDocument();
    expect(screen.getByText(/Classic Tea/)).toBeInTheDocument();
    expect(screen.getAllByText('Live').length).toBeGreaterThan(0);

    await waitFor(() => {
      const cached = JSON.parse(localStorage.getItem(STORE_RUNTIME_CACHE_KEY) ?? '{}') as Record<string, unknown>;
      expect(cached.authority).toBe('CONTROL_PLANE_ONLY');
      expect(cached.pending_mutations).toEqual([]);
      expect(cached.access_token).toBeUndefined();
      expect((cached.inventory_snapshot as Array<Record<string, unknown>>)[0]?.stock_on_hand).toBe(24);
      expect((cached.runtime_devices as Array<Record<string, unknown>>)[0]?.device_name).toBe('Counter Desktop 1');
    });
  });
});
