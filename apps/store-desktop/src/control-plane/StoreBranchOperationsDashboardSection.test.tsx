/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import type { StoreRuntimeWorkspaceState } from './useStoreRuntimeWorkspace';
import { StoreBranchOperationsDashboardSection } from './StoreBranchOperationsDashboardSection';

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

function buildWorkspace(): StoreRuntimeWorkspaceState {
  return {
    accessToken: 'session-cashier',
    tenantId: 'tenant-acme',
    branchId: 'branch-1',
    isSessionLive: true,
    isBusy: false,
    sales: [
      {
        sale_id: 'sale-1',
        invoice_number: 'INV-101',
        customer_name: 'Walk In',
        invoice_kind: 'TAX_INVOICE',
        irn_status: 'NOT_REQUIRED',
        payment_method: 'Cash',
        grand_total: 540,
        promotion_discount_amount: 0,
        store_credit_amount: 0,
        loyalty_points_redeemed: 0,
        loyalty_discount_amount: 0,
        loyalty_points_earned: 5,
        issued_on: '2026-04-18',
      },
      {
        sale_id: 'sale-2',
        invoice_number: 'INV-102',
        customer_name: 'Walk In',
        invoice_kind: 'TAX_INVOICE',
        irn_status: 'NOT_REQUIRED',
        payment_method: 'UPI',
        grand_total: 210,
        promotion_discount_amount: 0,
        store_credit_amount: 0,
        loyalty_points_redeemed: 0,
        loyalty_discount_amount: 0,
        loyalty_points_earned: 2,
        issued_on: '2026-04-18',
      },
    ],
    activeShiftSession: {
      id: 'shift-1',
      tenant_id: 'tenant-acme',
      branch_id: 'branch-1',
      status: 'OPEN',
      shift_number: 'SHIFT-001',
      shift_name: 'Morning shift',
      opened_at: '2026-04-18T08:00:00Z',
      linked_attendance_sessions_count: 2,
      linked_cashier_sessions_count: 1,
    },
    attendanceSessions: [
      {
        id: 'attendance-1',
        tenant_id: 'tenant-acme',
        branch_id: 'branch-1',
        device_registration_id: 'device-1',
        staff_profile_id: 'staff-1',
        runtime_user_id: 'runtime-user-1',
        opened_by_user_id: 'user-1',
        status: 'OPEN',
        session_number: 'ATT-001',
        opened_at: '2026-04-18T08:02:00Z',
        linked_cashier_sessions_count: 1,
        shift_session_id: 'shift-1',
      },
      {
        id: 'attendance-2',
        tenant_id: 'tenant-acme',
        branch_id: 'branch-1',
        device_registration_id: 'device-2',
        staff_profile_id: 'staff-2',
        runtime_user_id: 'runtime-user-2',
        opened_by_user_id: 'user-2',
        status: 'OPEN',
        session_number: 'ATT-002',
        opened_at: '2026-04-18T08:05:00Z',
        linked_cashier_sessions_count: 0,
        shift_session_id: 'shift-1',
      },
    ],
    cashierSessions: [
      {
        id: 'cashier-1',
        tenant_id: 'tenant-acme',
        branch_id: 'branch-1',
        attendance_session_id: 'attendance-1',
        device_registration_id: 'device-1',
        staff_profile_id: 'staff-1',
        runtime_user_id: 'runtime-user-1',
        opened_by_user_id: 'user-1',
        status: 'OPEN',
        session_number: 'CS-001',
        opening_float_amount: 500,
        opened_at: '2026-04-18T08:15:00Z',
        linked_sales_count: 2,
        linked_returns_count: 0,
        gross_billed_amount: 750,
      },
    ],
    branchRuntimePolicy: {
      require_assigned_staff_for_device: true,
      require_attendance_for_cashier: true,
      require_shift_for_attendance: true,
      allow_offline_sales: true,
      max_pending_offline_sales: 25,
    },
    runtimeHeartbeat: {
      device_id: 'device-1',
      status: 'online',
      last_seen_at: '2026-04-18T09:15:00Z',
      queued_job_count: 1,
    },
    pendingOfflineSaleCount: 1,
    pendingMutationCount: 2,
    offlineConflictCount: 0,
    offlineContinuityReady: true,
    offlineContinuityMessage: 'Offline continuity ready',
    runtimeHubServiceState: 'running',
    runtimeBindingStatus: 'BOUND',
  } as unknown as StoreRuntimeWorkspaceState;
}

describe('store branch operations dashboard section', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    globalThis.fetch = vi.fn(async (input) => {
      const url = String(input);
      if (url.includes('/replenishment-board')) {
        return jsonResponse({
          branch_id: 'branch-1',
          low_stock_count: 3,
          adequate_count: 11,
          records: [
            {
              product_id: 'product-tea',
              product_name: 'Masala Tea',
              sku_code: 'TEA-001',
              availability_status: 'LOW',
              stock_on_hand: 2,
              reorder_point: 6,
              target_stock: 12,
              suggested_reorder_quantity: 10,
              replenishment_status: 'LOW_STOCK',
            },
          ],
        }) as never;
      }
      if (url.includes('/restock-board')) {
        return jsonResponse({
          branch_id: 'branch-1',
          open_count: 2,
          picked_count: 1,
          completed_count: 4,
          canceled_count: 0,
          records: [
            {
              restock_task_id: 'restock-1',
              task_number: 'RST-001',
              product_id: 'product-tea',
              product_name: 'Masala Tea',
              sku_code: 'TEA-001',
              status: 'OPEN',
              stock_on_hand_snapshot: 2,
              reorder_point_snapshot: 6,
              target_stock_snapshot: 12,
              suggested_quantity_snapshot: 10,
              requested_quantity: 8,
              has_active_task: true,
            },
          ],
        }) as never;
      }
      if (url.includes('/receiving-board')) {
        return jsonResponse({
          branch_id: 'branch-1',
          blocked_count: 1,
          ready_count: 2,
          received_count: 5,
          received_with_variance_count: 1,
          records: [
            {
              purchase_order_id: 'po-1',
              purchase_order_number: 'PO-101',
              supplier_name: 'Metro Foods',
              approval_status: 'APPROVED',
              receiving_status: 'READY',
              can_receive: true,
            },
          ],
        }) as never;
      }
      if (url.includes('/stock-count-board')) {
        return jsonResponse({
          branch_id: 'branch-1',
          open_count: 1,
          counted_count: 1,
          approved_count: 3,
          canceled_count: 0,
          records: [
            {
              stock_count_session_id: 'count-1',
              session_number: 'CNT-001',
              product_id: 'product-tea',
              product_name: 'Masala Tea',
              sku_code: 'TEA-001',
              status: 'OPEN',
            },
          ],
        }) as never;
      }
      if (url.includes('/batch-expiry-report')) {
        return jsonResponse({
          branch_id: 'branch-1',
          tracked_lot_count: 6,
          expiring_soon_count: 2,
          expired_count: 1,
          untracked_stock_quantity: 0,
          records: [
            {
              batch_lot_id: 'lot-1',
              product_id: 'product-milk',
              product_name: 'Fresh Milk',
              batch_number: 'MILK-001',
              expiry_date: '2026-04-20',
              days_to_expiry: 2,
              received_quantity: 20,
              written_off_quantity: 0,
              remaining_quantity: 20,
              status: 'EXPIRING_SOON',
            },
          ],
        }) as never;
      }
      throw new Error(`Unexpected fetch: ${url}`);
    }) as typeof fetch;
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  test('renders branch manager posture and loads stock-operation exceptions', async () => {
    render(<StoreBranchOperationsDashboardSection workspace={buildWorkspace()} />);

    expect(screen.getByText('Branch operations dashboard')).toBeInTheDocument();
    expect(screen.getByText('Today sales')).toBeInTheDocument();
    expect(screen.getByText('750')).toBeInTheDocument();
    expect(screen.getByText('Morning shift')).toBeInTheDocument();
    expect(screen.getByText(/Offline continuity ready/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Refresh dashboard' }));

    expect(await screen.findByText('Low-stock products')).toBeInTheDocument();
    expect(screen.getByText('Receiving ready')).toBeInTheDocument();
    expect(screen.getByText('Expiring soon lots')).toBeInTheDocument();
    expect(screen.getByText(/Masala Tea :: LOW_STOCK/)).toBeInTheDocument();
    expect(screen.getByText(/Metro Foods :: PO-101 :: READY/)).toBeInTheDocument();
    expect(screen.getByText(/Fresh Milk :: MILK-001 :: EXPIRING_SOON/)).toBeInTheDocument();
  });
});
