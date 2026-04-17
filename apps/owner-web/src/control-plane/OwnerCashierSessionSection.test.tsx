/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { OwnerCashierSessionSection } from './OwnerCashierSessionSection';

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

describe('owner cashier session section', () => {
  const originalFetch = globalThis.fetch;
  let cashierSessions: Array<{
    id: string;
    tenant_id: string;
    branch_id: string;
    device_registration_id: string;
    device_name?: string | null;
    device_code?: string | null;
    staff_profile_id: string;
    staff_full_name?: string | null;
    runtime_user_id: string;
    opened_by_user_id: string;
    closed_by_user_id?: string | null;
    status: string;
    session_number: string;
    opening_float_amount: number;
    opening_note?: string | null;
    closing_note?: string | null;
    force_close_reason?: string | null;
    opened_at: string;
    closed_at?: string | null;
    last_activity_at?: string | null;
    linked_sales_count: number;
    linked_returns_count: number;
    gross_billed_amount: number;
  }>;

  beforeEach(() => {
    cashierSessions = [
      {
        id: 'cashier-session-open',
        tenant_id: 'tenant-acme',
        branch_id: 'branch-1',
        device_registration_id: 'device-1',
        device_name: 'Counter Desktop 1',
        device_code: 'BLR-POS-01',
        staff_profile_id: 'staff-1',
        staff_full_name: 'Counter Cashier',
        runtime_user_id: 'user-cashier',
        opened_by_user_id: 'user-cashier',
        closed_by_user_id: null,
        status: 'OPEN',
        session_number: 'CS-BLRFLAGSHIP-0002',
        opening_float_amount: 500,
        opening_note: 'Morning shift',
        closing_note: null,
        force_close_reason: null,
        opened_at: '2026-04-18T03:30:00Z',
        closed_at: null,
        last_activity_at: '2026-04-18T05:10:00Z',
        linked_sales_count: 3,
        linked_returns_count: 1,
        gross_billed_amount: 1450,
      },
      {
        id: 'cashier-session-closed',
        tenant_id: 'tenant-acme',
        branch_id: 'branch-1',
        device_registration_id: 'device-2',
        device_name: 'Counter Desktop 2',
        device_code: 'BLR-POS-02',
        staff_profile_id: 'staff-2',
        staff_full_name: 'Evening Cashier',
        runtime_user_id: 'user-cashier-2',
        opened_by_user_id: 'user-cashier-2',
        closed_by_user_id: 'user-cashier-2',
        status: 'CLOSED',
        session_number: 'CS-BLRFLAGSHIP-0001',
        opening_float_amount: 450,
        opening_note: 'Evening shift',
        closing_note: 'Closed cleanly',
        force_close_reason: null,
        opened_at: '2026-04-17T11:00:00Z',
        closed_at: '2026-04-17T19:00:00Z',
        last_activity_at: '2026-04-17T18:58:00Z',
        linked_sales_count: 12,
        linked_returns_count: 0,
        gross_billed_amount: 5320,
      },
    ];

    globalThis.fetch = vi.fn(async (input, init) => {
      const url = String(input);
      const method = init?.method ?? 'GET';

      if (url.endsWith('/cashier-sessions') && method === 'GET') {
        return jsonResponse({ records: cashierSessions }) as never;
      }
      if (url.includes('/cashier-sessions/cashier-session-open/force-close') && method === 'POST') {
        const payload = JSON.parse(String(init?.body ?? '{}'));
        const updated = {
          ...cashierSessions[0],
          status: 'FORCED_CLOSED',
          closed_by_user_id: 'owner-user-1',
          closed_at: '2026-04-18T05:20:00Z',
          force_close_reason: payload.reason,
        };
        cashierSessions = [updated, cashierSessions[1]];
        return jsonResponse(updated) as never;
      }

      throw new Error(`Unexpected fetch call: ${method} ${url}`);
    }) as typeof fetch;
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
    cleanup();
    vi.restoreAllMocks();
  });

  test('loads active and historical cashier sessions and force-closes the selected open session', async () => {
    render(
      <OwnerCashierSessionSection
        accessToken="session-owner"
        tenantId="tenant-acme"
        branchId="branch-1"
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Refresh cashier sessions' }));

    expect(await screen.findByText('Active sessions')).toBeInTheDocument();
    expect(screen.getByText('Session history')).toBeInTheDocument();
    expect(screen.getByText('CS-BLRFLAGSHIP-0002 :: Counter Cashier :: BLR-POS-01')).toBeInTheDocument();
    expect(screen.getByText('CS-BLRFLAGSHIP-0001 :: Evening Cashier :: BLR-POS-02')).toBeInTheDocument();
    expect(screen.getByText('Gross billed amount')).toBeInTheDocument();
    expect(screen.getByText('1450')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Force-close reason'), {
      target: { value: 'Terminal left signed in after shift handoff' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Force-close selected session' }));

    await waitFor(() => {
      expect(screen.getAllByText('FORCED_CLOSED').length).toBeGreaterThan(0);
    });
    expect(screen.queryByText('Active sessions')).not.toBeInTheDocument();
    expect(screen.getByText('Terminal left signed in after shift handoff')).toBeInTheDocument();

    await waitFor(() => {
      const forceCloseCall = vi.mocked(globalThis.fetch).mock.calls.find(
        ([url, init]) =>
          String(url).includes('/cashier-sessions/cashier-session-open/force-close')
          && init?.method === 'POST',
      );
      expect(forceCloseCall).toBeDefined();
      expect(JSON.parse(String(forceCloseCall?.[1]?.body ?? '{}'))).toMatchObject({
        reason: 'Terminal left signed in after shift handoff',
      });
    });
  });
});
