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

describe('owner procurement finance flow', () => {
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
            name: 'Notebook',
            sku_code: 'SKU-001',
            barcode: '8901234567890',
            hsn_sac_code: '4820',
            gst_rate: 18,
            selling_price: 100,
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
        name: 'Paper Supply Co',
        gstin: '29AAAAA1111A1Z5',
        payment_terms_days: 14,
        status: 'ACTIVE',
      }),
      jsonResponse({
        records: [
          {
            supplier_id: 'supplier-1',
            tenant_id: 'tenant-acme',
            name: 'Paper Supply Co',
            gstin: '29AAAAA1111A1Z5',
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
        subtotal: 300,
        tax_total: 54,
        grand_total: 354,
        lines: [
          {
            product_id: 'product-1',
            product_name: 'Notebook',
            sku_code: 'SKU-001',
            quantity: 6,
            unit_cost: 50,
            line_total: 300,
          },
        ],
      }),
      jsonResponse({
        records: [
          {
            purchase_order_id: 'purchase-order-1',
            purchase_order_number: 'PO-BLRFLAGSHIP-0001',
            supplier_id: 'supplier-1',
            supplier_name: 'Paper Supply Co',
            approval_status: 'NOT_REQUESTED',
            line_count: 1,
            ordered_quantity: 6,
            grand_total: 354,
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
            supplier_name: 'Paper Supply Co',
            approval_status: 'NOT_REQUESTED',
            line_count: 1,
            ordered_quantity: 6,
            grand_total: 354,
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
        subtotal: 300,
        tax_total: 54,
        grand_total: 354,
        lines: [
          {
            product_id: 'product-1',
            product_name: 'Notebook',
            sku_code: 'SKU-001',
            quantity: 6,
            unit_cost: 50,
            line_total: 300,
          },
        ],
      }),
      jsonResponse({
        records: [
          {
            purchase_order_id: 'purchase-order-1',
            purchase_order_number: 'PO-BLRFLAGSHIP-0001',
            supplier_id: 'supplier-1',
            supplier_name: 'Paper Supply Co',
            approval_status: 'PENDING_APPROVAL',
            line_count: 1,
            ordered_quantity: 6,
            grand_total: 354,
            approval_requested_note: 'Ready for supplier settlement',
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
            supplier_name: 'Paper Supply Co',
            approval_status: 'PENDING_APPROVAL',
            line_count: 1,
            ordered_quantity: 6,
            grand_total: 354,
            approval_requested_note: 'Ready for supplier settlement',
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
        subtotal: 300,
        tax_total: 54,
        grand_total: 354,
        lines: [
          {
            product_id: 'product-1',
            product_name: 'Notebook',
            sku_code: 'SKU-001',
            quantity: 6,
            unit_cost: 50,
            line_total: 300,
          },
        ],
      }),
      jsonResponse({
        records: [
          {
            purchase_order_id: 'purchase-order-1',
            purchase_order_number: 'PO-BLRFLAGSHIP-0001',
            supplier_id: 'supplier-1',
            supplier_name: 'Paper Supply Co',
            approval_status: 'APPROVED',
            line_count: 1,
            ordered_quantity: 6,
            grand_total: 354,
            approval_requested_note: 'Ready for supplier settlement',
            approval_decision_note: 'Approved for supplier settlement',
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
            supplier_name: 'Paper Supply Co',
            approval_status: 'APPROVED',
            line_count: 1,
            ordered_quantity: 6,
            grand_total: 354,
            approval_requested_note: 'Ready for supplier settlement',
            approval_decision_note: 'Approved for supplier settlement',
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
            product_name: 'Notebook',
            sku_code: 'SKU-001',
            quantity: 6,
            unit_cost: 50,
            line_total: 300,
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
            supplier_name: 'Paper Supply Co',
            received_on: '2026-04-13',
            line_count: 1,
            received_quantity: 6,
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
            supplier_name: 'Paper Supply Co',
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
            product_name: 'Notebook',
            sku_code: 'SKU-001',
            entry_type: 'PURCHASE_RECEIPT',
            quantity: 6,
            reference_type: 'goods_receipt',
            reference_id: 'goods-receipt-1',
          },
        ],
      }),
      jsonResponse({
        records: [
          {
            product_id: 'product-1',
            product_name: 'Notebook',
            sku_code: 'SKU-001',
            stock_on_hand: 6,
            last_entry_type: 'PURCHASE_RECEIPT',
          },
        ],
      }),
      jsonResponse({
        id: 'purchase-invoice-1',
        tenant_id: 'tenant-acme',
        branch_id: 'branch-1',
        supplier_id: 'supplier-1',
        goods_receipt_id: 'goods-receipt-1',
        invoice_number: 'SPINV-2627-000001',
        invoice_date: '2026-04-14',
        due_date: '2026-04-28',
        payment_terms_days: 14,
        subtotal: 300,
        cgst_total: 27,
        sgst_total: 27,
        igst_total: 0,
        grand_total: 354,
        lines: [
          {
            product_id: 'product-1',
            product_name: 'Notebook',
            sku_code: 'SKU-001',
            quantity: 6,
            unit_cost: 50,
            gst_rate: 18,
            line_subtotal: 300,
            tax_total: 54,
            line_total: 354,
          },
        ],
      }),
      jsonResponse({
        records: [
          {
            purchase_invoice_id: 'purchase-invoice-1',
            purchase_invoice_number: 'SPINV-2627-000001',
            supplier_id: 'supplier-1',
            supplier_name: 'Paper Supply Co',
            goods_receipt_id: 'goods-receipt-1',
            goods_receipt_number: 'GRN-BLRFLAGSHIP-0001',
            invoice_date: '2026-04-14',
            due_date: '2026-04-28',
            grand_total: 354,
          },
        ],
      }),
      jsonResponse({
        branch_id: 'branch-1',
        invoiced_total: 354,
        credit_note_total: 0,
        paid_total: 0,
        outstanding_total: 354,
        records: [
          {
            purchase_invoice_id: 'purchase-invoice-1',
            purchase_invoice_number: 'SPINV-2627-000001',
            supplier_name: 'Paper Supply Co',
            grand_total: 354,
            credit_note_total: 0,
            paid_total: 0,
            outstanding_total: 354,
            settlement_status: 'UNPAID',
          },
        ],
      }),
      jsonResponse({
        id: 'supplier-return-1',
        tenant_id: 'tenant-acme',
        branch_id: 'branch-1',
        supplier_id: 'supplier-1',
        purchase_invoice_id: 'purchase-invoice-1',
        supplier_credit_note_number: 'SRCN-2627-000001',
        issued_on: '2026-04-14',
        subtotal: 50,
        cgst_total: 4.5,
        sgst_total: 4.5,
        igst_total: 0,
        grand_total: 59,
        lines: [
          {
            product_id: 'product-1',
            product_name: 'Notebook',
            sku_code: 'SKU-001',
            quantity: 1,
            unit_cost: 50,
            gst_rate: 18,
            line_subtotal: 50,
            tax_total: 9,
            line_total: 59,
          },
        ],
      }),
      jsonResponse({
        branch_id: 'branch-1',
        invoiced_total: 354,
        credit_note_total: 59,
        paid_total: 0,
        outstanding_total: 295,
        records: [
          {
            purchase_invoice_id: 'purchase-invoice-1',
            purchase_invoice_number: 'SPINV-2627-000001',
            supplier_name: 'Paper Supply Co',
            grand_total: 354,
            credit_note_total: 59,
            paid_total: 0,
            outstanding_total: 295,
            settlement_status: 'PARTIALLY_SETTLED',
          },
        ],
      }),
      jsonResponse({
        records: [
          {
            inventory_ledger_entry_id: 'ledger-1',
            product_id: 'product-1',
            product_name: 'Notebook',
            sku_code: 'SKU-001',
            entry_type: 'PURCHASE_RECEIPT',
            quantity: 6,
            reference_type: 'goods_receipt',
            reference_id: 'goods-receipt-1',
          },
          {
            inventory_ledger_entry_id: 'ledger-2',
            product_id: 'product-1',
            product_name: 'Notebook',
            sku_code: 'SKU-001',
            entry_type: 'SUPPLIER_RETURN',
            quantity: -1,
            reference_type: 'supplier_return',
            reference_id: 'supplier-return-1',
          },
        ],
      }),
      jsonResponse({
        records: [
          {
            product_id: 'product-1',
            product_name: 'Notebook',
            sku_code: 'SKU-001',
            stock_on_hand: 5,
            last_entry_type: 'SUPPLIER_RETURN',
          },
        ],
      }),
      jsonResponse({
        id: 'supplier-payment-1',
        tenant_id: 'tenant-acme',
        branch_id: 'branch-1',
        supplier_id: 'supplier-1',
        purchase_invoice_id: 'purchase-invoice-1',
        payment_number: 'SPAY-2627-000001',
        paid_on: '2026-04-14',
        payment_method: 'bank_transfer',
        amount: 200,
        reference: 'UTR-001',
      }),
      jsonResponse({
        branch_id: 'branch-1',
        invoiced_total: 354,
        credit_note_total: 59,
        paid_total: 200,
        outstanding_total: 95,
        records: [
          {
            purchase_invoice_id: 'purchase-invoice-1',
            purchase_invoice_number: 'SPINV-2627-000001',
            supplier_name: 'Paper Supply Co',
            grand_total: 354,
            credit_note_total: 59,
            paid_total: 200,
            outstanding_total: 95,
            settlement_status: 'PARTIALLY_SETTLED',
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

  test('creates purchase invoice, supplier return, and supplier payment from the owner workspace', async () => {
    render(<App />);

    fireEvent.change(screen.getByLabelText('Korsenex token'), {
      target: { value: 'stub:sub=owner-1;email=owner@acme.local;name=Acme Owner' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Start owner session' }));

    expect(await screen.findByText('Acme Owner')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Supplier name'), { target: { value: 'Paper Supply Co' } });
    fireEvent.change(screen.getByLabelText('Supplier GSTIN'), { target: { value: '29AAAAA1111A1Z5' } });
    fireEvent.change(screen.getByLabelText('Payment terms (days)'), { target: { value: '14' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create supplier' }));
    await screen.findByText('Latest supplier');

    fireEvent.change(screen.getByLabelText('Purchase quantity'), { target: { value: '6' } });
    fireEvent.change(screen.getByLabelText('Unit cost'), { target: { value: '50' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create purchase order' }));
    await screen.findByText('Latest purchase order');

    fireEvent.change(screen.getByLabelText('Approval note'), { target: { value: 'Ready for supplier settlement' } });
    fireEvent.click(screen.getByRole('button', { name: 'Submit approval' }));
    await screen.findByText('Latest approval state');

    fireEvent.change(screen.getByLabelText('Decision note'), { target: { value: 'Approved for supplier settlement' } });
    fireEvent.click(screen.getByRole('button', { name: 'Approve purchase order' }));
    await waitFor(() => {
      expect(screen.getByText('Paper Supply Co :: APPROVED')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: 'Create goods receipt' }));
    await screen.findByText('Latest goods receipt');

    fireEvent.click(screen.getByRole('button', { name: 'Create purchase invoice' }));
    await waitFor(() => {
      expect(screen.getByText('Latest purchase invoice')).toBeInTheDocument();
      expect(screen.getByText('SPINV-2627-000001')).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText('Supplier return quantity'), { target: { value: '1' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create supplier return' }));
    await waitFor(() => {
      expect(screen.getByText('Latest supplier return')).toBeInTheDocument();
      expect(screen.getByText('SRCN-2627-000001')).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText('Supplier payment amount'), { target: { value: '200' } });
    fireEvent.change(screen.getByLabelText('Supplier payment reference'), { target: { value: 'UTR-001' } });
    fireEvent.click(screen.getByRole('button', { name: 'Record supplier payment' }));

    await waitFor(() => {
      expect(screen.getByText('Latest supplier payment')).toBeInTheDocument();
      expect(screen.getByText('SPAY-2627-000001')).toBeInTheDocument();
      expect(screen.getByText('Outstanding total')).toBeInTheDocument();
      expect(screen.getByText('95')).toBeInTheDocument();
    });
  });
});
