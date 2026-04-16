import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import type {
  ControlPlaneGoodsReceipt,
  ControlPlaneGoodsReceiptRecord,
  ControlPlanePurchaseOrder,
  ControlPlaneReceivingBoard,
} from '@store/types';
import { storeControlPlaneClient } from './client';

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

describe('storeControlPlaneClient reviewed receiving routes', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    globalThis.fetch = vi.fn() as typeof fetch;
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  test('loads the receiving board and purchase-order detail', async () => {
    const board: ControlPlaneReceivingBoard = {
      branch_id: 'branch-1',
      blocked_count: 0,
      ready_count: 1,
      received_count: 0,
      received_with_variance_count: 0,
      records: [
        {
          purchase_order_id: 'po-1',
          purchase_order_number: 'PO-001',
          supplier_name: 'Acme Wholesale',
          approval_status: 'APPROVED',
          receiving_status: 'READY',
          can_receive: true,
          has_discrepancy: false,
          variance_quantity: 0,
          blocked_reason: null,
          goods_receipt_id: null,
        },
      ],
    };
    const purchaseOrder: ControlPlanePurchaseOrder = {
      id: 'po-1',
      tenant_id: 'tenant-1',
      branch_id: 'branch-1',
      supplier_id: 'supplier-1',
      purchase_order_number: 'PO-001',
      approval_status: 'APPROVED',
      subtotal: 1700,
      tax_total: 306,
      grand_total: 2006,
      lines: [
        {
          product_id: 'product-1',
          product_name: 'Classic Tea',
          sku_code: 'tea-classic-250g',
          quantity: 24,
          unit_cost: 50,
          line_total: 1200,
        },
      ],
    };

    vi.mocked(globalThis.fetch)
      .mockResolvedValueOnce(jsonResponse(board) as never)
      .mockResolvedValueOnce(jsonResponse(purchaseOrder) as never);

    const boardResult = await storeControlPlaneClient.getReceivingBoard('access-token', 'tenant-1', 'branch-1');
    const purchaseOrderResult = await storeControlPlaneClient.getPurchaseOrder('access-token', 'tenant-1', 'branch-1', 'po-1');

    expect(boardResult).toEqual(board);
    expect(purchaseOrderResult).toEqual(purchaseOrder);
  });

  test('creates and lists goods receipts', async () => {
    const goodsReceipt: ControlPlaneGoodsReceipt = {
      id: 'grn-1',
      tenant_id: 'tenant-1',
      branch_id: 'branch-1',
      purchase_order_id: 'po-1',
      supplier_id: 'supplier-1',
      goods_receipt_number: 'GRN-BRANCH1-0001',
      received_on: '2026-04-16',
      note: 'Short shipment noted',
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
          unit_cost: 50,
          line_total: 1000,
          discrepancy_note: 'Four cartons short',
        },
      ],
    };
    const receiptRecord: ControlPlaneGoodsReceiptRecord = {
      goods_receipt_id: 'grn-1',
      goods_receipt_number: 'GRN-BRANCH1-0001',
      purchase_order_id: 'po-1',
      purchase_order_number: 'PO-001',
      supplier_id: 'supplier-1',
      supplier_name: 'Acme Wholesale',
      received_on: '2026-04-16',
      line_count: 1,
      received_quantity: 20,
      ordered_quantity: 24,
      variance_quantity: 4,
      has_discrepancy: true,
      note: 'Short shipment noted',
    };

    vi.mocked(globalThis.fetch)
      .mockResolvedValueOnce(jsonResponse(goodsReceipt) as never)
      .mockResolvedValueOnce(jsonResponse({ records: [receiptRecord] }) as never);

    const createResult = await storeControlPlaneClient.createGoodsReceipt('access-token', 'tenant-1', 'branch-1', {
      purchase_order_id: 'po-1',
      note: 'Short shipment noted',
      lines: [
        {
          product_id: 'product-1',
          received_quantity: 20,
          discrepancy_note: 'Four cartons short',
        },
      ],
    });
    const listResult = await storeControlPlaneClient.listGoodsReceipts('access-token', 'tenant-1', 'branch-1');

    expect(createResult).toEqual(goodsReceipt);
    expect(listResult.records).toEqual([receiptRecord]);
  });
});
