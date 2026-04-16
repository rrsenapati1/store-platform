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

describe('owner receiving foundation flow', () => {
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
            selling_price: 92.5,
            status: 'ACTIVE',
          },
        ],
      }),
      jsonResponse({ records: [] }),
      jsonResponse({ records: [] }),
      jsonResponse({ records: [] }),
      jsonResponse({
        id: 'supplier-1',
        tenant_id: 'tenant-acme',
        name: 'Acme Tea Traders',
        gstin: '29AAEPM0111C1Z3',
        payment_terms_days: 14,
        status: 'ACTIVE',
      }),
      jsonResponse({
        records: [
          {
            supplier_id: 'supplier-1',
            tenant_id: 'tenant-acme',
            name: 'Acme Tea Traders',
            gstin: '29AAEPM0111C1Z3',
            payment_terms_days: 14,
            status: 'ACTIVE',
          },
        ],
      }),
      jsonResponse({
        id: 'purchase-order-1',
        tenant_id: 'tenant-acme',
        branch_id: 'branch-1',
        supplier_id: 'supplier-1',
        purchase_order_number: 'PO-BLRFLAGSHIP-0001',
        approval_status: 'NOT_REQUESTED',
        subtotal: 1476,
        tax_total: 73.8,
        grand_total: 1549.8,
        lines: [
          {
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            quantity: 24,
            unit_cost: 61.5,
            line_total: 1476,
          },
        ],
      }),
      jsonResponse({
        records: [
          {
            purchase_order_id: 'purchase-order-1',
            purchase_order_number: 'PO-BLRFLAGSHIP-0001',
            supplier_id: 'supplier-1',
            supplier_name: 'Acme Tea Traders',
            approval_status: 'NOT_REQUESTED',
            line_count: 1,
            ordered_quantity: 24,
            grand_total: 1549.8,
          },
        ],
      }),
      jsonResponse({
        branch_id: 'branch-1',
        not_requested_count: 1,
        pending_approval_count: 0,
        approved_count: 0,
        rejected_count: 0,
        records: [
          {
            purchase_order_id: 'purchase-order-1',
            purchase_order_number: 'PO-BLRFLAGSHIP-0001',
            supplier_name: 'Acme Tea Traders',
            approval_status: 'NOT_REQUESTED',
            line_count: 1,
            ordered_quantity: 24,
            grand_total: 1549.8,
            approval_requested_note: null,
            approval_decision_note: null,
          },
        ],
      }),
      jsonResponse({
        id: 'purchase-order-1',
        tenant_id: 'tenant-acme',
        branch_id: 'branch-1',
        supplier_id: 'supplier-1',
        purchase_order_number: 'PO-BLRFLAGSHIP-0001',
        approval_status: 'PENDING_APPROVAL',
        subtotal: 1476,
        tax_total: 73.8,
        grand_total: 1549.8,
        lines: [
          {
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            quantity: 24,
            unit_cost: 61.5,
            line_total: 1476,
          },
        ],
      }),
      jsonResponse({
        records: [
          {
            purchase_order_id: 'purchase-order-1',
            purchase_order_number: 'PO-BLRFLAGSHIP-0001',
            supplier_id: 'supplier-1',
            supplier_name: 'Acme Tea Traders',
            approval_status: 'PENDING_APPROVAL',
            line_count: 1,
            ordered_quantity: 24,
            grand_total: 1549.8,
            approval_requested_note: 'Need replenishment before the weekend rush',
            approval_decision_note: null,
          },
        ],
      }),
      jsonResponse({
        branch_id: 'branch-1',
        not_requested_count: 0,
        pending_approval_count: 1,
        approved_count: 0,
        rejected_count: 0,
        records: [
          {
            purchase_order_id: 'purchase-order-1',
            purchase_order_number: 'PO-BLRFLAGSHIP-0001',
            supplier_name: 'Acme Tea Traders',
            approval_status: 'PENDING_APPROVAL',
            line_count: 1,
            ordered_quantity: 24,
            grand_total: 1549.8,
            approval_requested_note: 'Need replenishment before the weekend rush',
            approval_decision_note: null,
          },
        ],
      }),
      jsonResponse({
        id: 'purchase-order-1',
        tenant_id: 'tenant-acme',
        branch_id: 'branch-1',
        supplier_id: 'supplier-1',
        purchase_order_number: 'PO-BLRFLAGSHIP-0001',
        approval_status: 'APPROVED',
        subtotal: 1476,
        tax_total: 73.8,
        grand_total: 1549.8,
        lines: [
          {
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            quantity: 24,
            unit_cost: 61.5,
            line_total: 1476,
          },
        ],
      }),
      jsonResponse({
        records: [
          {
            purchase_order_id: 'purchase-order-1',
            purchase_order_number: 'PO-BLRFLAGSHIP-0001',
            supplier_id: 'supplier-1',
            supplier_name: 'Acme Tea Traders',
            approval_status: 'APPROVED',
            line_count: 1,
            ordered_quantity: 24,
            grand_total: 1549.8,
            approval_requested_note: 'Need replenishment before the weekend rush',
            approval_decision_note: 'Approved for branch restock',
          },
        ],
      }),
      jsonResponse({
        branch_id: 'branch-1',
        not_requested_count: 0,
        pending_approval_count: 0,
        approved_count: 1,
        rejected_count: 0,
        records: [
          {
            purchase_order_id: 'purchase-order-1',
            purchase_order_number: 'PO-BLRFLAGSHIP-0001',
            supplier_name: 'Acme Tea Traders',
            approval_status: 'APPROVED',
            line_count: 1,
            ordered_quantity: 24,
            grand_total: 1549.8,
            approval_requested_note: 'Need replenishment before the weekend rush',
            approval_decision_note: 'Approved for branch restock',
          },
        ],
      }),
      jsonResponse({
        id: 'goods-receipt-1',
        tenant_id: 'tenant-acme',
        branch_id: 'branch-1',
        purchase_order_id: 'purchase-order-1',
        supplier_id: 'supplier-1',
        goods_receipt_number: 'GRN-BLRFLAGSHIP-0001',
        received_on: '2026-04-13',
        note: 'Four cartons short from supplier dispatch',
        ordered_quantity_total: 24,
        received_quantity_total: 20,
        variance_quantity_total: 4,
        has_discrepancy: true,
        lines: [
          {
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            ordered_quantity: 24,
            quantity: 20,
            variance_quantity: 4,
            unit_cost: 61.5,
            line_total: 1230,
            discrepancy_note: 'Four cartons short from supplier dispatch',
          },
        ],
      }),
      jsonResponse({
        records: [
          {
            goods_receipt_id: 'goods-receipt-1',
            goods_receipt_number: 'GRN-BLRFLAGSHIP-0001',
            purchase_order_id: 'purchase-order-1',
            purchase_order_number: 'PO-BLRFLAGSHIP-0001',
            supplier_id: 'supplier-1',
            supplier_name: 'Acme Tea Traders',
            received_on: '2026-04-13',
            line_count: 1,
            received_quantity: 20,
            ordered_quantity: 24,
            variance_quantity: 4,
            has_discrepancy: true,
            note: 'Four cartons short from supplier dispatch',
          },
        ],
      }),
      jsonResponse({
        branch_id: 'branch-1',
        blocked_count: 0,
        ready_count: 0,
        received_count: 1,
        received_with_variance_count: 1,
        records: [
          {
            purchase_order_id: 'purchase-order-1',
            purchase_order_number: 'PO-BLRFLAGSHIP-0001',
            supplier_name: 'Acme Tea Traders',
            approval_status: 'APPROVED',
            receiving_status: 'RECEIVED_WITH_VARIANCE',
            can_receive: false,
            has_discrepancy: true,
            variance_quantity: 4,
            blocked_reason: null,
            goods_receipt_id: 'goods-receipt-1',
          },
        ],
      }),
      jsonResponse({
        records: [
          {
            inventory_ledger_entry_id: 'ledger-1',
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            entry_type: 'PURCHASE_RECEIPT',
            quantity: 20,
            reference_type: 'goods_receipt',
            reference_id: 'goods-receipt-1',
          },
        ],
      }),
      jsonResponse({
        records: [
          {
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            stock_on_hand: 20,
            last_entry_type: 'PURCHASE_RECEIPT',
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

  test('posts a reviewed partial goods receipt and updates discrepancy visibility', async () => {
    render(<App />);

    fireEvent.change(screen.getByLabelText('Korsenex token'), {
      target: { value: 'stub:sub=owner-1;email=owner@acme.local;name=Acme Owner' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Start owner session' }));

    expect(await screen.findByText('Acme Owner')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Supplier name'), { target: { value: 'Acme Tea Traders' } });
    fireEvent.change(screen.getByLabelText('Supplier GSTIN'), { target: { value: '29AAEPM0111C1Z3' } });
    fireEvent.change(screen.getByLabelText('Payment terms (days)'), { target: { value: '14' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create supplier' }));
    await screen.findByText('Latest supplier');

    fireEvent.change(screen.getByLabelText('Purchase quantity'), { target: { value: '24' } });
    fireEvent.change(screen.getByLabelText('Unit cost'), { target: { value: '61.5' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create purchase order' }));
    await screen.findByText('Latest purchase order');

    fireEvent.change(screen.getByLabelText('Approval note'), {
      target: { value: 'Need replenishment before the weekend rush' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Submit approval' }));
    await screen.findByText('Latest approval state');

    fireEvent.change(screen.getByLabelText('Decision note'), {
      target: { value: 'Approved for branch restock' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Approve purchase order' }));
    await waitFor(() => {
      expect(screen.getByText('Acme Tea Traders :: APPROVED')).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText('Received quantity for Classic Tea'), {
      target: { value: '20' },
    });
    fireEvent.change(screen.getByLabelText('Discrepancy note for Classic Tea'), {
      target: { value: 'Four cartons short from supplier dispatch' },
    });
    fireEvent.change(screen.getByLabelText('Receipt note'), {
      target: { value: 'Four cartons short from supplier dispatch' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Create goods receipt' }));

    await waitFor(() => {
      expect(screen.getByText('Latest goods receipt')).toBeInTheDocument();
      expect(screen.getByText('GRN-BLRFLAGSHIP-0001')).toBeInTheDocument();
      expect(screen.getByText('Receiving board')).toBeInTheDocument();
      expect(screen.getByText('Classic Tea -> 20')).toBeInTheDocument();
      expect(screen.getAllByText('RECEIVED_WITH_VARIANCE').length).toBeGreaterThan(0);
      expect(screen.getAllByText(/variance 4/i).length).toBeGreaterThan(0);
    });
  });
});
