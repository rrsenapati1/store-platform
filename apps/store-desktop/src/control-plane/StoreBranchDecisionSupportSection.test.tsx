/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { StoreBranchDecisionSupportSection } from './StoreBranchDecisionSupportSection';

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

describe('store branch decision support section', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    globalThis.fetch = vi.fn(async (input) => {
      const url = String(input);
      if (url.includes('/management-dashboard')) {
        return jsonResponse({
          branch_id: 'branch-1',
          branch_name: 'Bengaluru Flagship',
          as_of_date: '2026-04-18',
          trade: {
            sales_today_total: 780,
            sales_today_count: 3,
            sales_7d_total: 2400,
            sales_7d_count: 14,
            returns_7d_total: 105,
            returns_7d_count: 1,
            average_basket_value_7d: 171.43,
          },
          workforce: {
            open_shift_count: 1,
            open_attendance_count: 4,
            open_cashier_count: 2,
          },
          operations: {
            low_stock_count: 3,
            restock_open_count: 2,
            receiving_ready_count: 1,
            receiving_variance_count: 0,
            stock_count_open_count: 1,
            expiring_soon_count: 2,
            supplier_blocker_count: 0,
            overdue_supplier_invoice_count: 1,
            queued_operations_job_count: 0,
          },
          procurement: {
            approval_pending_count: 1,
            approved_pending_receipt_count: 2,
            approved_pending_receipt_total: 640,
            outstanding_payables_total: 325,
            blocked_release_total: 0,
          },
          recommendations: [
            {
              product_id: 'product-tea',
              product_name: 'Masala Tea',
              sku_code: 'TEA-001',
              stock_on_hand: 2,
              reorder_point: 10,
              target_stock: 20,
              suggested_reorder_quantity: 18,
              open_restock_quantity: 3,
              open_purchase_order_quantity: 5,
              net_recommended_order_quantity: 10,
              latest_purchase_unit_cost: 40,
              estimated_purchase_cost: 400,
              recommendation_status: 'ORDER_NOW',
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

  test('loads branch purchase and replenishment decision support', async () => {
    render(
      <StoreBranchDecisionSupportSection
        accessToken="runtime-session"
        tenantId="tenant-acme"
        branchId="branch-1"
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Load decision support' }));

    expect(await screen.findByText('Immediate reorder quantity')).toBeInTheDocument();
    expect(screen.getByText('10')).toBeInTheDocument();
    expect(screen.getByText('Approved pending receipt')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('Outstanding payables')).toBeInTheDocument();
    expect(screen.getByText('325')).toBeInTheDocument();
    expect(screen.getByText(/Masala Tea :: reorder 10 :: spend 400/)).toBeInTheDocument();
  });
});
