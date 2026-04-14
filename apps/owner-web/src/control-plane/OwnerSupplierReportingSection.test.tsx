/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { OwnerSupplierReportingSection } from './OwnerSupplierReportingSection';

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

describe('owner supplier reporting section', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    const responses = [
      jsonResponse({
        branch_id: 'branch-1',
        invoiced_total: 450,
        credit_note_total: 28,
        paid_total: 100,
        outstanding_total: 322,
        snapshot_status: 'CURRENT',
        records: [{ supplier_name: 'Paper Supply Co', purchase_invoice_number: 'PINV-001', outstanding_total: 195 }],
      }),
      jsonResponse({
        branch_id: 'branch-1',
        as_of_date: '2026-04-14',
        open_invoice_count: 3,
        current_total: 59,
        days_1_30_total: 68,
        days_31_60_total: 195,
        days_61_plus_total: 0,
        outstanding_total: 322,
        records: [{ supplier_name: 'Paper Supply Co', purchase_invoice_number: 'PINV-001', aging_bucket: '31_60_DAYS', outstanding_total: 195 }],
      }),
      jsonResponse({
        branch_id: 'branch-1',
        as_of_date: '2026-04-14',
        supplier_count: 3,
        open_supplier_count: 3,
        outstanding_total: 322,
        records: [{ supplier_id: 'supplier-1', supplier_name: 'Paper Supply Co', invoice_count: 1, open_invoice_count: 1, invoiced_total: 250, credit_note_total: 28, paid_total: 27, outstanding_total: 195 }],
      }),
      jsonResponse({
        branch_id: 'branch-1',
        as_of_date: '2026-04-14',
        overdue_invoice_count: 1,
        overdue_total: 195,
        due_today_total: 68,
        due_in_7_days_total: 59,
        due_in_8_30_days_total: 0,
        due_later_total: 0,
        records: [{ supplier_name: 'Paper Supply Co', purchase_invoice_number: 'PINV-001', due_status: 'OVERDUE', outstanding_total: 195, purchase_invoice_id: 'invoice-1', supplier_id: 'supplier-1', due_date: '2026-04-10' }],
      }),
      jsonResponse({
        branch_id: 'branch-1',
        as_of_date: '2026-04-14',
        open_count: 1,
        resolved_count: 1,
        overdue_open_count: 1,
        snapshot_status: 'STALE_REFRESH_QUEUED',
        snapshot_job_id: 'job-supplier-refresh-1',
        records: [{ dispute_id: 'dispute-1', supplier_id: 'supplier-1', supplier_name: 'Paper Supply Co', reference_type: 'goods_receipt', reference_number: 'GRN-001', dispute_type: 'SHORT_SUPPLY', status: 'OPEN', age_days: 10, overdue: true }],
      }),
      jsonResponse({
        branch_id: 'branch-1',
        as_of_date: '2026-04-14',
        supplier_count: 1,
        suppliers_with_open_disputes: 1,
        suppliers_with_overdue_disputes: 1,
        records: [{ supplier_id: 'supplier-1', supplier_name: 'Paper Supply Co', dispute_count: 2, open_count: 1, resolved_count: 1, overdue_open_count: 1, status: 'ATTENTION' }],
      }),
      jsonResponse({
        branch_id: 'branch-1',
        as_of_date: '2026-04-14',
        supplier_count: 3,
        overdue_total: 195,
        due_in_7_days_total: 127,
        outstanding_total: 322,
        records: [{ supplier_id: 'supplier-1', supplier_name: 'Paper Supply Co', outstanding_total: 195, overdue_total: 195, due_in_7_days_total: 0, risk_status: 'HIGH' }],
      }),
      jsonResponse({
        branch_id: 'branch-1',
        as_of_date: '2026-04-14',
        supplier_count: 3,
        hard_hold_count: 1,
        soft_hold_count: 2,
        blocked_release_now_total: 195,
        blocked_release_this_week_total: 127,
        blocked_outstanding_total: 322,
        records: [{ supplier_id: 'supplier-1', supplier_name: 'Paper Supply Co', hold_status: 'HARD_HOLD', open_dispute_count: 1, overdue_open_dispute_count: 1, outstanding_total: 195, release_now_total: 195, release_this_week_total: 0 }],
      }),
      jsonResponse({
        branch_id: 'branch-1',
        as_of_date: '2026-04-14',
        open_case_count: 3,
        finance_escalation_count: 1,
        owner_escalation_count: 2,
        stale_case_count: 0,
        branch_follow_up_count: 0,
        blocked_release_now_total: 195,
        blocked_release_this_week_total: 127,
        blocked_outstanding_total: 322,
        records: [{ dispute_id: 'dispute-1', supplier_id: 'supplier-1', supplier_name: 'Paper Supply Co', escalation_status: 'FINANCE_ESCALATION', escalation_target: 'finance_admin', blocked_release_now_total: 195, blocked_release_this_week_total: 0, age_days: 10 }],
      }),
      jsonResponse({
        branch_id: 'branch-1',
        supplier_count: 3,
        at_risk_count: 1,
        watch_count: 1,
        good_count: 1,
        records: [{ supplier_id: 'supplier-1', supplier_name: 'Paper Supply Co', approved_purchase_order_count: 1, received_purchase_order_count: 1, on_time_receipt_rate: 0.2, supplier_return_rate: 0.5, invoice_mismatch_rate: 0.5, average_receipt_delay_days: 4, performance_status: 'AT_RISK' }],
      }),
      jsonResponse({
        branch_id: 'branch-1',
        as_of_date: '2026-04-14',
        supplier_count: 2,
        payment_count: 2,
        paid_total: 150,
        recent_30_days_paid_total: 150,
        records: [{ supplier_id: 'supplier-1', supplier_name: 'Paper Supply Co', payment_count: 1, paid_total: 100, recent_30_days_paid_total: 100, average_payment_value: 100, outstanding_total: 195, last_payment_date: '2026-04-10', last_payment_method: 'bank_transfer', last_payment_amount: 100 }],
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

  test('loads supplier reporting summaries across the migrated control-plane routes', async () => {
    render(<OwnerSupplierReportingSection accessToken="session-owner" tenantId="tenant-acme" branchId="branch-1" />);

    fireEvent.click(screen.getByRole('button', { name: 'Load supplier reporting' }));

    expect(await screen.findByText('Outstanding payables')).toBeInTheDocument();
    expect(screen.getByText('Snapshot health')).toBeInTheDocument();
    expect(screen.getByText('1 refresh queued')).toBeInTheDocument();
    expect(screen.getByText('322')).toBeInTheDocument();
    expect(screen.getByText(/Paper Supply Co :: PINV-001 :: 195/)).toBeInTheDocument();
    expect(screen.getByText(/Paper Supply Co :: HARD_HOLD :: 195/)).toBeInTheDocument();
    expect(screen.getByText(/Paper Supply Co :: FINANCE_ESCALATION/)).toBeInTheDocument();
  });
});
