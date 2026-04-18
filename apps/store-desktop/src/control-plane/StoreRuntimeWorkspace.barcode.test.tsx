/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { App } from '../App';

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

describe('store runtime barcode lookup flow', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    globalThis.fetch = vi.fn(async (input, init) => {
      const url = String(input);
      const method = init?.method ?? 'GET';

      if (url.endsWith('/v1/auth/oidc/exchange') && method === 'POST') {
        return jsonResponse({ access_token: 'session-cashier', token_type: 'Bearer' }) as never;
      }
      if (url.endsWith('/v1/auth/me') && method === 'GET') {
        return jsonResponse({
          user_id: 'user-cashier',
          email: 'cashier@acme.local',
          full_name: 'Counter Cashier',
          is_platform_admin: false,
          tenant_memberships: [],
          branch_memberships: [{ tenant_id: 'tenant-acme', branch_id: 'branch-1', role_name: 'cashier', status: 'ACTIVE' }],
        }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme') && method === 'GET') {
        return jsonResponse({
          id: 'tenant-acme',
          name: 'Acme Retail',
          slug: 'acme-retail',
          status: 'ACTIVE',
          onboarding_status: 'BRANCH_READY',
        }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches') && method === 'GET') {
        return jsonResponse({
          records: [{ branch_id: 'branch-1', tenant_id: 'tenant-acme', name: 'Bengaluru Flagship', code: 'blr-flagship', status: 'ACTIVE' }],
        }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/catalog-items') && method === 'GET') {
        return jsonResponse({ records: [] }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/inventory-snapshot') && method === 'GET') {
        return jsonResponse({ records: [] }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/sales') && method === 'GET') {
        return jsonResponse({ records: [] }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/runtime/devices') && method === 'GET') {
        return jsonResponse({
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
            },
          ],
        }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/runtime/sync-conflicts') && method === 'GET') {
        return jsonResponse({ records: [] }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/runtime/sync-spokes') && method === 'GET') {
        return jsonResponse({ records: [] }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/runtime-policy') && method === 'GET') {
        return jsonResponse({
          id: 'runtime-policy-1',
          tenant_id: 'tenant-acme',
          branch_id: 'branch-1',
          require_shift_for_attendance: false,
          require_attendance_for_cashier: true,
          require_assigned_staff_for_device: true,
          allow_offline_sales: true,
          max_pending_offline_sales: 25,
          updated_by_user_id: 'owner-user-1',
        }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/shift-sessions') && method === 'GET') {
        return jsonResponse({ records: [] }) as never;
      }
      if (url.includes('/attendance-sessions') && method === 'GET') {
        return jsonResponse({ records: [] }) as never;
      }
      if (url.includes('/cashier-sessions') && method === 'GET') {
        return jsonResponse({ records: [] }) as never;
      }
      if (url.endsWith('/catalog-scan/ACMETEACLASSIC') && method === 'GET') {
        return jsonResponse({
          product_id: 'product-1',
          product_name: 'Classic Tea',
          sku_code: 'tea-classic-250g',
          barcode: 'ACMETEACLASSIC',
          mrp: 120,
          selling_price: 89,
          stock_on_hand: 24,
          availability_status: 'ACTIVE',
          automatic_discount_hint: {
            campaign_id: 'campaign-auto-1',
            campaign_name: 'Tea Auto',
            discount_type: 'PERCENTAGE',
            discount_value: 10,
            scope: 'ITEM_CATEGORY',
          },
        }) as never;
      }

      throw new Error(`Unexpected fetch call: ${method} ${url}`);
    }) as typeof fetch;
  });

  afterEach(() => {
    cleanup();
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  test('looks up a scanned barcode against the live branch catalog', async () => {
    render(<App />);

    fireEvent.change(screen.getByLabelText('Korsenex token'), {
      target: { value: 'stub:sub=cashier-1;email=cashier@acme.local;name=Counter Cashier' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Start runtime session' }));

    expect(await screen.findByText('Counter Cashier')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Scanned barcode'), {
      target: { value: '  ACMETEACLASSIC  ' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Lookup scanned barcode' }));

    await waitFor(() => {
      expect(screen.getByText('Latest scan lookup')).toBeInTheDocument();
      expect(screen.getAllByText('Classic Tea').length).toBeGreaterThan(0);
      expect(screen.getByText('120')).toBeInTheDocument();
      expect(screen.getAllByText('24').length).toBeGreaterThan(0);
      expect(screen.getByText('Tea Auto :: PERCENTAGE 10')).toBeInTheDocument();
    });
  });
});
