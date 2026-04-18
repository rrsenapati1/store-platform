/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import type { ControlPlaneBranchRecord } from '@store/types';
import { OwnerBranchPerformanceSection } from './OwnerBranchPerformanceSection';

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

describe('owner branch performance section', () => {
  const originalFetch = globalThis.fetch;
  const branches: ControlPlaneBranchRecord[] = [
    {
      branch_id: 'branch-1',
      tenant_id: 'tenant-acme',
      name: 'Bengaluru Flagship',
      code: 'blr-flagship',
      gstin: '29ABCDE1234F1Z5',
      status: 'ACTIVE',
    },
    {
      branch_id: 'branch-2',
      tenant_id: 'tenant-acme',
      name: 'Indiranagar Express',
      code: 'blr-indiranagar',
      gstin: '29ABCDE1234F1Z6',
      status: 'ACTIVE',
    },
  ];

  beforeEach(() => {
    globalThis.fetch = vi.fn(async (input) => {
      const url = String(input);
      if (url.includes('/branches/branch-1/management-dashboard')) {
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
            {
              product_id: 'product-rice',
              product_name: 'Daily Rice',
              sku_code: 'RICE-001',
              stock_on_hand: 4,
              reorder_point: 12,
              target_stock: 24,
              suggested_reorder_quantity: 20,
              open_restock_quantity: 0,
              open_purchase_order_quantity: 10,
              net_recommended_order_quantity: 10,
              latest_purchase_unit_cost: 32,
              estimated_purchase_cost: 320,
              recommendation_status: 'ORDER_NOW',
            },
          ],
        }) as never;
      }
      if (url.includes('/branches/branch-2/management-dashboard')) {
        return jsonResponse({
          branch_id: 'branch-2',
          branch_name: 'Indiranagar Express',
          as_of_date: '2026-04-18',
          trade: {
            sales_today_total: 320,
            sales_today_count: 2,
            sales_7d_total: 980,
            sales_7d_count: 7,
            returns_7d_total: 0,
            returns_7d_count: 0,
            average_basket_value_7d: 140,
          },
          workforce: {
            open_shift_count: 1,
            open_attendance_count: 2,
            open_cashier_count: 1,
          },
          operations: {
            low_stock_count: 0,
            restock_open_count: 0,
            receiving_ready_count: 0,
            receiving_variance_count: 0,
            stock_count_open_count: 0,
            expiring_soon_count: 0,
            supplier_blocker_count: 0,
            overdue_supplier_invoice_count: 0,
            queued_operations_job_count: 0,
          },
          procurement: {
            approval_pending_count: 0,
            approved_pending_receipt_count: 0,
            approved_pending_receipt_total: 0,
            outstanding_payables_total: 180,
            blocked_release_total: 0,
          },
          recommendations: [],
        }) as never;
      }
      throw new Error(`Unexpected fetch: ${url}`);
    }) as typeof fetch;
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  test('loads branch performance dashboards and aggregates management totals', async () => {
    render(
      <OwnerBranchPerformanceSection
        accessToken="owner-session"
        tenantId="tenant-acme"
        branches={branches}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Load branch performance' }));

    expect(await screen.findByText('Sales 7 days')).toBeInTheDocument();
    expect(screen.getByText('3380')).toBeInTheDocument();
    expect(screen.getByText('At-risk branches')).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText('Immediate reorder spend')).toBeInTheDocument();
    expect(screen.getByText('720')).toBeInTheDocument();
    expect(screen.getByText(/Bengaluru Flagship :: sales 2400 :: reorder spend 720/)).toBeInTheDocument();
    expect(screen.getByText(/Indiranagar Express :: sales 980 :: reorder spend 0/)).toBeInTheDocument();
  });
});
