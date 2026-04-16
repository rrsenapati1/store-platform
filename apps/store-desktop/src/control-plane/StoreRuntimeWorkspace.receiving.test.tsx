/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { useStoreRuntimeWorkspace } from './useStoreRuntimeWorkspace';

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

function WorkspaceHarness() {
  const workspace = useStoreRuntimeWorkspace();

  return (
    <div>
      <label htmlFor="workspace-korsenex-token">Korsenex token</label>
      <input
        id="workspace-korsenex-token"
        value={workspace.korsenexToken}
        onChange={(event) => workspace.setKorsenexToken(event.target.value)}
      />
      <button type="button" onClick={() => void workspace.startSession()}>
        Start runtime session
      </button>
      <button type="button" onClick={() => void workspace.loadReceivingBoard()}>
        Load receiving board
      </button>
      <button type="button" onClick={() => void workspace.selectReceivingPurchaseOrder('po-1')}>
        Select receiving PO
      </button>
      <button type="button" onClick={() => void workspace.createGoodsReceipt()}>
        Create goods receipt
      </button>

      <label htmlFor="workspace-goods-receipt-note">Receipt note</label>
      <input
        id="workspace-goods-receipt-note"
        value={workspace.goodsReceiptNote}
        onChange={(event) => workspace.setGoodsReceiptNote(event.target.value)}
      />

      {workspace.receivingLineDrafts.map((line) => (
        <div key={line.product_id}>
          <label htmlFor={`workspace-receiving-quantity-${line.product_id}`}>
            Received quantity for {line.product_name}
          </label>
          <input
            id={`workspace-receiving-quantity-${line.product_id}`}
            value={line.received_quantity}
            onChange={(event) => workspace.setReceivingLineQuantity(line.product_id, event.target.value)}
          />
          <label htmlFor={`workspace-receiving-discrepancy-${line.product_id}`}>
            Discrepancy note for {line.product_name}
          </label>
          <input
            id={`workspace-receiving-discrepancy-${line.product_id}`}
            value={line.discrepancy_note}
            onChange={(event) => workspace.setReceivingLineDiscrepancyNote(line.product_id, event.target.value)}
          />
        </div>
      ))}

      <output>{workspace.actor?.full_name ?? 'No actor'}</output>
      <output>{workspace.receivingBoard ? `Board ready -> ${workspace.receivingBoard.ready_count}` : 'No board'}</output>
      <output>{workspace.selectedReceivingPurchaseOrder ? `Selected PO -> ${workspace.selectedReceivingPurchaseOrder.purchase_order_number}` : 'No selected PO'}</output>
      <output>{workspace.latestGoodsReceipt ? `Latest goods receipt -> ${workspace.latestGoodsReceipt.goods_receipt_number}` : 'No latest goods receipt'}</output>
    </div>
  );
}

describe('store runtime reviewed receiving workspace flow', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    globalThis.localStorage?.clear();
    globalThis.sessionStorage?.clear();

    let boardReadyCount = 1;
    let boardReceivedWithVarianceCount = 0;
    let latestGoodsReceiptId: string | null = null;
    let latestGoodsReceiptNumber: string | null = null;
    let inventorySnapshot = [
      {
        product_id: 'product-1',
        product_name: 'Classic Tea',
        sku_code: 'tea-classic-250g',
        stock_on_hand: 12,
        last_entry_type: 'PURCHASE_RECEIPT',
      },
    ];

    globalThis.fetch = vi.fn(async (input, init) => {
      const url = String(input);
      const method = init?.method ?? 'GET';

      if (url.endsWith('/v1/auth/oidc/exchange') && method === 'POST') {
        return jsonResponse({ access_token: 'session-stock-clerk', token_type: 'Bearer' }) as never;
      }
      if (url.endsWith('/v1/auth/me') && method === 'GET') {
        return jsonResponse({
          user_id: 'user-stock-clerk',
          email: 'stock@acme.local',
          full_name: 'Stock Clerk',
          is_platform_admin: false,
          tenant_memberships: [],
          branch_memberships: [{ tenant_id: 'tenant-acme', branch_id: 'branch-1', role_name: 'stock_clerk', status: 'ACTIVE' }],
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
        return jsonResponse({ records: inventorySnapshot }) as never;
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
              device_name: 'Backroom Desktop',
              device_code: 'backroom-1',
              session_surface: 'store_desktop',
              status: 'ACTIVE',
              assigned_staff_profile_id: null,
              assigned_staff_full_name: null,
            },
          ],
        }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/receiving-board') && method === 'GET') {
        return jsonResponse({
          branch_id: 'branch-1',
          blocked_count: 0,
          ready_count: boardReadyCount,
          received_count: 0,
          received_with_variance_count: boardReceivedWithVarianceCount,
          records: [
            {
              purchase_order_id: 'po-1',
              purchase_order_number: 'PO-001',
              supplier_name: 'Acme Wholesale',
              approval_status: 'APPROVED',
              receiving_status: latestGoodsReceiptId ? 'RECEIVED_WITH_VARIANCE' : 'READY',
              can_receive: !latestGoodsReceiptId,
              has_discrepancy: Boolean(latestGoodsReceiptId),
              variance_quantity: latestGoodsReceiptId ? 14 : 0,
              blocked_reason: null,
              goods_receipt_id: latestGoodsReceiptId,
            },
          ],
        }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/goods-receipts') && method === 'GET') {
        return jsonResponse({
          records: latestGoodsReceiptId
            ? [
                {
                  goods_receipt_id: latestGoodsReceiptId,
                  goods_receipt_number: latestGoodsReceiptNumber,
                  purchase_order_id: 'po-1',
                  purchase_order_number: 'PO-001',
                  supplier_id: 'supplier-1',
                  supplier_name: 'Acme Wholesale',
                  received_on: '2026-04-16',
                  line_count: 2,
                  received_quantity: 20,
                  ordered_quantity: 34,
                  variance_quantity: 14,
                  has_discrepancy: true,
                  note: 'Second line held back',
                },
              ]
            : [],
        }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/purchase-orders/po-1') && method === 'GET') {
        return jsonResponse({
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
            {
              product_id: 'product-2',
              product_name: 'Ginger Tea',
              sku_code: 'tea-ginger-250g',
              quantity: 10,
              unit_cost: 50,
              line_total: 500,
            },
          ],
        }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/goods-receipts') && method === 'POST') {
        boardReadyCount = 0;
        boardReceivedWithVarianceCount = 1;
        latestGoodsReceiptId = 'grn-1';
        latestGoodsReceiptNumber = 'GRN-BLRFLAGSHIP-0001';
        inventorySnapshot = [
          {
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            stock_on_hand: 32,
            last_entry_type: 'PURCHASE_RECEIPT',
          },
          {
            product_id: 'product-2',
            product_name: 'Ginger Tea',
            sku_code: 'tea-ginger-250g',
            stock_on_hand: 4,
            last_entry_type: 'PURCHASE_RECEIPT',
          },
        ];
        return jsonResponse({
          id: latestGoodsReceiptId,
          tenant_id: 'tenant-acme',
          branch_id: 'branch-1',
          purchase_order_id: 'po-1',
          supplier_id: 'supplier-1',
          goods_receipt_number: latestGoodsReceiptNumber,
          received_on: '2026-04-16',
          note: 'Second line held back',
          ordered_quantity_total: 34,
          received_quantity_total: 20,
          variance_quantity_total: 14,
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
            {
              product_id: 'product-2',
              product_name: 'Ginger Tea',
              sku_code: 'tea-ginger-250g',
              ordered_quantity: 10,
              quantity: 0,
              variance_quantity: 10,
              unit_cost: 50,
              line_total: 0,
              discrepancy_note: 'Supplier held dispatch',
            },
          ],
        }) as never;
      }

      throw new Error(`Unexpected fetch call: ${method} ${url}`);
    }) as typeof fetch;
  });

  afterEach(() => {
    globalThis.localStorage?.clear();
    globalThis.sessionStorage?.clear();
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  test('runs desktop reviewed receiving flow end-to-end', async () => {
    render(<WorkspaceHarness />);

    fireEvent.change(screen.getByLabelText('Korsenex token'), {
      target: { value: 'stub:sub=stock-1;email=stock@acme.local;name=Stock Clerk' },
    });
    fireEvent.click(screen.getByText('Start runtime session'));
    await waitFor(() => expect(screen.getByText('Stock Clerk')).toBeInTheDocument());

    fireEvent.click(screen.getByText('Load receiving board'));
    await waitFor(() => expect(screen.getByText('Board ready -> 1')).toBeInTheDocument());

    fireEvent.click(screen.getByText('Select receiving PO'));
    await waitFor(() => expect(screen.getByText('Selected PO -> PO-001')).toBeInTheDocument());

    fireEvent.change(screen.getByLabelText('Received quantity for Classic Tea'), {
      target: { value: '20' },
    });
    fireEvent.change(screen.getByLabelText('Discrepancy note for Classic Tea'), {
      target: { value: 'Four cartons short' },
    });
    fireEvent.change(screen.getByLabelText('Received quantity for Ginger Tea'), {
      target: { value: '0' },
    });
    fireEvent.change(screen.getByLabelText('Discrepancy note for Ginger Tea'), {
      target: { value: 'Supplier held dispatch' },
    });
    fireEvent.change(screen.getByLabelText('Receipt note'), {
      target: { value: 'Second line held back' },
    });
    fireEvent.click(screen.getByText('Create goods receipt'));

    await waitFor(() =>
      expect(screen.getByText('Latest goods receipt -> GRN-BLRFLAGSHIP-0001')).toBeInTheDocument(),
    );
  });
});
