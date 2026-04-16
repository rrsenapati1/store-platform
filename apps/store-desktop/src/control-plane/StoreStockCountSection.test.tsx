/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';
import { StoreStockCountSection } from './StoreStockCountSection';
import type { StoreRuntimeWorkspaceState } from './useStoreRuntimeWorkspace';

function buildWorkspace(overrides: Partial<StoreRuntimeWorkspaceState> = {}): StoreRuntimeWorkspaceState {
  return {
    isBusy: false,
    isSessionLive: true,
    branchId: 'branch-1',
    stockCountBoard: null,
    activeStockCountSession: null,
    latestApprovedStockCount: null,
    selectedStockCountProductId: 'product-1',
    stockCountNote: '',
    blindCountedQuantity: '10',
    stockCountReviewNote: '',
    loadStockCountBoard: vi.fn(async () => {}),
    createStockCountSession: vi.fn(async () => {}),
    recordStockCountSession: vi.fn(async () => {}),
    approveStockCountSession: vi.fn(async () => {}),
    cancelStockCountSession: vi.fn(async () => {}),
    setSelectedStockCountProductId: vi.fn(),
    setStockCountNote: vi.fn(),
    setBlindCountedQuantity: vi.fn(),
    setStockCountReviewNote: vi.fn(),
    ...overrides,
  } as unknown as StoreRuntimeWorkspaceState;
}

describe('store stock count section', () => {
  test('keeps expected quantity hidden while session is open and reveals it when counted', () => {
    const openWorkspace = buildWorkspace({
      stockCountBoard: {
        branch_id: 'branch-1',
        open_count: 1,
        counted_count: 0,
        approved_count: 0,
        canceled_count: 0,
        records: [
          {
            stock_count_session_id: 'scs-1',
            session_number: 'SCS-BLRFLAGSHIP-0001',
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            status: 'OPEN',
            expected_quantity: null,
            counted_quantity: null,
            variance_quantity: null,
            note: 'Aisle recount',
            review_note: null,
          },
        ],
      },
      activeStockCountSession: {
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
      },
    });

    const { rerender } = render(<StoreStockCountSection workspace={openWorkspace} />);

    expect(screen.queryByText('Expected quantity')).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Record blind count' }));
    expect(openWorkspace.recordStockCountSession).toHaveBeenCalledTimes(1);

    const countedWorkspace = buildWorkspace({
      stockCountBoard: {
        branch_id: 'branch-1',
        open_count: 0,
        counted_count: 1,
        approved_count: 0,
        canceled_count: 0,
        records: [
          {
            stock_count_session_id: 'scs-1',
            session_number: 'SCS-BLRFLAGSHIP-0001',
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            status: 'COUNTED',
            expected_quantity: 12,
            counted_quantity: 10,
            variance_quantity: -2,
            note: 'Aisle recount',
            review_note: null,
          },
        ],
      },
      activeStockCountSession: {
        id: 'scs-1',
        tenant_id: 'tenant-acme',
        branch_id: 'branch-1',
        product_id: 'product-1',
        session_number: 'SCS-BLRFLAGSHIP-0001',
        status: 'COUNTED',
        expected_quantity: 12,
        counted_quantity: 10,
        variance_quantity: -2,
        note: 'Aisle recount',
        review_note: null,
      },
    });

    rerender(<StoreStockCountSection workspace={countedWorkspace} />);

    expect(screen.getByText('Expected quantity')).toBeInTheDocument();
    expect(screen.getByText('Variance quantity')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Approve stock count session' })).toBeInTheDocument();
  });

  test('renders board-driven product selection and create-session controls', () => {
    const workspace = buildWorkspace({
      selectedStockCountProductId: '',
      stockCountBoard: {
        branch_id: 'branch-1',
        open_count: 0,
        counted_count: 0,
        approved_count: 0,
        canceled_count: 0,
        records: [
          {
            stock_count_session_id: 'scs-1',
            session_number: 'SCS-BLRFLAGSHIP-0001',
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            status: 'APPROVED',
            expected_quantity: 12,
            counted_quantity: 10,
            variance_quantity: -2,
            note: 'Prior count',
            review_note: 'Approved',
          },
        ],
      },
    });

    render(<StoreStockCountSection workspace={workspace} />);

    fireEvent.click(screen.getByRole('button', { name: 'Select Classic Tea' }));
    expect(workspace.setSelectedStockCountProductId).toHaveBeenCalledWith('product-1');

    expect(screen.getByRole('button', { name: 'Open stock count session' })).toBeDisabled();
  });

  test('shows latest approved stock count only after approval', () => {
    const workspace = buildWorkspace({
      latestApprovedStockCount: {
        id: 'count-1',
        tenant_id: 'tenant-acme',
        branch_id: 'branch-1',
        product_id: 'product-1',
        counted_quantity: 10,
        expected_quantity: 12,
        variance_quantity: -2,
        note: 'Blind count complete',
        closing_stock: 10,
      },
    });

    render(<StoreStockCountSection workspace={workspace} />);

    expect(screen.getByText('Latest approved stock count')).toBeInTheDocument();
    expect(screen.getByText('Closing stock')).toBeInTheDocument();
    expect(screen.getAllByText('10')).toHaveLength(2);
  });
});
