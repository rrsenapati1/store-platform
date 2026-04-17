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
    const catalogProduct = {
      product_id: 'product-1',
      tenant_id: 'tenant-acme',
      name: 'Notebook',
      sku_code: 'SKU-001',
      barcode: '8901234567890',
      hsn_sac_code: '4820',
      gst_rate: 18,
      selling_price: 100,
      status: 'ACTIVE',
    };
    let supplier:
      | {
          supplier_id: string;
          tenant_id: string;
          name: string;
          gstin: string;
          payment_terms_days: number;
          status: string;
        }
      | null = null;
    let purchaseOrder:
      | {
          id: string;
          tenant_id: string;
          branch_id: string;
          supplier_id: string;
          purchase_order_number: string;
          approval_status: 'NOT_REQUESTED' | 'PENDING_APPROVAL' | 'APPROVED';
          subtotal: number;
          tax_total: number;
          grand_total: number;
          lines: Array<{
            product_id: string;
            product_name: string;
            sku_code: string;
            quantity: number;
            unit_cost: number;
            line_total: number;
          }>;
        }
      | null = null;
    let approvalRequestedNote: string | null = null;
    let approvalDecisionNote: string | null = null;
    let goodsReceipt:
      | {
          id: string;
          tenant_id: string;
          branch_id: string;
          purchase_order_id: string;
          supplier_id: string;
          goods_receipt_number: string;
          received_on: string;
          lines: Array<{
            product_id: string;
            product_name: string;
            sku_code: string;
            quantity: number;
            unit_cost: number;
            line_total: number;
          }>;
        }
      | null = null;
    let purchaseInvoice:
      | {
          id: string;
          tenant_id: string;
          branch_id: string;
          supplier_id: string;
          goods_receipt_id: string;
          invoice_number: string;
          invoice_date: string;
          due_date: string;
          payment_terms_days: number;
          subtotal: number;
          cgst_total: number;
          sgst_total: number;
          igst_total: number;
          grand_total: number;
          lines: Array<{
            product_id: string;
            product_name: string;
            sku_code: string;
            quantity: number;
            unit_cost: number;
            gst_rate: number;
            line_subtotal: number;
            tax_total: number;
            line_total: number;
          }>;
        }
      | null = null;
    let supplierReturn:
      | {
          id: string;
          tenant_id: string;
          branch_id: string;
          supplier_id: string;
          purchase_invoice_id: string;
          supplier_credit_note_number: string;
          issued_on: string;
          subtotal: number;
          cgst_total: number;
          sgst_total: number;
          igst_total: number;
          grand_total: number;
          lines: Array<{
            product_id: string;
            product_name: string;
            sku_code: string;
            quantity: number;
            unit_cost: number;
            gst_rate: number;
            line_subtotal: number;
            tax_total: number;
            line_total: number;
          }>;
        }
      | null = null;
    let supplierPayment:
      | {
          id: string;
          tenant_id: string;
          branch_id: string;
          supplier_id: string;
          purchase_invoice_id: string;
          payment_number: string;
          paid_on: string;
          payment_method: string;
          amount: number;
          reference: string;
        }
      | null = null;

    function buildPurchaseOrderRecords() {
      if (!purchaseOrder || !supplier) {
        return [];
      }
      return [
        {
          purchase_order_id: purchaseOrder.id,
          purchase_order_number: purchaseOrder.purchase_order_number,
          supplier_id: supplier.supplier_id,
          supplier_name: supplier.name,
          approval_status: purchaseOrder.approval_status,
          line_count: purchaseOrder.lines.length,
          ordered_quantity: purchaseOrder.lines.reduce((total, line) => total + line.quantity, 0),
          grand_total: purchaseOrder.grand_total,
        },
      ];
    }

    function buildPurchaseApprovalReport() {
      const records =
        purchaseOrder && supplier
          ? [
              {
                purchase_order_id: purchaseOrder.id,
                purchase_order_number: purchaseOrder.purchase_order_number,
                supplier_name: supplier.name,
                approval_status: purchaseOrder.approval_status,
                line_count: purchaseOrder.lines.length,
                ordered_quantity: purchaseOrder.lines.reduce((total, line) => total + line.quantity, 0),
                grand_total: purchaseOrder.grand_total,
                approval_requested_note: approvalRequestedNote,
                approval_decision_note: approvalDecisionNote,
              },
            ]
          : [];

      return {
        branch_id: 'branch-1',
        not_requested_count: records.filter((record) => record.approval_status === 'NOT_REQUESTED').length,
        pending_approval_count: records.filter((record) => record.approval_status === 'PENDING_APPROVAL').length,
        approved_count: records.filter((record) => record.approval_status === 'APPROVED').length,
        rejected_count: 0,
        records,
      };
    }

    function buildGoodsReceiptRecords() {
      if (!goodsReceipt || !purchaseOrder || !supplier) {
        return [];
      }
      return [
        {
          goods_receipt_id: goodsReceipt.id,
          goods_receipt_number: goodsReceipt.goods_receipt_number,
          purchase_order_id: purchaseOrder.id,
          purchase_order_number: purchaseOrder.purchase_order_number,
          supplier_id: supplier.supplier_id,
          supplier_name: supplier.name,
          received_on: goodsReceipt.received_on,
          line_count: goodsReceipt.lines.length,
          received_quantity: goodsReceipt.lines.reduce((total, line) => total + line.quantity, 0),
        },
      ];
    }

    function buildReceivingBoard() {
      if (!purchaseOrder || !supplier) {
        return {
          branch_id: 'branch-1',
          blocked_count: 0,
          ready_count: 0,
          received_count: 0,
          records: [],
        };
      }
      const receivingStatus = goodsReceipt ? 'RECEIVED' : purchaseOrder.approval_status === 'APPROVED' ? 'READY' : 'BLOCKED';
      const canReceive = purchaseOrder.approval_status === 'APPROVED' && goodsReceipt == null;
      return {
        branch_id: 'branch-1',
        blocked_count: receivingStatus === 'BLOCKED' ? 1 : 0,
        ready_count: receivingStatus === 'READY' ? 1 : 0,
        received_count: receivingStatus === 'RECEIVED' ? 1 : 0,
        records: [
          {
            purchase_order_id: purchaseOrder.id,
            purchase_order_number: purchaseOrder.purchase_order_number,
            supplier_name: supplier.name,
            approval_status: purchaseOrder.approval_status,
            receiving_status: receivingStatus,
            can_receive: canReceive,
            blocked_reason: canReceive || receivingStatus === 'RECEIVED' ? null : 'Purchase order requires approval',
            goods_receipt_id: goodsReceipt?.id ?? null,
          },
        ],
      };
    }

    function buildInventoryLedgerRecords() {
      const records: Array<{
        inventory_ledger_entry_id: string;
        product_id: string;
        product_name: string;
        sku_code: string;
        entry_type: string;
        quantity: number;
        reference_type: string;
        reference_id: string;
      }> = [];

      if (goodsReceipt) {
        records.push({
          inventory_ledger_entry_id: 'ledger-1',
          product_id: catalogProduct.product_id,
          product_name: catalogProduct.name,
          sku_code: catalogProduct.sku_code,
          entry_type: 'PURCHASE_RECEIPT',
          quantity: goodsReceipt.lines.reduce((total, line) => total + line.quantity, 0),
          reference_type: 'goods_receipt',
          reference_id: goodsReceipt.id,
        });
      }
      if (supplierReturn) {
        records.push({
          inventory_ledger_entry_id: 'ledger-2',
          product_id: catalogProduct.product_id,
          product_name: catalogProduct.name,
          sku_code: catalogProduct.sku_code,
          entry_type: 'SUPPLIER_RETURN',
          quantity: -supplierReturn.lines.reduce((total, line) => total + line.quantity, 0),
          reference_type: 'supplier_return',
          reference_id: supplierReturn.id,
        });
      }

      return records;
    }

    function buildInventorySnapshotRecords() {
      const receivedQuantity = goodsReceipt?.lines.reduce((total, line) => total + line.quantity, 0) ?? 0;
      const returnedQuantity = supplierReturn?.lines.reduce((total, line) => total + line.quantity, 0) ?? 0;
      const stockOnHand = receivedQuantity - returnedQuantity;
      if (stockOnHand <= 0) {
        return [];
      }
      return [
        {
          product_id: catalogProduct.product_id,
          product_name: catalogProduct.name,
          sku_code: catalogProduct.sku_code,
          stock_on_hand: stockOnHand,
          last_entry_type: supplierReturn ? 'SUPPLIER_RETURN' : 'PURCHASE_RECEIPT',
        },
      ];
    }

    function buildPurchaseInvoiceRecords() {
      if (!purchaseInvoice || !supplier || !goodsReceipt) {
        return [];
      }
      return [
        {
          purchase_invoice_id: purchaseInvoice.id,
          purchase_invoice_number: purchaseInvoice.invoice_number,
          supplier_id: supplier.supplier_id,
          supplier_name: supplier.name,
          goods_receipt_id: goodsReceipt.id,
          goods_receipt_number: goodsReceipt.goods_receipt_number,
          invoice_date: purchaseInvoice.invoice_date,
          due_date: purchaseInvoice.due_date,
          grand_total: purchaseInvoice.grand_total,
        },
      ];
    }

    function buildSupplierPayablesReport() {
      if (!purchaseInvoice || !supplier) {
        return {
          branch_id: 'branch-1',
          invoiced_total: 0,
          credit_note_total: 0,
          paid_total: 0,
          outstanding_total: 0,
          records: [],
        };
      }

      const creditNoteTotal = supplierReturn?.grand_total ?? 0;
      const paidTotal = supplierPayment?.amount ?? 0;
      const outstandingTotal = purchaseInvoice.grand_total - creditNoteTotal - paidTotal;

      return {
        branch_id: 'branch-1',
        invoiced_total: purchaseInvoice.grand_total,
        credit_note_total: creditNoteTotal,
        paid_total: paidTotal,
        outstanding_total: outstandingTotal,
        records: [
          {
            purchase_invoice_id: purchaseInvoice.id,
            purchase_invoice_number: purchaseInvoice.invoice_number,
            supplier_name: supplier.name,
            grand_total: purchaseInvoice.grand_total,
            credit_note_total: creditNoteTotal,
            paid_total: paidTotal,
            outstanding_total: outstandingTotal,
            settlement_status:
              outstandingTotal === purchaseInvoice.grand_total
                ? 'UNPAID'
                : outstandingTotal > 0
                  ? 'PARTIALLY_SETTLED'
                  : 'SETTLED',
          },
        ],
      };
    }

    globalThis.fetch = vi.fn(async (input, init) => {
      const url = typeof input === 'string' ? input : input.toString();
      const method = init?.method ?? 'GET';

      if (url === '/v1/auth/oidc/exchange' && method === 'POST') {
        return jsonResponse({ access_token: 'session-owner', token_type: 'Bearer' }) as never;
      }
      if (url === '/v1/auth/me' && method === 'GET') {
        return jsonResponse({
          user_id: 'user-owner',
          email: 'owner@acme.local',
          full_name: 'Acme Owner',
          is_platform_admin: false,
          tenant_memberships: [{ tenant_id: 'tenant-acme', role_name: 'tenant_owner', status: 'ACTIVE' }],
          branch_memberships: [],
        }) as never;
      }
      if (url === '/v1/tenants/tenant-acme' && method === 'GET') {
        return jsonResponse({
          id: 'tenant-acme',
          name: 'Acme Retail',
          slug: 'acme-retail',
          status: 'ACTIVE',
          onboarding_status: 'BRANCH_READY',
        }) as never;
      }
      if (url === '/v1/tenants/tenant-acme/branches' && method === 'GET') {
        return jsonResponse({
          records: [
            {
              branch_id: 'branch-1',
              tenant_id: 'tenant-acme',
              name: 'Bengaluru Flagship',
              code: 'blr-flagship',
              status: 'ACTIVE',
            },
          ],
        }) as never;
      }
      if (url === '/v1/tenants/tenant-acme/audit-events' && method === 'GET') {
        return jsonResponse({
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
        }) as never;
      }
      if (url === '/v1/tenants/tenant-acme/staff-profiles' && method === 'GET') {
        return jsonResponse({ records: [] }) as never;
      }
      if (url === '/v1/tenants/tenant-acme/catalog/products' && method === 'GET') {
        return jsonResponse({ records: [catalogProduct] }) as never;
      }
      if (url === '/v1/tenants/tenant-acme/branches/branch-1/catalog-items' && method === 'GET') {
        return jsonResponse({ records: [] }) as never;
      }
      if (url === '/v1/tenants/tenant-acme/branches/branch-1/devices' && method === 'GET') {
        return jsonResponse({ records: [] }) as never;
      }
      if (url === '/v1/tenants/tenant-acme/suppliers' && method === 'POST') {
        supplier = {
          supplier_id: 'supplier-1',
          tenant_id: 'tenant-acme',
          name: 'Paper Supply Co',
          gstin: '29AAAAA1111A1Z5',
          payment_terms_days: 14,
          status: 'ACTIVE',
        };
        return jsonResponse({
          id: supplier.supplier_id,
          tenant_id: supplier.tenant_id,
          name: supplier.name,
          gstin: supplier.gstin,
          payment_terms_days: supplier.payment_terms_days,
          status: supplier.status,
        }) as never;
      }
      if (url === '/v1/tenants/tenant-acme/suppliers' && method === 'GET') {
        return jsonResponse({ records: supplier ? [supplier] : [] }) as never;
      }
      if (url === '/v1/tenants/tenant-acme/branches/branch-1/purchase-orders' && method === 'POST') {
        purchaseOrder = {
          id: 'purchase-order-1',
          tenant_id: 'tenant-acme',
          branch_id: 'branch-1',
          supplier_id: supplier?.supplier_id ?? 'supplier-1',
          purchase_order_number: 'PO-BLRFLAGSHIP-0001',
          approval_status: 'NOT_REQUESTED',
          subtotal: 300,
          tax_total: 54,
          grand_total: 354,
          lines: [
            {
              product_id: catalogProduct.product_id,
              product_name: catalogProduct.name,
              sku_code: catalogProduct.sku_code,
              quantity: 6,
              unit_cost: 50,
              line_total: 300,
            },
          ],
        };
        approvalRequestedNote = null;
        approvalDecisionNote = null;
        return jsonResponse(purchaseOrder) as never;
      }
      if (url === '/v1/tenants/tenant-acme/branches/branch-1/purchase-orders' && method === 'GET') {
        return jsonResponse({ records: buildPurchaseOrderRecords() }) as never;
      }
      if (url === '/v1/tenants/tenant-acme/branches/branch-1/purchase-approval-report' && method === 'GET') {
        return jsonResponse(buildPurchaseApprovalReport()) as never;
      }
      if (url === '/v1/tenants/tenant-acme/branches/branch-1/purchase-orders/purchase-order-1/submit-approval' && method === 'POST') {
        purchaseOrder = purchaseOrder ? { ...purchaseOrder, approval_status: 'PENDING_APPROVAL' } : purchaseOrder;
        approvalRequestedNote = 'Ready for supplier settlement';
        return jsonResponse(purchaseOrder) as never;
      }
      if (url === '/v1/tenants/tenant-acme/branches/branch-1/purchase-orders/purchase-order-1/approve' && method === 'POST') {
        purchaseOrder = purchaseOrder ? { ...purchaseOrder, approval_status: 'APPROVED' } : purchaseOrder;
        approvalDecisionNote = 'Approved for supplier settlement';
        return jsonResponse(purchaseOrder) as never;
      }
      if (url === '/v1/tenants/tenant-acme/branches/branch-1/goods-receipts' && method === 'POST') {
        goodsReceipt = {
          id: 'goods-receipt-1',
          tenant_id: 'tenant-acme',
          branch_id: 'branch-1',
          purchase_order_id: 'purchase-order-1',
          supplier_id: supplier?.supplier_id ?? 'supplier-1',
          goods_receipt_number: 'GRN-BLRFLAGSHIP-0001',
          received_on: '2026-04-13',
          lines: [
            {
              product_id: catalogProduct.product_id,
              product_name: catalogProduct.name,
              sku_code: catalogProduct.sku_code,
              quantity: 6,
              unit_cost: 50,
              line_total: 300,
            },
          ],
        };
        return jsonResponse(goodsReceipt) as never;
      }
      if (url === '/v1/tenants/tenant-acme/branches/branch-1/goods-receipts' && method === 'GET') {
        return jsonResponse({ records: buildGoodsReceiptRecords() }) as never;
      }
      if (url === '/v1/tenants/tenant-acme/branches/branch-1/receiving-board' && method === 'GET') {
        return jsonResponse(buildReceivingBoard()) as never;
      }
      if (url === '/v1/tenants/tenant-acme/branches/branch-1/inventory-ledger' && method === 'GET') {
        return jsonResponse({ records: buildInventoryLedgerRecords() }) as never;
      }
      if (url === '/v1/tenants/tenant-acme/branches/branch-1/inventory-snapshot' && method === 'GET') {
        return jsonResponse({ records: buildInventorySnapshotRecords() }) as never;
      }
      if (url === '/v1/tenants/tenant-acme/branches/branch-1/purchase-invoices' && method === 'POST') {
        purchaseInvoice = {
          id: 'purchase-invoice-1',
          tenant_id: 'tenant-acme',
          branch_id: 'branch-1',
          supplier_id: supplier?.supplier_id ?? 'supplier-1',
          goods_receipt_id: goodsReceipt?.id ?? 'goods-receipt-1',
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
              product_id: catalogProduct.product_id,
              product_name: catalogProduct.name,
              sku_code: catalogProduct.sku_code,
              quantity: 6,
              unit_cost: 50,
              gst_rate: 18,
              line_subtotal: 300,
              tax_total: 54,
              line_total: 354,
            },
          ],
        };
        return jsonResponse(purchaseInvoice) as never;
      }
      if (url === '/v1/tenants/tenant-acme/branches/branch-1/purchase-invoices' && method === 'GET') {
        return jsonResponse({ records: buildPurchaseInvoiceRecords() }) as never;
      }
      if (url === '/v1/tenants/tenant-acme/branches/branch-1/supplier-payables-report' && method === 'GET') {
        return jsonResponse(buildSupplierPayablesReport()) as never;
      }
      if (
        url === '/v1/tenants/tenant-acme/branches/branch-1/purchase-invoices/purchase-invoice-1/supplier-returns' &&
        method === 'POST'
      ) {
        supplierReturn = {
          id: 'supplier-return-1',
          tenant_id: 'tenant-acme',
          branch_id: 'branch-1',
          supplier_id: supplier?.supplier_id ?? 'supplier-1',
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
              product_id: catalogProduct.product_id,
              product_name: catalogProduct.name,
              sku_code: catalogProduct.sku_code,
              quantity: 1,
              unit_cost: 50,
              gst_rate: 18,
              line_subtotal: 50,
              tax_total: 9,
              line_total: 59,
            },
          ],
        };
        return jsonResponse(supplierReturn) as never;
      }
      if (
        url === '/v1/tenants/tenant-acme/branches/branch-1/purchase-invoices/purchase-invoice-1/supplier-payments' &&
        method === 'POST'
      ) {
        supplierPayment = {
          id: 'supplier-payment-1',
          tenant_id: 'tenant-acme',
          branch_id: 'branch-1',
          supplier_id: supplier?.supplier_id ?? 'supplier-1',
          purchase_invoice_id: 'purchase-invoice-1',
          payment_number: 'SPAY-2627-000001',
          paid_on: '2026-04-14',
          payment_method: 'bank_transfer',
          amount: 200,
          reference: 'UTR-001',
        };
        return jsonResponse(supplierPayment) as never;
      }
      if (
        url === '/v1/tenants/tenant-acme/branches/branch-1/supplier-aging-report' ||
        url === '/v1/tenants/tenant-acme/branches/branch-1/supplier-statements' ||
        url === '/v1/tenants/tenant-acme/branches/branch-1/supplier-due-schedule' ||
        url === '/v1/tenants/tenant-acme/branches/branch-1/vendor-dispute-board' ||
        url === '/v1/tenants/tenant-acme/branches/branch-1/supplier-exception-report' ||
        url === '/v1/tenants/tenant-acme/branches/branch-1/supplier-settlement-report' ||
        url === '/v1/tenants/tenant-acme/branches/branch-1/supplier-settlement-blockers' ||
        url === '/v1/tenants/tenant-acme/branches/branch-1/supplier-escalation-report' ||
        url === '/v1/tenants/tenant-acme/branches/branch-1/supplier-performance-report' ||
        url === '/v1/tenants/tenant-acme/branches/branch-1/supplier-payment-activity'
      ) {
        return jsonResponse({ branch_id: 'branch-1', records: [] }) as never;
      }

      throw new Error(`Unexpected fetch call: ${method} ${url}`);
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
