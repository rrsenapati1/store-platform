/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';
import { StoreRestockSection } from './StoreRestockSection';
import type { StoreRuntimeWorkspaceState } from './useStoreRuntimeWorkspace';

function buildWorkspace(overrides: Partial<StoreRuntimeWorkspaceState> = {}): StoreRuntimeWorkspaceState {
  return {
    isBusy: false,
    isSessionLive: true,
    latestScanLookup: {
      product_id: 'product-1',
      product_name: 'Classic Tea',
      sku_code: 'tea-classic-250g',
      barcode: 'ACMETEACLASSIC',
      selling_price: 89,
      stock_on_hand: 4,
      availability_status: 'ACTIVE',
    },
    branchCatalogItems: [
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
    restockBoard: {
      branch_id: 'branch-1',
      open_count: 1,
      picked_count: 0,
      completed_count: 0,
      canceled_count: 0,
      records: [
        {
          restock_task_id: 'restock-task-1',
          task_number: 'RST-BLRFLAGSHIP-0001',
          product_id: 'product-1',
          product_name: 'Classic Tea',
          sku_code: 'tea-classic-250g',
          status: 'OPEN',
          stock_on_hand_snapshot: 4,
          reorder_point_snapshot: 10,
          target_stock_snapshot: 24,
          suggested_quantity_snapshot: 20,
          requested_quantity: 12,
          picked_quantity: null,
          source_posture: 'BACKROOM_AVAILABLE',
          note: 'Aisle 2 shelf gap',
          completion_note: null,
          has_active_task: true,
        },
      ],
    },
    latestRestockTask: {
      id: 'restock-task-1',
      tenant_id: 'tenant-acme',
      branch_id: 'branch-1',
      product_id: 'product-1',
      task_number: 'RST-BLRFLAGSHIP-0001',
      status: 'OPEN',
      stock_on_hand_snapshot: 4,
      reorder_point_snapshot: 10,
      target_stock_snapshot: 24,
      suggested_quantity_snapshot: 20,
      requested_quantity: 12,
      picked_quantity: null,
      source_posture: 'BACKROOM_AVAILABLE',
      note: 'Aisle 2 shelf gap',
      completion_note: null,
    },
    restockRequestedQuantity: '12',
    restockPickedQuantity: '10',
    restockSourcePosture: 'BACKROOM_AVAILABLE',
    restockNote: 'Aisle 2 shelf gap',
    restockCompletionNote: '',
    replenishmentBoard: {
      branch_id: 'branch-1',
      low_stock_count: 1,
      adequate_count: 0,
      records: [
        {
          product_id: 'product-1',
          product_name: 'Classic Tea',
          sku_code: 'tea-classic-250g',
          availability_status: 'ACTIVE',
          stock_on_hand: 4,
          reorder_point: 10,
          target_stock: 24,
          suggested_reorder_quantity: 20,
          replenishment_status: 'LOW_STOCK',
        },
      ],
    },
    selectedRestockProductId: '',
    selectRestockProduct: vi.fn(),
    setRestockRequestedQuantity: vi.fn(),
    setRestockPickedQuantity: vi.fn(),
    setRestockSourcePosture: vi.fn(),
    setRestockNote: vi.fn(),
    setRestockCompletionNote: vi.fn(),
    loadRestockBoard: vi.fn(async () => {}),
    createRestockTaskForLatestScanLookup: vi.fn(async () => {}),
    pickActiveRestockTaskForLatestScanLookup: vi.fn(async () => {}),
    completeActiveRestockTaskForLatestScanLookup: vi.fn(async () => {}),
    cancelActiveRestockTaskForLatestScanLookup: vi.fn(async () => {}),
    ...overrides,
  } as unknown as StoreRuntimeWorkspaceState;
}

describe('store assisted restock section', () => {
  test('renders assisted restock posture for the latest scanned product', () => {
    render(<StoreRestockSection workspace={buildWorkspace()} />);

    expect(screen.getByText('Assisted restock')).toBeInTheDocument();
    expect(screen.getByText('Classic Tea')).toBeInTheDocument();
    expect(screen.getByText('Suggested restock -> 20')).toBeInTheDocument();
    expect(screen.getByText('Active restock task -> RST-BLRFLAGSHIP-0001')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Create restock task' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Mark active task picked' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Refresh restock board' })).toBeInTheDocument();
  });

  test('renders replenishment board visibility and selection controls', () => {
    const workspace = buildWorkspace({
      latestScanLookup: null,
      selectedRestockProductId: 'product-1',
    });

    render(<StoreRestockSection workspace={workspace} />);

    expect(screen.getByText('Replenishment board')).toBeInTheDocument();
    expect(screen.getByText(/Low-stock items -> 1/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Use Classic Tea' }));
    expect(workspace.selectRestockProduct).toHaveBeenCalledWith('product-1');
  });
});
