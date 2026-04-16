/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
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

describe('store runtime assisted restock flow', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
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
      }),
      jsonResponse({
        records: [
          {
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            stock_on_hand: 4,
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
          },
        ],
      }),
      jsonResponse({ records: [] }),
      jsonResponse({
        product_id: 'product-1',
        product_name: 'Classic Tea',
        sku_code: 'tea-classic-250g',
        barcode: 'ACMETEACLASSIC',
        selling_price: 89,
        stock_on_hand: 4,
        availability_status: 'ACTIVE',
      }),
      jsonResponse({
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
        picked_quantity: null,
        source_posture: 'BACKROOM_AVAILABLE',
        note: 'Shelf gap on aisle 2',
        completion_note: null,
      }),
      jsonResponse({
        branch_id: 'branch-1',
        open_count: 1,
        picked_count: 0,
        completed_count: 0,
        canceled_count: 0,
        records: [
          {
            restock_task_id: 'restock-task-1',
            task_number: 'RST-BLRFLAGSHIP-0001',
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            status: 'OPEN',
            stock_on_hand_snapshot: 4,
            reorder_point_snapshot: 10,
            target_stock_snapshot: 24,
            suggested_quantity_snapshot: 20,
            requested_quantity: 12,
            picked_quantity: null,
            source_posture: 'BACKROOM_AVAILABLE',
            note: 'Shelf gap on aisle 2',
            completion_note: null,
            has_active_task: true,
          },
        ],
      }),
      jsonResponse({
        id: 'restock-task-1',
        tenant_id: 'tenant-acme',
        branch_id: 'branch-1',
        product_id: 'product-1',
        task_number: 'RST-BLRFLAGSHIP-0001',
        status: 'PICKED',
        stock_on_hand_snapshot: 4,
        reorder_point_snapshot: 10,
        target_stock_snapshot: 24,
        suggested_quantity_snapshot: 20,
        requested_quantity: 12,
        picked_quantity: 10,
        source_posture: 'BACKROOM_AVAILABLE',
        note: 'Backroom rack B',
        completion_note: null,
      }),
      jsonResponse({
        branch_id: 'branch-1',
        open_count: 0,
        picked_count: 1,
        completed_count: 0,
        canceled_count: 0,
        records: [
          {
            restock_task_id: 'restock-task-1',
            task_number: 'RST-BLRFLAGSHIP-0001',
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            status: 'PICKED',
            stock_on_hand_snapshot: 4,
            reorder_point_snapshot: 10,
            target_stock_snapshot: 24,
            suggested_quantity_snapshot: 20,
            requested_quantity: 12,
            picked_quantity: 10,
            source_posture: 'BACKROOM_AVAILABLE',
            note: 'Backroom rack B',
            completion_note: null,
            has_active_task: true,
          },
        ],
      }),
      jsonResponse({
        id: 'restock-task-1',
        tenant_id: 'tenant-acme',
        branch_id: 'branch-1',
        product_id: 'product-1',
        task_number: 'RST-BLRFLAGSHIP-0001',
        status: 'COMPLETED',
        stock_on_hand_snapshot: 4,
        reorder_point_snapshot: 10,
        target_stock_snapshot: 24,
        suggested_quantity_snapshot: 20,
        requested_quantity: 12,
        picked_quantity: 10,
        source_posture: 'BACKROOM_AVAILABLE',
        note: 'Backroom rack B',
        completion_note: 'Shelf filled before rush hour',
      }),
      jsonResponse({
        branch_id: 'branch-1',
        open_count: 0,
        picked_count: 0,
        completed_count: 1,
        canceled_count: 0,
        records: [
          {
            restock_task_id: 'restock-task-1',
            task_number: 'RST-BLRFLAGSHIP-0001',
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            status: 'COMPLETED',
            stock_on_hand_snapshot: 4,
            reorder_point_snapshot: 10,
            target_stock_snapshot: 24,
            suggested_quantity_snapshot: 20,
            requested_quantity: 12,
            picked_quantity: 10,
            source_posture: 'BACKROOM_AVAILABLE',
            note: 'Backroom rack B',
            completion_note: 'Shelf filled before rush hour',
            has_active_task: false,
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
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  test('creates and completes a restock task for the latest scanned product', async () => {
    render(<App />);

    fireEvent.change(screen.getByLabelText('Korsenex token'), {
      target: { value: 'stub:sub=cashier-1;email=cashier@acme.local;name=Counter Cashier' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Start runtime session' }));

    expect(await screen.findByText('Counter Cashier')).toBeInTheDocument();

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
    fireEvent.click(screen.getByRole('button', { name: 'Create restock task for scanned product' }));

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
});
