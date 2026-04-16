/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';
import { StoreReceivingSection } from './StoreReceivingSection';
import type { StoreRuntimeWorkspaceState } from './useStoreRuntimeWorkspace';

function buildWorkspace(overrides: Partial<StoreRuntimeWorkspaceState> = {}): StoreRuntimeWorkspaceState {
  return {
    isBusy: false,
    isSessionLive: true,
    branchId: 'branch-1',
    receivingBoard: {
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
    },
    selectedReceivingPurchaseOrderId: '',
    selectedReceivingPurchaseOrder: null,
    receivingLineDrafts: [],
    goodsReceiptNote: '',
    goodsReceipts: [],
    latestGoodsReceipt: null,
    loadReceivingBoard: vi.fn(async () => {}),
    selectReceivingPurchaseOrder: vi.fn(async () => {}),
    setReceivingLineQuantity: vi.fn(),
    setReceivingLineDiscrepancyNote: vi.fn(),
    setGoodsReceiptNote: vi.fn(),
    createGoodsReceipt: vi.fn(async () => {}),
    ...overrides,
  } as unknown as StoreRuntimeWorkspaceState;
}

describe('store receiving section', () => {
  test('renders board-driven PO selection controls', () => {
    const workspace = buildWorkspace();

    render(<StoreReceivingSection workspace={workspace} />);

    expect(screen.getByRole('button', { name: 'Load receiving board' })).toBeInTheDocument();
    expect(screen.getByText('Reviewed receiving board')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Select PO-001' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Create goods receipt' })).toBeDisabled();

    fireEvent.click(screen.getByRole('button', { name: 'Select PO-001' }));
    expect(workspace.selectReceivingPurchaseOrder).toHaveBeenCalledWith('po-1');
  });

  test('renders selected reviewed-receipt draft and latest goods receipt', () => {
    const workspace = buildWorkspace({
      selectedReceivingPurchaseOrderId: 'po-1',
      selectedReceivingPurchaseOrder: {
        id: 'po-1',
        tenant_id: 'tenant-acme',
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
      },
      receivingLineDrafts: [
        {
          product_id: 'product-1',
          product_name: 'Classic Tea',
          sku_code: 'tea-classic-250g',
          ordered_quantity: 24,
          received_quantity: '20',
          discrepancy_note: 'Four cartons short',
        },
      ],
      goodsReceiptNote: 'Short shipment noted',
      latestGoodsReceipt: {
        id: 'grn-1',
        tenant_id: 'tenant-acme',
        branch_id: 'branch-1',
        purchase_order_id: 'po-1',
        supplier_id: 'supplier-1',
        goods_receipt_number: 'GRN-BLRFLAGSHIP-0001',
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
      },
    });

    render(<StoreReceivingSection workspace={workspace} />);

    expect(screen.getByText('Selected purchase order')).toBeInTheDocument();
    expect(screen.getByLabelText('Received quantity for Classic Tea')).toBeInTheDocument();
    expect(screen.getByLabelText('Discrepancy note for Classic Tea')).toBeInTheDocument();
    expect(screen.getByLabelText('Receipt note')).toBeInTheDocument();
    expect(screen.getByText('Latest goods receipt')).toBeInTheDocument();
    expect(screen.getByText('GRN-BLRFLAGSHIP-0001')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Create goods receipt' }));
    expect(workspace.createGoodsReceipt).toHaveBeenCalledTimes(1);
  });
});
