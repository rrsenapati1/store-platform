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
      <button type="button" onClick={() => void workspace.loadStockCountBoard()}>
        Load stock-count board
      </button>
      <button type="button" onClick={() => workspace.setSelectedStockCountProductId('product-1')}>
        Select stock-count product
      </button>
      <button type="button" onClick={() => void workspace.createStockCountSession()}>
        Create stock-count session
      </button>
      <button type="button" onClick={() => void workspace.recordStockCountSession()}>
        Record stock-count session
      </button>
      <button type="button" onClick={() => void workspace.approveStockCountSession()}>
        Approve stock-count session
      </button>
      <button type="button" onClick={() => void workspace.cancelStockCountSession()}>
        Cancel stock-count session
      </button>

      <label htmlFor="workspace-stock-count-note">Count note</label>
      <input
        id="workspace-stock-count-note"
        value={workspace.stockCountNote}
        onChange={(event) => workspace.setStockCountNote(event.target.value)}
      />
      <label htmlFor="workspace-blind-counted-quantity">Blind counted quantity</label>
      <input
        id="workspace-blind-counted-quantity"
        value={workspace.blindCountedQuantity}
        onChange={(event) => workspace.setBlindCountedQuantity(event.target.value)}
      />
      <label htmlFor="workspace-stock-count-review-note">Stock-count review note</label>
      <input
        id="workspace-stock-count-review-note"
        value={workspace.stockCountReviewNote}
        onChange={(event) => workspace.setStockCountReviewNote(event.target.value)}
      />

      <output>{workspace.actor?.full_name ?? 'No actor'}</output>
      <output>
        {workspace.stockCountBoard ? `Board open -> ${workspace.stockCountBoard.open_count}` : 'No board'}
      </output>
      <output>
        {workspace.activeStockCountSession
          ? `Session ${workspace.activeStockCountSession.session_number} -> ${workspace.activeStockCountSession.status}`
          : 'No active session'}
      </output>
      <output>
        {workspace.latestApprovedStockCount
          ? `Latest stock count -> ${workspace.latestApprovedStockCount.counted_quantity}`
          : 'No latest stock count'}
      </output>
    </div>
  );
}

describe('store runtime reviewed stock-count workspace flow', () => {
  const originalFetch = globalThis.fetch;

  afterEach(() => {
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  test('runs desktop reviewed stock-count flow end-to-end', async () => {
    const buildInventorySnapshot = (stockOnHand: number, lastEntryType: string) => ({
      records: [
        {
          product_id: 'product-1',
          product_name: 'Classic Tea',
          sku_code: 'tea-classic-250g',
          stock_on_hand: stockOnHand,
          last_entry_type: lastEntryType,
        },
      ],
    });
    const buildBoardRecord = (status: string, note: string, reviewNote: string | null) => ({
      stock_count_session_id: status === 'CANCELED' ? 'scs-2' : 'scs-1',
      session_number: status === 'CANCELED' ? 'SCS-BLRFLAGSHIP-0002' : 'SCS-BLRFLAGSHIP-0001',
      product_id: 'product-1',
      product_name: 'Classic Tea',
      sku_code: 'tea-classic-250g',
      status,
      expected_quantity: status === 'OPEN' || status === 'CANCELED' ? null : 12,
      counted_quantity: status === 'OPEN' || status === 'CANCELED' ? null : 10,
      variance_quantity: status === 'OPEN' || status === 'CANCELED' ? null : -2,
      note,
      review_note: reviewNote,
    });

    let inventorySnapshot = buildInventorySnapshot(12, 'PURCHASE_RECEIPT');
    let stockCountBoard = {
      branch_id: 'branch-1',
      open_count: 0,
      counted_count: 0,
      approved_count: 0,
      canceled_count: 0,
      records: [] as Array<ReturnType<typeof buildBoardRecord>>,
    };
    let activeSession: Record<string, unknown> | null = null;
    let latestApprovedStockCount: Record<string, unknown> | null = null;

    globalThis.fetch = vi.fn(async (input, init) => {
      const url = String(input);
      const method = init?.method ?? 'GET';

      if (url.endsWith('/v1/auth/oidc/exchange') && method === 'POST') {
        return jsonResponse({ access_token: 'session-stock-clerk', token_type: 'Bearer' }) as never;
      }
      if (url.endsWith('/v1/auth/me')) {
        return jsonResponse({
          user_id: 'user-stock-clerk',
          email: 'stock@acme.local',
          full_name: 'Stock Clerk',
          is_platform_admin: false,
          tenant_memberships: [],
          branch_memberships: [{ tenant_id: 'tenant-acme', branch_id: 'branch-1', role_name: 'stock_clerk', status: 'ACTIVE' }],
        }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme')) {
        return jsonResponse({
          id: 'tenant-acme',
          name: 'Acme Retail',
          slug: 'acme-retail',
          status: 'ACTIVE',
          onboarding_status: 'BRANCH_READY',
        }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches')) {
        return jsonResponse({
          records: [{ branch_id: 'branch-1', tenant_id: 'tenant-acme', name: 'Bengaluru Flagship', code: 'blr-flagship', status: 'ACTIVE' }],
        }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/catalog-items')) {
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
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/inventory-snapshot')) {
        return jsonResponse(inventorySnapshot) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/sales') && method === 'GET') {
        return jsonResponse({ records: [] }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/runtime/devices')) {
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
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/checkout-payment-sessions') && method === 'GET') {
        return jsonResponse({ records: [] }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/stock-count-board') && method === 'GET') {
        return jsonResponse(stockCountBoard) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/stock-count-sessions') && method === 'POST') {
        const payload = JSON.parse(String(init?.body ?? '{}')) as { note?: string };
        if (payload.note === 'Aisle recount') {
          activeSession = {
            id: 'scs-1',
            tenant_id: 'tenant-acme',
            branch_id: 'branch-1',
            product_id: 'product-1',
            session_number: 'SCS-BLRFLAGSHIP-0001',
            status: 'OPEN',
            expected_quantity: null,
            counted_quantity: null,
            variance_quantity: null,
            note: 'Aisle recount',
            review_note: null,
          };
          stockCountBoard = {
            ...stockCountBoard,
            open_count: 1,
            counted_count: 0,
            approved_count: latestApprovedStockCount ? 1 : 0,
            canceled_count: 0,
            records: [buildBoardRecord('OPEN', 'Aisle recount', null)],
          };
        } else {
          activeSession = {
            id: 'scs-2',
            tenant_id: 'tenant-acme',
            branch_id: 'branch-1',
            product_id: 'product-1',
            session_number: 'SCS-BLRFLAGSHIP-0002',
            status: 'OPEN',
            expected_quantity: null,
            counted_quantity: null,
            variance_quantity: null,
            note: 'Second recount',
            review_note: null,
          };
          stockCountBoard = {
            ...stockCountBoard,
            open_count: 1,
            counted_count: 0,
            approved_count: latestApprovedStockCount ? 1 : 0,
            canceled_count: 0,
            records: [
              {
                ...buildBoardRecord('OPEN', 'Second recount', null),
                stock_count_session_id: 'scs-2',
                session_number: 'SCS-BLRFLAGSHIP-0002',
              },
            ],
          };
        }
        return jsonResponse(activeSession) as never;
      }
      if (url.endsWith('/stock-count-sessions/scs-1/record') && method === 'POST') {
        activeSession = {
          id: 'scs-1',
          tenant_id: 'tenant-acme',
          branch_id: 'branch-1',
          product_id: 'product-1',
          session_number: 'SCS-BLRFLAGSHIP-0001',
          status: 'COUNTED',
          expected_quantity: 12,
          counted_quantity: 10,
          variance_quantity: -2,
          note: 'Blind count complete',
          review_note: null,
        };
        stockCountBoard = {
          ...stockCountBoard,
          open_count: 0,
          counted_count: 1,
          approved_count: 0,
          canceled_count: 0,
          records: [buildBoardRecord('COUNTED', 'Blind count complete', null)],
        };
        return jsonResponse(activeSession) as never;
      }
      if (url.endsWith('/stock-count-sessions/scs-1/approve') && method === 'POST') {
        activeSession = {
          id: 'scs-1',
          tenant_id: 'tenant-acme',
          branch_id: 'branch-1',
          product_id: 'product-1',
          session_number: 'SCS-BLRFLAGSHIP-0001',
          status: 'APPROVED',
          expected_quantity: 12,
          counted_quantity: 10,
          variance_quantity: -2,
          note: 'Blind count complete',
          review_note: 'Approved after review',
        };
        latestApprovedStockCount = {
          id: 'count-1',
          tenant_id: 'tenant-acme',
          branch_id: 'branch-1',
          product_id: 'product-1',
          counted_quantity: 10,
          expected_quantity: 12,
          variance_quantity: -2,
          note: 'Blind count complete',
          closing_stock: 10,
        };
        inventorySnapshot = buildInventorySnapshot(10, 'STOCK_COUNT');
        stockCountBoard = {
          ...stockCountBoard,
          open_count: 0,
          counted_count: 0,
          approved_count: 1,
          canceled_count: 0,
          records: [buildBoardRecord('APPROVED', 'Blind count complete', 'Approved after review')],
        };
        return jsonResponse({
          session: activeSession,
          stock_count: latestApprovedStockCount,
        }) as never;
      }
      if (url.endsWith('/stock-count-sessions/scs-2/cancel') && method === 'POST') {
        activeSession = {
          id: 'scs-2',
          tenant_id: 'tenant-acme',
          branch_id: 'branch-1',
          product_id: 'product-1',
          session_number: 'SCS-BLRFLAGSHIP-0002',
          status: 'CANCELED',
          expected_quantity: null,
          counted_quantity: null,
          variance_quantity: null,
          note: 'Second recount',
          review_note: 'Canceled after recount',
        };
        stockCountBoard = {
          ...stockCountBoard,
          open_count: 0,
          counted_count: 0,
          approved_count: 1,
          canceled_count: 1,
          records: [
            {
              ...buildBoardRecord('CANCELED', 'Second recount', 'Canceled after recount'),
              stock_count_session_id: 'scs-2',
              session_number: 'SCS-BLRFLAGSHIP-0002',
            },
          ],
        };
        return jsonResponse(activeSession) as never;
      }

      throw new Error(`Unexpected fetch call: ${method} ${url}`);
    }) as typeof fetch;

    render(<WorkspaceHarness />);

    fireEvent.change(screen.getByLabelText('Korsenex token'), {
      target: { value: 'stub:sub=stock-1;email=stock@acme.local;name=Stock Clerk' },
    });
    fireEvent.click(screen.getByText('Start runtime session'));
    await waitFor(() => expect(screen.getByText('Stock Clerk')).toBeInTheDocument());
    fireEvent.click(screen.getByText('Load stock-count board'));

    await waitFor(() => expect(screen.getByText('Board open -> 0')).toBeInTheDocument());

    fireEvent.change(screen.getByLabelText('Count note'), { target: { value: 'Aisle recount' } });
    fireEvent.click(screen.getByText('Select stock-count product'));
    fireEvent.click(screen.getByText('Create stock-count session'));

    await waitFor(() =>
      expect(screen.getByText('Session SCS-BLRFLAGSHIP-0001 -> OPEN')).toBeInTheDocument(),
    );

    fireEvent.change(screen.getByLabelText('Blind counted quantity'), { target: { value: '10' } });
    fireEvent.click(screen.getByText('Record stock-count session'));

    await waitFor(() =>
      expect(screen.getByText('Session SCS-BLRFLAGSHIP-0001 -> COUNTED')).toBeInTheDocument(),
    );

    fireEvent.change(screen.getByLabelText('Stock-count review note'), {
      target: { value: 'Approved after review' },
    });
    fireEvent.click(screen.getByText('Approve stock-count session'));

    await waitFor(() => expect(screen.getByText('Latest stock count -> 10')).toBeInTheDocument());

    fireEvent.change(screen.getByLabelText('Count note'), { target: { value: 'Second recount' } });
    fireEvent.click(screen.getByText('Create stock-count session'));
    await waitFor(() =>
      expect(screen.getByText('Session SCS-BLRFLAGSHIP-0002 -> OPEN')).toBeInTheDocument(),
    );

    fireEvent.change(screen.getByLabelText('Stock-count review note'), {
      target: { value: 'Canceled after recount' },
    });
    fireEvent.click(screen.getByText('Cancel stock-count session'));

    await waitFor(() =>
      expect(screen.getByText('Session SCS-BLRFLAGSHIP-0002 -> CANCELED')).toBeInTheDocument(),
    );
  });
});
