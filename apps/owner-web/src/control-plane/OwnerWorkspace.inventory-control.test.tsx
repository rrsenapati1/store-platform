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

describe('owner inventory control flow', () => {
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
          { branch_id: 'branch-1', tenant_id: 'tenant-acme', name: 'Bengaluru Flagship', code: 'blr-flagship', status: 'ACTIVE' },
          { branch_id: 'branch-2', tenant_id: 'tenant-acme', name: 'Mysuru Hub', code: 'mysuru-hub', status: 'ACTIVE' },
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
            goods_receipt_id: 'goods-receipt-1',
            goods_receipt_number: 'GRN-BLRFLAGSHIP-0001',
            purchase_order_id: 'purchase-order-1',
            purchase_order_number: 'PO-BLRFLAGSHIP-0001',
            supplier_id: 'supplier-1',
            supplier_name: 'Acme Tea Traders',
            received_on: '2026-04-13',
            line_count: 1,
            received_quantity: 24,
          },
        ],
      }),
      jsonResponse({
        branch_id: 'branch-1',
        blocked_count: 0,
        ready_count: 0,
        received_count: 1,
        records: [
          {
            purchase_order_id: 'purchase-order-1',
            purchase_order_number: 'PO-BLRFLAGSHIP-0001',
            supplier_name: 'Acme Tea Traders',
            approval_status: 'APPROVED',
            receiving_status: 'RECEIVED',
            can_receive: false,
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
            quantity: 24,
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
            stock_on_hand: 24,
            last_entry_type: 'PURCHASE_RECEIPT',
          },
        ],
      }),
      jsonResponse({
        id: 'adjustment-1',
        tenant_id: 'tenant-acme',
        branch_id: 'branch-1',
        product_id: 'product-1',
        quantity_delta: -2,
        reason: 'Shelf damage',
        note: 'Shelf damage',
        resulting_stock_on_hand: 22,
      }),
      jsonResponse({
        records: [
          {
            inventory_ledger_entry_id: 'ledger-1',
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            entry_type: 'PURCHASE_RECEIPT',
            quantity: 24,
            reference_type: 'goods_receipt',
            reference_id: 'goods-receipt-1',
          },
          {
            inventory_ledger_entry_id: 'ledger-2',
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            entry_type: 'ADJUSTMENT',
            quantity: -2,
            reference_type: 'stock_adjustment',
            reference_id: 'adjustment-1',
          },
        ],
      }),
      jsonResponse({
        records: [
          {
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            stock_on_hand: 22,
            last_entry_type: 'ADJUSTMENT',
          },
        ],
      }),
      jsonResponse({
        id: 'count-session-1',
        tenant_id: 'tenant-acme',
        branch_id: 'branch-1',
        product_id: 'product-1',
        session_number: 'SCN-BLRFLAGSHIP-0001',
        status: 'OPEN',
        expected_quantity: null,
        counted_quantity: null,
        variance_quantity: null,
        note: 'Cycle count before transfer',
        review_note: null,
      }),
      jsonResponse({
        branch_id: 'branch-1',
        open_count: 1,
        counted_count: 0,
        approved_count: 0,
        canceled_count: 0,
        records: [
          {
            stock_count_session_id: 'count-session-1',
            session_number: 'SCN-BLRFLAGSHIP-0001',
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            status: 'OPEN',
            expected_quantity: null,
            counted_quantity: null,
            variance_quantity: null,
            note: 'Cycle count before transfer',
            review_note: null,
          },
        ],
      }),
      jsonResponse({
        id: 'count-session-1',
        tenant_id: 'tenant-acme',
        branch_id: 'branch-1',
        product_id: 'product-1',
        session_number: 'SCN-BLRFLAGSHIP-0001',
        status: 'COUNTED',
        expected_quantity: 22,
        counted_quantity: 20,
        variance_quantity: -2,
        note: 'Cycle count before transfer',
        review_note: null,
      }),
      jsonResponse({
        branch_id: 'branch-1',
        open_count: 0,
        counted_count: 1,
        approved_count: 0,
        canceled_count: 0,
        records: [
          {
            stock_count_session_id: 'count-session-1',
            session_number: 'SCN-BLRFLAGSHIP-0001',
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            status: 'COUNTED',
            expected_quantity: 22,
            counted_quantity: 20,
            variance_quantity: -2,
            note: 'Cycle count before transfer',
            review_note: null,
          },
        ],
      }),
      jsonResponse({
        session: {
          id: 'count-session-1',
          tenant_id: 'tenant-acme',
          branch_id: 'branch-1',
          product_id: 'product-1',
          session_number: 'SCN-BLRFLAGSHIP-0001',
          status: 'APPROVED',
          expected_quantity: 22,
          counted_quantity: 20,
          variance_quantity: -2,
          note: 'Cycle count before transfer',
          review_note: 'Approved after blind count review',
        },
        stock_count: {
          id: 'count-1',
          tenant_id: 'tenant-acme',
          branch_id: 'branch-1',
          product_id: 'product-1',
          counted_quantity: 20,
          expected_quantity: 22,
          variance_quantity: -2,
          note: 'Cycle count before transfer',
          closing_stock: 20,
        },
      }),
      jsonResponse({
        branch_id: 'branch-1',
        open_count: 0,
        counted_count: 0,
        approved_count: 1,
        canceled_count: 0,
        records: [
          {
            stock_count_session_id: 'count-session-1',
            session_number: 'SCN-BLRFLAGSHIP-0001',
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            status: 'APPROVED',
            expected_quantity: 22,
            counted_quantity: 20,
            variance_quantity: -2,
            note: 'Cycle count before transfer',
            review_note: 'Approved after blind count review',
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
            quantity: 24,
            reference_type: 'goods_receipt',
            reference_id: 'goods-receipt-1',
          },
          {
            inventory_ledger_entry_id: 'ledger-2',
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            entry_type: 'ADJUSTMENT',
            quantity: -2,
            reference_type: 'stock_adjustment',
            reference_id: 'adjustment-1',
          },
          {
            inventory_ledger_entry_id: 'ledger-3',
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            entry_type: 'COUNT_VARIANCE',
            quantity: -2,
            reference_type: 'stock_count',
            reference_id: 'count-1',
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
            last_entry_type: 'COUNT_VARIANCE',
          },
        ],
      }),
      jsonResponse({
        id: 'transfer-1',
        tenant_id: 'tenant-acme',
        source_branch_id: 'branch-1',
        destination_branch_id: 'branch-2',
        product_id: 'product-1',
        transfer_number: 'TRF-BLRFLAGSHIP-0001',
        quantity: 5,
        status: 'COMPLETED',
        note: 'Branch rebalance',
      }),
      jsonResponse({
        branch_id: 'branch-1',
        outbound_count: 1,
        inbound_count: 0,
        records: [
          {
            transfer_order_id: 'transfer-1',
            transfer_number: 'TRF-BLRFLAGSHIP-0001',
            direction: 'OUTBOUND',
            counterparty_branch_id: 'branch-2',
            counterparty_branch_name: 'Mysuru Hub',
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            quantity: 5,
            status: 'COMPLETED',
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
            quantity: 24,
            reference_type: 'goods_receipt',
            reference_id: 'goods-receipt-1',
          },
          {
            inventory_ledger_entry_id: 'ledger-2',
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            entry_type: 'ADJUSTMENT',
            quantity: -2,
            reference_type: 'stock_adjustment',
            reference_id: 'adjustment-1',
          },
          {
            inventory_ledger_entry_id: 'ledger-3',
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            entry_type: 'COUNT_VARIANCE',
            quantity: -2,
            reference_type: 'stock_count',
            reference_id: 'count-1',
          },
          {
            inventory_ledger_entry_id: 'ledger-4',
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            entry_type: 'TRANSFER_OUT',
            quantity: -5,
            reference_type: 'transfer_order',
            reference_id: 'transfer-1',
          },
        ],
      }),
      jsonResponse({
        records: [
          {
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            stock_on_hand: 15,
            last_entry_type: 'TRANSFER_OUT',
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

  test('posts adjustments, reviewed counts, and branch transfers after receipt', async () => {
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

    fireEvent.click(screen.getByRole('button', { name: 'Create goods receipt' }));
    await screen.findByText('Latest goods receipt');

    fireEvent.change(screen.getByLabelText('Adjustment delta'), { target: { value: '-2' } });
    fireEvent.change(screen.getByLabelText('Adjustment reason'), { target: { value: 'Shelf damage' } });
    fireEvent.click(screen.getByRole('button', { name: 'Post stock adjustment' }));

    await waitFor(() => {
      expect(screen.getByText('Latest stock adjustment')).toBeInTheDocument();
      expect(screen.getByText('22')).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText('Count note'), { target: { value: 'Cycle count before transfer' } });
    fireEvent.click(screen.getByRole('button', { name: 'Open stock count session' }));

    await waitFor(() => {
      expect(screen.getByText('Latest stock count session')).toBeInTheDocument();
      expect(screen.getByText('SCN-BLRFLAGSHIP-0001')).toBeInTheDocument();
      expect(screen.queryByText('Expected quantity')).not.toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText('Blind counted quantity'), { target: { value: '20' } });
    fireEvent.change(screen.getByLabelText('Count note'), { target: { value: 'Cycle count before transfer' } });
    fireEvent.click(screen.getByRole('button', { name: 'Record blind count' }));

    await waitFor(() => {
      expect(screen.getByText('Review stock count session')).toBeInTheDocument();
      expect(screen.getAllByText('-2').length).toBeGreaterThan(0);
    });

    fireEvent.click(screen.getByRole('button', { name: 'Approve stock count session' }));

    await waitFor(() => {
      expect(screen.getByText('Latest stock count')).toBeInTheDocument();
      expect(screen.getByText('Approved after blind count review')).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText('Transfer quantity'), { target: { value: '5' } });
    fireEvent.change(screen.getByLabelText('Destination branch'), { target: { value: 'branch-2' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create branch transfer' }));

    await waitFor(() => {
      expect(screen.getByText('Latest branch transfer')).toBeInTheDocument();
      expect(screen.getByText('TRF-BLRFLAGSHIP-0001')).toBeInTheDocument();
      expect(screen.getByText('Transfer board')).toBeInTheDocument();
      expect(screen.getByText('Classic Tea -> 15')).toBeInTheDocument();
    });
  });
});
