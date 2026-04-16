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
      <button type="button" onClick={() => void workspace.loadBatchExpiryReport()}>
        Load branch expiry report
      </button>
      <button type="button" onClick={() => void workspace.loadBatchExpiryBoard()}>
        Load expiry board
      </button>
      <button type="button" onClick={() => void workspace.createBatchExpirySession()}>
        Create expiry session
      </button>
      <button type="button" onClick={() => void workspace.recordBatchExpirySession()}>
        Record expiry session
      </button>
      <button type="button" onClick={() => void workspace.approveBatchExpirySession()}>
        Approve expiry session
      </button>
      <button type="button" onClick={() => void workspace.cancelBatchExpirySession()}>
        Cancel expiry session
      </button>

      <label htmlFor="workspace-expiry-session-note">Expiry session note</label>
      <input
        id="workspace-expiry-session-note"
        value={workspace.expirySessionNote}
        onChange={(event) => workspace.setExpirySessionNote(event.target.value)}
      />
      <label htmlFor="workspace-expiry-write-off-quantity">Expiry write-off quantity</label>
      <input
        id="workspace-expiry-write-off-quantity"
        value={workspace.expiryWriteOffQuantity}
        onChange={(event) => workspace.setExpiryWriteOffQuantity(event.target.value)}
      />
      <label htmlFor="workspace-expiry-write-off-reason">Expiry write-off reason</label>
      <input
        id="workspace-expiry-write-off-reason"
        value={workspace.expiryWriteOffReason}
        onChange={(event) => workspace.setExpiryWriteOffReason(event.target.value)}
      />
      <label htmlFor="workspace-expiry-review-note">Expiry review note</label>
      <input
        id="workspace-expiry-review-note"
        value={workspace.expiryReviewNote}
        onChange={(event) => workspace.setExpiryReviewNote(event.target.value)}
      />

      <output>{workspace.actor?.full_name ?? 'No actor'}</output>
      <output>{workspace.batchExpiryReport ? `Report tracked -> ${workspace.batchExpiryReport.tracked_lot_count}` : 'No report'}</output>
      <output>{workspace.batchExpiryBoard ? `Board open -> ${workspace.batchExpiryBoard.open_count}` : 'No board'}</output>
      <output>{workspace.activeBatchExpirySession ? `Session ${workspace.activeBatchExpirySession.session_number} -> ${workspace.activeBatchExpirySession.status}` : 'No active session'}</output>
      <output>{workspace.latestBatchWriteOff ? `Latest write-off -> ${workspace.latestBatchWriteOff.batch_number} -> ${workspace.latestBatchWriteOff.remaining_quantity}` : 'No latest write-off'}</output>
    </div>
  );
}

describe('store runtime reviewed batch expiry workspace flow', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    const responses = [
      jsonResponse({ access_token: 'session-stock-clerk', token_type: 'Bearer' }),
      jsonResponse({
        user_id: 'user-stock-clerk',
        email: 'stock@acme.local',
        full_name: 'Stock Clerk',
        is_platform_admin: false,
        tenant_memberships: [],
        branch_memberships: [{ tenant_id: 'tenant-acme', branch_id: 'branch-1', role_name: 'stock_clerk', status: 'ACTIVE' }],
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
      jsonResponse({ records: [] }),
      jsonResponse({
        records: [
          {
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            stock_on_hand: 6,
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
            device_name: 'Backroom Tablet',
            device_code: 'backroom-1',
            session_surface: 'store_desktop',
            status: 'ACTIVE',
            assigned_staff_profile_id: null,
            assigned_staff_full_name: null,
          },
        ],
      }),
      jsonResponse({ records: [] }),
      jsonResponse({
        branch_id: 'branch-1',
        tracked_lot_count: 1,
        expiring_soon_count: 1,
        expired_count: 0,
        untracked_stock_quantity: 0,
        records: [
          {
            batch_lot_id: 'lot-1',
            product_id: 'product-1',
            product_name: 'Classic Tea',
            batch_number: 'BATCH-A',
            expiry_date: '2026-04-21',
            days_to_expiry: 7,
            received_quantity: 6,
            written_off_quantity: 0,
            remaining_quantity: 6,
            status: 'EXPIRING_SOON',
          },
        ],
      }),
      jsonResponse({
        branch_id: 'branch-1',
        open_count: 0,
        reviewed_count: 0,
        approved_count: 0,
        canceled_count: 0,
        records: [],
      }),
      jsonResponse({
        id: 'bes-1',
        tenant_id: 'tenant-acme',
        branch_id: 'branch-1',
        batch_lot_id: 'lot-1',
        product_id: 'product-1',
        session_number: 'BES-BLRFLAGSHIP-0001',
        status: 'OPEN',
        remaining_quantity_snapshot: 6,
        proposed_quantity: null,
        reason: null,
        note: 'Shelf check before disposal',
        review_note: null,
        created_at: '2026-04-16T09:00:00Z',
        updated_at: '2026-04-16T09:00:00Z',
      }),
      jsonResponse({
        branch_id: 'branch-1',
        open_count: 1,
        reviewed_count: 0,
        approved_count: 0,
        canceled_count: 0,
        records: [
          {
            batch_expiry_session_id: 'bes-1',
            session_number: 'BES-BLRFLAGSHIP-0001',
            batch_lot_id: 'lot-1',
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            batch_number: 'BATCH-A',
            status: 'OPEN',
            remaining_quantity_snapshot: 6,
            proposed_quantity: null,
            reason: null,
            note: 'Shelf check before disposal',
            review_note: null,
            created_at: '2026-04-16T09:00:00Z',
            updated_at: '2026-04-16T09:00:00Z',
          },
        ],
      }),
      jsonResponse({
        id: 'bes-1',
        tenant_id: 'tenant-acme',
        branch_id: 'branch-1',
        batch_lot_id: 'lot-1',
        product_id: 'product-1',
        session_number: 'BES-BLRFLAGSHIP-0001',
        status: 'REVIEWED',
        remaining_quantity_snapshot: 6,
        proposed_quantity: 1,
        reason: 'Expired on shelf',
        note: 'Shelf check before disposal',
        review_note: null,
        created_at: '2026-04-16T09:00:00Z',
        updated_at: '2026-04-16T09:05:00Z',
      }),
      jsonResponse({
        branch_id: 'branch-1',
        open_count: 0,
        reviewed_count: 1,
        approved_count: 0,
        canceled_count: 0,
        records: [
          {
            batch_expiry_session_id: 'bes-1',
            session_number: 'BES-BLRFLAGSHIP-0001',
            batch_lot_id: 'lot-1',
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            batch_number: 'BATCH-A',
            status: 'REVIEWED',
            remaining_quantity_snapshot: 6,
            proposed_quantity: 1,
            reason: 'Expired on shelf',
            note: 'Shelf check before disposal',
            review_note: null,
            created_at: '2026-04-16T09:00:00Z',
            updated_at: '2026-04-16T09:05:00Z',
          },
        ],
      }),
      jsonResponse({
        session: {
          id: 'bes-1',
          tenant_id: 'tenant-acme',
          branch_id: 'branch-1',
          batch_lot_id: 'lot-1',
          product_id: 'product-1',
          session_number: 'BES-BLRFLAGSHIP-0001',
          status: 'APPROVED',
          remaining_quantity_snapshot: 6,
          proposed_quantity: 1,
          reason: 'Expired on shelf',
          note: 'Shelf check before disposal',
          review_note: 'Approved after shelf review',
          created_at: '2026-04-16T09:00:00Z',
          updated_at: '2026-04-16T09:08:00Z',
        },
        write_off: {
          batch_lot_id: 'lot-1',
          product_id: 'product-1',
          product_name: 'Classic Tea',
          batch_number: 'BATCH-A',
          expiry_date: '2026-04-21',
          received_quantity: 6,
          written_off_quantity: 1,
          remaining_quantity: 5,
          status: 'EXPIRING_SOON',
          reason: 'Expired on shelf',
        },
      }),
      jsonResponse({
        branch_id: 'branch-1',
        open_count: 0,
        reviewed_count: 0,
        approved_count: 1,
        canceled_count: 0,
        records: [
          {
            batch_expiry_session_id: 'bes-1',
            session_number: 'BES-BLRFLAGSHIP-0001',
            batch_lot_id: 'lot-1',
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            batch_number: 'BATCH-A',
            status: 'APPROVED',
            remaining_quantity_snapshot: 6,
            proposed_quantity: 1,
            reason: 'Expired on shelf',
            note: 'Shelf check before disposal',
            review_note: 'Approved after shelf review',
            created_at: '2026-04-16T09:00:00Z',
            updated_at: '2026-04-16T09:08:00Z',
          },
        ],
      }),
      jsonResponse({
        branch_id: 'branch-1',
        tracked_lot_count: 1,
        expiring_soon_count: 1,
        expired_count: 0,
        untracked_stock_quantity: 0,
        records: [
          {
            batch_lot_id: 'lot-1',
            product_id: 'product-1',
            product_name: 'Classic Tea',
            batch_number: 'BATCH-A',
            expiry_date: '2026-04-21',
            days_to_expiry: 7,
            received_quantity: 6,
            written_off_quantity: 1,
            remaining_quantity: 5,
            status: 'EXPIRING_SOON',
          },
        ],
      }),
      jsonResponse({
        records: [
          {
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            stock_on_hand: 5,
            last_entry_type: 'EXPIRY_WRITE_OFF',
          },
        ],
      }),
      jsonResponse({
        id: 'bes-2',
        tenant_id: 'tenant-acme',
        branch_id: 'branch-1',
        batch_lot_id: 'lot-1',
        product_id: 'product-1',
        session_number: 'BES-BLRFLAGSHIP-0002',
        status: 'OPEN',
        remaining_quantity_snapshot: 5,
        proposed_quantity: null,
        reason: null,
        note: 'Recheck second lot',
        review_note: null,
        created_at: '2026-04-16T10:00:00Z',
        updated_at: '2026-04-16T10:00:00Z',
      }),
      jsonResponse({
        branch_id: 'branch-1',
        open_count: 1,
        reviewed_count: 0,
        approved_count: 1,
        canceled_count: 0,
        records: [
          {
            batch_expiry_session_id: 'bes-2',
            session_number: 'BES-BLRFLAGSHIP-0002',
            batch_lot_id: 'lot-1',
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            batch_number: 'BATCH-A',
            status: 'OPEN',
            remaining_quantity_snapshot: 5,
            proposed_quantity: null,
            reason: null,
            note: 'Recheck second lot',
            review_note: null,
            created_at: '2026-04-16T10:00:00Z',
            updated_at: '2026-04-16T10:00:00Z',
          },
          {
            batch_expiry_session_id: 'bes-1',
            session_number: 'BES-BLRFLAGSHIP-0001',
            batch_lot_id: 'lot-1',
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            batch_number: 'BATCH-A',
            status: 'APPROVED',
            remaining_quantity_snapshot: 6,
            proposed_quantity: 1,
            reason: 'Expired on shelf',
            note: 'Shelf check before disposal',
            review_note: 'Approved after shelf review',
            created_at: '2026-04-16T09:00:00Z',
            updated_at: '2026-04-16T09:08:00Z',
          },
        ],
      }),
      jsonResponse({
        id: 'bes-2',
        tenant_id: 'tenant-acme',
        branch_id: 'branch-1',
        batch_lot_id: 'lot-1',
        product_id: 'product-1',
        session_number: 'BES-BLRFLAGSHIP-0002',
        status: 'CANCELED',
        remaining_quantity_snapshot: 5,
        proposed_quantity: null,
        reason: null,
        note: 'Recheck second lot',
        review_note: 'Canceled after recount',
        created_at: '2026-04-16T10:00:00Z',
        updated_at: '2026-04-16T10:02:00Z',
      }),
      jsonResponse({
        branch_id: 'branch-1',
        open_count: 0,
        reviewed_count: 0,
        approved_count: 1,
        canceled_count: 1,
        records: [
          {
            batch_expiry_session_id: 'bes-2',
            session_number: 'BES-BLRFLAGSHIP-0002',
            batch_lot_id: 'lot-1',
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            batch_number: 'BATCH-A',
            status: 'CANCELED',
            remaining_quantity_snapshot: 5,
            proposed_quantity: null,
            reason: null,
            note: 'Recheck second lot',
            review_note: 'Canceled after recount',
            created_at: '2026-04-16T10:00:00Z',
            updated_at: '2026-04-16T10:02:00Z',
          },
          {
            batch_expiry_session_id: 'bes-1',
            session_number: 'BES-BLRFLAGSHIP-0001',
            batch_lot_id: 'lot-1',
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            batch_number: 'BATCH-A',
            status: 'APPROVED',
            remaining_quantity_snapshot: 6,
            proposed_quantity: 1,
            reason: 'Expired on shelf',
            note: 'Shelf check before disposal',
            review_note: 'Approved after shelf review',
            created_at: '2026-04-16T09:00:00Z',
            updated_at: '2026-04-16T09:08:00Z',
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

  test('loads report and board, reviews a session, approves it, then cancels a later session', async () => {
    render(<WorkspaceHarness />);

    fireEvent.change(screen.getByLabelText('Korsenex token'), {
      target: { value: 'stub:sub=stock-clerk-1;email=stock@acme.local;name=Stock Clerk' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Start runtime session' }));

    expect(await screen.findByText('Stock Clerk')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Load branch expiry report' }));
    fireEvent.click(screen.getByRole('button', { name: 'Load expiry board' }));

    await waitFor(() => {
      expect(screen.getByText('Report tracked -> 1')).toBeInTheDocument();
      expect(screen.getByText('Board open -> 0')).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText('Expiry session note'), {
      target: { value: 'Shelf check before disposal' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Create expiry session' }));

    await waitFor(() => {
      expect(screen.getByText('Session BES-BLRFLAGSHIP-0001 -> OPEN')).toBeInTheDocument();
      expect(screen.getByText('Board open -> 1')).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText('Expiry write-off quantity'), { target: { value: '1' } });
    fireEvent.change(screen.getByLabelText('Expiry write-off reason'), { target: { value: 'Expired on shelf' } });
    fireEvent.click(screen.getByRole('button', { name: 'Record expiry session' }));

    await waitFor(() => {
      expect(screen.getByText('Session BES-BLRFLAGSHIP-0001 -> REVIEWED')).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText('Expiry review note'), { target: { value: 'Approved after shelf review' } });
    fireEvent.click(screen.getByRole('button', { name: 'Approve expiry session' }));

    await waitFor(() => {
      expect(screen.getByText('Session BES-BLRFLAGSHIP-0001 -> APPROVED')).toBeInTheDocument();
      expect(screen.getByText('Latest write-off -> BATCH-A -> 5')).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText('Expiry session note'), {
      target: { value: 'Recheck second lot' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Create expiry session' }));

    await waitFor(() => {
      expect(screen.getByText('Session BES-BLRFLAGSHIP-0002 -> OPEN')).toBeInTheDocument();
      expect(screen.getByText('Board open -> 1')).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText('Expiry review note'), { target: { value: 'Canceled after recount' } });
    fireEvent.click(screen.getByRole('button', { name: 'Cancel expiry session' }));

    await waitFor(() => {
      expect(screen.getByText('Session BES-BLRFLAGSHIP-0002 -> CANCELED')).toBeInTheDocument();
      expect(screen.getByText('Board open -> 0')).toBeInTheDocument();
    });
  });
});
