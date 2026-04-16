/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';
import { StoreBatchExpirySection } from './StoreBatchExpirySection';
import type { StoreRuntimeWorkspaceState } from './useStoreRuntimeWorkspace';

function buildWorkspace(overrides: Partial<StoreRuntimeWorkspaceState> = {}): StoreRuntimeWorkspaceState {
  return {
    isBusy: false,
    isSessionLive: true,
    branchId: 'branch-1',
    batchExpiryReport: {
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
    },
    batchExpiryBoard: {
      branch_id: 'branch-1',
      open_count: 0,
      reviewed_count: 0,
      approved_count: 0,
      canceled_count: 0,
      records: [],
    },
    activeBatchExpirySession: null,
    expirySessionNote: '',
    expiryWriteOffQuantity: '1',
    expiryWriteOffReason: '',
    expiryReviewNote: '',
    latestBatchWriteOff: null,
    loadBatchExpiryReport: vi.fn(async () => {}),
    loadBatchExpiryBoard: vi.fn(async () => {}),
    createBatchExpirySession: vi.fn(async () => {}),
    recordBatchExpirySession: vi.fn(async () => {}),
    approveBatchExpirySession: vi.fn(async () => {}),
    cancelBatchExpirySession: vi.fn(async () => {}),
    setExpirySessionNote: vi.fn(),
    setExpiryWriteOffQuantity: vi.fn(),
    setExpiryWriteOffReason: vi.fn(),
    setExpiryReviewNote: vi.fn(),
    ...overrides,
  } as unknown as StoreRuntimeWorkspaceState;
}

describe('store batch expiry section', () => {
  test('renders report and board visibility with create-session controls', () => {
    const workspace = buildWorkspace();

    render(<StoreBatchExpirySection workspace={workspace} />);

    expect(screen.getByRole('button', { name: 'Load branch expiry report' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Load expiry board' })).toBeInTheDocument();
    expect(screen.getByText('Latest branch expiry report')).toBeInTheDocument();
    expect(screen.getByText(/BATCH-A :: Classic Tea :: 6/i)).toBeInTheDocument();
    expect(screen.getByText('Expiry disposition board')).toBeInTheDocument();
    expect(screen.getByText('No expiry review sessions recorded yet.')).toBeInTheDocument();
    expect(screen.getByLabelText('Expiry session note')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Open expiry review session' })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Open expiry review session' }));

    expect(workspace.createBatchExpirySession).toHaveBeenCalledTimes(1);
  });

  test('renders active open-session review controls', () => {
    const workspace = buildWorkspace({
      activeBatchExpirySession: {
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
        note: 'Shelf check',
        review_note: null,
      },
      expiryWriteOffQuantity: '1',
      expiryWriteOffReason: 'Expired on shelf',
      batchExpiryBoard: {
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
            note: 'Shelf check',
            review_note: null,
          },
        ],
      },
    });

    render(<StoreBatchExpirySection workspace={workspace} />);

    expect(screen.getByText('Latest expiry review session')).toBeInTheDocument();
    expect(screen.getByText('BES-BLRFLAGSHIP-0001')).toBeInTheDocument();
    expect(screen.getByLabelText('Proposed write-off quantity')).toBeInTheDocument();
    expect(screen.getByLabelText('Expiry review reason')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Record expiry review' })).toBeInTheDocument();
    expect(screen.getByText(/BES-BLRFLAGSHIP-0001 :: BATCH-A :: OPEN/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Record expiry review' }));

    expect(workspace.recordBatchExpirySession).toHaveBeenCalledTimes(1);
  });

  test('renders reviewed-session approval controls and latest approved write-off', () => {
    const workspace = buildWorkspace({
      activeBatchExpirySession: {
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
        note: 'Shelf check',
        review_note: null,
      },
      expiryReviewNote: 'Approved after shelf review',
      latestBatchWriteOff: {
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
      batchExpiryBoard: {
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
            note: 'Shelf check',
            review_note: null,
          },
        ],
      },
    });

    render(<StoreBatchExpirySection workspace={workspace} />);

    expect(screen.getByText('Review expiry session')).toBeInTheDocument();
    expect(screen.getByLabelText('Expiry review note')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Approve expiry session' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Cancel expiry session' })).toBeInTheDocument();
    expect(screen.getByText('Latest expiry write-off')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Approve expiry session' }));
    fireEvent.click(screen.getByRole('button', { name: 'Cancel expiry session' }));

    expect(workspace.approveBatchExpirySession).toHaveBeenCalledTimes(1);
    expect(workspace.cancelBatchExpirySession).toHaveBeenCalledTimes(1);
  });
});
