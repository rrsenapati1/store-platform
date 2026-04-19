/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { App } from '../App';
import { clearRuntimeBrowserState } from './storeRuntimeTestHelpers';

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

describe('store runtime assisted restock flow', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    clearRuntimeBrowserState();
    let restockTask = {
      id: 'restock-task-1',
      tenant_id: 'tenant-acme',
      branch_id: 'branch-1',
      product_id: 'product-1',
      task_number: 'RST-BLRFLAGSHIP-0001',
      status: 'OPEN',
      stock_on_hand_snapshot: 4,
      reorder_point_snapshot: 10,
      target_stock_snapshot: 24,
      suggested_quantity_snapshot: 20,
      requested_quantity: 12,
      picked_quantity: null as number | null,
      source_posture: 'BACKROOM_AVAILABLE',
      note: 'Shelf gap on aisle 2',
      completion_note: null as string | null,
    };

    function buildRestockBoard() {
      return {
        branch_id: 'branch-1',
        open_count: restockTask.status === 'OPEN' ? 1 : 0,
        picked_count: restockTask.status === 'PICKED' ? 1 : 0,
        completed_count: restockTask.status === 'COMPLETED' ? 1 : 0,
        canceled_count: restockTask.status === 'CANCELED' ? 1 : 0,
        records: [
          {
            restock_task_id: restockTask.id,
            task_number: restockTask.task_number,
            product_id: restockTask.product_id,
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            status: restockTask.status,
            stock_on_hand_snapshot: restockTask.stock_on_hand_snapshot,
            reorder_point_snapshot: restockTask.reorder_point_snapshot,
            target_stock_snapshot: restockTask.target_stock_snapshot,
            suggested_quantity_snapshot: restockTask.suggested_quantity_snapshot,
            requested_quantity: restockTask.requested_quantity,
            picked_quantity: restockTask.picked_quantity,
            source_posture: restockTask.source_posture,
            note: restockTask.note,
            completion_note: restockTask.completion_note,
            has_active_task: restockTask.status === 'OPEN' || restockTask.status === 'PICKED',
          },
        ],
      };
    }

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
          branch_memberships: [{ tenant_id: 'tenant-acme', branch_id: 'branch-1', role_name: 'store_manager', status: 'ACTIVE' }],
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
        return jsonResponse({
          records: [
            {
              id: 'catalog-item-1',
              tenant_id: 'tenant-acme',
              branch_id: 'branch-1',
              product_id: 'product-1',
              product_name: 'Classic Tea',
              sku_code: 'tea-classic-250g',
              barcode: 'ACMETEACLASSIC',
              hsn_sac_code: '0902',
              gst_rate: 5,
              base_selling_price: 89,
              selling_price_override: null,
              effective_selling_price: 89,
              availability_status: 'ACTIVE',
              reorder_point: 10,
              target_stock: 24,
            },
          ],
        }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/inventory-snapshot') && method === 'GET') {
        return jsonResponse({
          records: [
            {
              product_id: 'product-1',
              product_name: 'Classic Tea',
              sku_code: 'tea-classic-250g',
              stock_on_hand: 4,
              last_entry_type: 'PURCHASE_RECEIPT',
            },
          ],
        }) as never;
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
          selling_price: 89,
          stock_on_hand: 4,
          availability_status: 'ACTIVE',
        }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/restock-board') && method === 'GET') {
        return jsonResponse(buildRestockBoard()) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/replenishment-board') && method === 'GET') {
        return jsonResponse({
          branch_id: 'branch-1',
          low_stock_count: 1,
          adequate_count: 0,
          records: [
            {
              product_id: 'product-1',
              product_name: 'Classic Tea',
              sku_code: 'tea-classic-250g',
              availability_status: 'ACTIVE',
              stock_on_hand: 4,
              reorder_point: 10,
              target_stock: 24,
              suggested_reorder_quantity: 20,
              replenishment_status: 'LOW_STOCK',
            },
          ],
        }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/restock-tasks') && method === 'POST') {
        const payload = JSON.parse(String(init?.body ?? '{}'));
        restockTask = {
          ...restockTask,
          status: 'OPEN',
          requested_quantity: payload.requested_quantity,
          source_posture: payload.source_posture,
          note: payload.note ?? null,
          picked_quantity: null,
          completion_note: null,
        };
        return jsonResponse(restockTask) as never;
      }
      if (url.includes('/restock-tasks/restock-task-1/pick') && method === 'POST') {
        const payload = JSON.parse(String(init?.body ?? '{}'));
        restockTask = {
          ...restockTask,
          status: 'PICKED',
          picked_quantity: payload.picked_quantity,
          note: payload.note ?? restockTask.note,
        };
        return jsonResponse(restockTask) as never;
      }
      if (url.includes('/restock-tasks/restock-task-1/complete') && method === 'POST') {
        const payload = JSON.parse(String(init?.body ?? '{}'));
        restockTask = {
          ...restockTask,
          status: 'COMPLETED',
          completion_note: payload.completion_note ?? null,
        };
        return jsonResponse(restockTask) as never;
      }

      throw new Error(`Unexpected fetch call: ${method} ${url}`);
    }) as typeof fetch;
  });

  afterEach(() => {
    clearRuntimeBrowserState();
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  test('creates and completes a restock task for the latest scanned product', async () => {
    render(<App />);

    fireEvent.change(screen.getByLabelText('Korsenex token'), {
      target: { value: 'stub:sub=cashier-1;email=cashier@acme.local;name=Counter Cashier' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Start runtime session' }));

    fireEvent.click(await screen.findByRole('button', { name: 'Operations' }));
    await screen.findByRole('button', { name: 'Refresh restock board' });

    fireEvent.change(screen.getByLabelText('Scanned barcode'), {
      target: { value: 'ACMETEACLASSIC' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Lookup scanned barcode' }));

    await screen.findByText('Latest scanned stock workflow');

    fireEvent.change(screen.getByLabelText('Restock requested quantity'), {
      target: { value: '12' },
    });
    fireEvent.change(screen.getByLabelText('Restock note'), {
      target: { value: 'Shelf gap on aisle 2' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Create restock task' }));

    await waitFor(() => {
      expect(screen.getByText('RST-BLRFLAGSHIP-0001')).toBeInTheDocument();
      expect(screen.getByText(/RST-BLRFLAGSHIP-0001 :: Classic Tea :: OPEN :: requested 12 :: picked 0/i)).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText('Restock picked quantity'), {
      target: { value: '10' },
    });
    fireEvent.change(screen.getByLabelText('Restock note'), {
      target: { value: 'Backroom rack B' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Mark active task picked' }));

    await waitFor(() => {
      expect(screen.getByText(/RST-BLRFLAGSHIP-0001 :: Classic Tea :: PICKED :: requested 12 :: picked 10/i)).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText('Restock completion note'), {
      target: { value: 'Shelf filled before rush hour' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Complete active task' }));

    await waitFor(() => {
      expect(screen.getByText('Completed tasks -> 1')).toBeInTheDocument();
      expect(screen.getByText(/RST-BLRFLAGSHIP-0001 :: Classic Tea :: COMPLETED :: requested 12 :: picked 10 :: Shelf filled before rush hour/i)).toBeInTheDocument();
    });
  });

  test('creates a restock task from the replenishment board without scanning first', async () => {
    render(<App />);

    fireEvent.change(screen.getByLabelText('Korsenex token'), {
      target: { value: 'stub:sub=cashier-1;email=cashier@acme.local;name=Counter Cashier' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Start runtime session' }));

    expect(await screen.findByText('Counter Cashier')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Operations' }));
    await screen.findByRole('button', { name: 'Refresh restock board' });

    fireEvent.click(screen.getByRole('button', { name: 'Refresh restock board' }));

    await screen.findByText(/Low-stock items -> 1/i);

    fireEvent.click(screen.getByRole('button', { name: 'Use Classic Tea' }));
    fireEvent.change(screen.getByLabelText('Restock note'), {
      target: { value: 'Suggested from replenishment board' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Create restock task' }));

    await waitFor(() => {
      expect(screen.getByText('Active restock task -> RST-BLRFLAGSHIP-0001')).toBeInTheDocument();
      expect(screen.getByText(/RST-BLRFLAGSHIP-0001 :: Classic Tea :: OPEN :: requested 20 :: picked 0/i)).toBeInTheDocument();
    });
  });
});
