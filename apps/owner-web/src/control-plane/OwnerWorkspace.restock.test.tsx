/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
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

describe('owner restock workflow', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    const responses = [
      jsonResponse({ access_token: 'session-owner', token_type: 'Bearer' }),
      jsonResponse({
        user_id: 'user-owner',
        email: 'owner@acme.local',
        full_name: 'Acme Owner',
        is_platform_admin: false,
        tenant_memberships: [{ tenant_id: 'tenant-acme', role_name: 'tenant_owner', status: 'ACTIVE' }],
        branch_memberships: [],
      }),
      jsonResponse({
        id: 'tenant-acme',
        name: 'Acme Retail',
        slug: 'acme-retail',
        status: 'ACTIVE',
        onboarding_status: 'BRANCH_READY',
      }),
      jsonResponse({
        records: [
          {
            branch_id: 'branch-1',
            tenant_id: 'tenant-acme',
            name: 'Bengaluru Flagship',
            code: 'blr-flagship',
            status: 'ACTIVE',
          },
        ],
      }),
      jsonResponse({
        records: [
          {
            id: 'audit-1',
            action: 'branch.created',
            entity_type: 'branch',
            entity_id: 'branch-1',
            tenant_id: 'tenant-acme',
            branch_id: 'branch-1',
            created_at: '2026-04-13T08:00:00',
            payload: { name: 'Bengaluru Flagship' },
          },
        ],
      }),
      jsonResponse({ records: [] }),
      jsonResponse({ records: [] }),
      jsonResponse({ records: [] }),
      jsonResponse({ records: [] }),
      jsonResponse({ records: [] }),
      jsonResponse({
        id: 'product-1',
        tenant_id: 'tenant-acme',
        name: 'Classic Tea',
        sku_code: 'tea-classic-250g',
        barcode: '8901234567890',
        hsn_sac_code: '0902',
        gst_rate: 5,
        mrp: 120,
        category_code: 'TEA',
        selling_price: 92.5,
        status: 'ACTIVE',
      }),
      jsonResponse({
        records: [
          {
            product_id: 'product-1',
            tenant_id: 'tenant-acme',
            name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            barcode: '8901234567890',
            hsn_sac_code: '0902',
            gst_rate: 5,
            mrp: 120,
            category_code: 'TEA',
            selling_price: 92.5,
            status: 'ACTIVE',
          },
        ],
      }),
      jsonResponse({
        id: 'branch-catalog-1',
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
        selling_price_override: 89,
        effective_selling_price: 89,
        availability_status: 'ACTIVE',
        reorder_point: null,
        target_stock: null,
      }),
      jsonResponse({
        records: [
          {
            id: 'branch-catalog-1',
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
            selling_price_override: 89,
            effective_selling_price: 89,
            availability_status: 'ACTIVE',
            reorder_point: null,
            target_stock: null,
          },
        ],
      }),
      jsonResponse({
        id: 'branch-catalog-1',
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
        selling_price_override: 89,
        effective_selling_price: 89,
        availability_status: 'ACTIVE',
        reorder_point: 10,
        target_stock: 24,
      }),
      jsonResponse({
        branch_id: 'branch-1',
        low_stock_count: 1,
        adequate_count: 0,
        records: [
          {
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            availability_status: 'ACTIVE',
            stock_on_hand: 8,
            reorder_point: 10,
            target_stock: 24,
            suggested_reorder_quantity: 16,
            replenishment_status: 'LOW_STOCK',
          },
        ],
      }),
      jsonResponse({
        id: 'restock-task-1',
        tenant_id: 'tenant-acme',
        branch_id: 'branch-1',
        product_id: 'product-1',
        task_number: 'RST-BLRFLAGSHIP-0001',
        status: 'OPEN',
        stock_on_hand_snapshot: 8,
        reorder_point_snapshot: 10,
        target_stock_snapshot: 24,
        suggested_quantity_snapshot: 16,
        requested_quantity: 12,
        picked_quantity: null,
        source_posture: 'BACKROOM_AVAILABLE',
        note: 'Front shelf refill',
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
            stock_on_hand_snapshot: 8,
            reorder_point_snapshot: 10,
            target_stock_snapshot: 24,
            suggested_quantity_snapshot: 16,
            requested_quantity: 12,
            picked_quantity: null,
            source_posture: 'BACKROOM_AVAILABLE',
            note: 'Front shelf refill',
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
        stock_on_hand_snapshot: 8,
        reorder_point_snapshot: 10,
        target_stock_snapshot: 24,
        suggested_quantity_snapshot: 16,
        requested_quantity: 12,
        picked_quantity: 10,
        source_posture: 'BACKROOM_AVAILABLE',
        note: 'Front shelf refill',
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
            stock_on_hand_snapshot: 8,
            reorder_point_snapshot: 10,
            target_stock_snapshot: 24,
            suggested_quantity_snapshot: 16,
            requested_quantity: 12,
            picked_quantity: 10,
            source_posture: 'BACKROOM_AVAILABLE',
            note: 'Front shelf refill',
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
        stock_on_hand_snapshot: 8,
        reorder_point_snapshot: 10,
        target_stock_snapshot: 24,
        suggested_quantity_snapshot: 16,
        requested_quantity: 12,
        picked_quantity: 10,
        source_posture: 'BACKROOM_AVAILABLE',
        note: 'Front shelf refill',
        completion_note: 'Shelf refill done',
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
            stock_on_hand_snapshot: 8,
            reorder_point_snapshot: 10,
            target_stock_snapshot: 24,
            suggested_quantity_snapshot: 16,
            requested_quantity: 12,
            picked_quantity: 10,
            source_posture: 'BACKROOM_AVAILABLE',
            note: 'Front shelf refill',
            completion_note: 'Shelf refill done',
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

  test('creates, picks, and completes a branch restock task from the low-stock board', async () => {
    render(<App />);

    fireEvent.change(screen.getByLabelText('Korsenex token'), {
      target: { value: 'stub:sub=owner-1;email=owner@acme.local;name=Acme Owner' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Start owner session' }));

    expect(await screen.findByText('Acme Owner')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Product name'), { target: { value: 'Classic Tea' } });
    fireEvent.change(screen.getByLabelText('SKU code'), { target: { value: 'tea-classic-250g' } });
    fireEvent.change(screen.getByLabelText('Barcode'), { target: { value: '8901234567890' } });
    fireEvent.change(screen.getByLabelText('HSN or SAC code'), { target: { value: '0902' } });
    fireEvent.change(screen.getByLabelText('GST rate'), { target: { value: '5' } });
    fireEvent.change(screen.getByLabelText('MRP'), { target: { value: '120' } });
    fireEvent.change(screen.getByLabelText('Category code'), { target: { value: 'TEA' } });
    fireEvent.change(screen.getByLabelText('Selling price'), { target: { value: '92.5' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create catalog product' }));

    await screen.findByText('Latest catalog product');

    fireEvent.change(screen.getByLabelText('Branch selling price override'), { target: { value: '89' } });
    fireEvent.click(screen.getByRole('button', { name: 'Assign first product to branch' }));

    await screen.findByText('Latest branch catalog item');

    fireEvent.change(screen.getByLabelText('Reorder point'), { target: { value: '10' } });
    fireEvent.change(screen.getByLabelText('Target stock'), { target: { value: '24' } });
    fireEvent.click(screen.getByRole('button', { name: 'Set replenishment policy for first branch item' }));

    await screen.findByText('Latest replenishment policy');

    fireEvent.change(screen.getByLabelText('Requested quantity'), { target: { value: '12' } });
    fireEvent.change(screen.getByLabelText('Restock note'), { target: { value: 'Front shelf refill' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create restock task' }));

    await waitFor(() => {
      expect(screen.getByText('Latest restock task')).toBeInTheDocument();
      expect(screen.getByText('RST-BLRFLAGSHIP-0001')).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText('Picked quantity'), { target: { value: '10' } });
    fireEvent.click(screen.getByRole('button', { name: 'Mark task picked' }));

    await waitFor(() => {
      expect(screen.getByText('PICKED')).toBeInTheDocument();
      expect(screen.getAllByText('10').length).toBeGreaterThan(0);
    });

    fireEvent.change(screen.getByLabelText('Completion note'), { target: { value: 'Shelf refill done' } });
    fireEvent.click(screen.getByRole('button', { name: 'Complete restock task' }));

    await waitFor(() => {
      expect(screen.getByText('Shelf refill done')).toBeInTheDocument();
    });

    const restockBoardSection = screen.getByRole('heading', { name: 'Restock board' }).closest('section');
    expect(restockBoardSection).not.toBeNull();
    expect(within(restockBoardSection as HTMLElement).getByRole('listitem')).toHaveTextContent(
      'Classic Tea :: COMPLETED :: requested 12 :: picked 10',
    );
  });
});
