/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { OwnerAttendanceSection } from './OwnerAttendanceSection';

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

describe('owner attendance section', () => {
  const originalFetch = globalThis.fetch;
  let attendanceSessions: Array<{
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
    attendance_number: string;
    clock_in_note?: string | null;
    clock_out_note?: string | null;
    force_close_reason?: string | null;
    opened_at: string;
    closed_at?: string | null;
    last_activity_at?: string | null;
    linked_cashier_sessions_count: number;
  }>;

  beforeEach(() => {
    attendanceSessions = [
      {
        id: 'attendance-session-open',
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
        attendance_number: 'ATTD-BLRFLAGSHIP-0002',
        clock_in_note: 'Morning shift',
        clock_out_note: null,
        force_close_reason: null,
        opened_at: '2026-04-18T03:30:00Z',
        closed_at: null,
        last_activity_at: '2026-04-18T05:10:00Z',
        linked_cashier_sessions_count: 1,
      },
      {
        id: 'attendance-session-closed',
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
        attendance_number: 'ATTD-BLRFLAGSHIP-0001',
        clock_in_note: 'Evening shift',
        clock_out_note: 'Shift complete',
        force_close_reason: null,
        opened_at: '2026-04-17T11:00:00Z',
        closed_at: '2026-04-17T19:00:00Z',
        last_activity_at: '2026-04-17T18:58:00Z',
        linked_cashier_sessions_count: 1,
      },
    ];

    globalThis.fetch = vi.fn(async (input, init) => {
      const url = String(input);
      const method = init?.method ?? 'GET';

      if (url.endsWith('/attendance-sessions') && method === 'GET') {
        return jsonResponse({ records: attendanceSessions }) as never;
      }
      if (url.includes('/attendance-sessions/attendance-session-open/force-close') && method === 'POST') {
        const payload = JSON.parse(String(init?.body ?? '{}'));
        const updated = {
          ...attendanceSessions[0],
          status: 'FORCED_CLOSED',
          closed_by_user_id: 'owner-user-1',
          closed_at: '2026-04-18T05:20:00Z',
          force_close_reason: payload.reason,
        };
        attendanceSessions = [updated, attendanceSessions[1]];
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

  test('loads active and historical attendance sessions and force-closes the selected open session', async () => {
    render(
      <OwnerAttendanceSection
        accessToken="session-owner"
        tenantId="tenant-acme"
        branchId="branch-1"
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Refresh attendance sessions' }));

    expect(await screen.findByText('Active attendance')).toBeInTheDocument();
    expect(screen.getByText('Attendance history')).toBeInTheDocument();
    expect(screen.getByText('ATTD-BLRFLAGSHIP-0002 :: Counter Cashier :: BLR-POS-01')).toBeInTheDocument();
    expect(screen.getByText('ATTD-BLRFLAGSHIP-0001 :: Evening Cashier :: BLR-POS-02')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Force-close reason'), {
      target: { value: 'Missed clock-out on abandoned terminal' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Force-close selected attendance' }));

    await waitFor(() => {
      expect(screen.getAllByText('FORCED_CLOSED').length).toBeGreaterThan(0);
    });
    expect(screen.queryByText('Active attendance')).not.toBeInTheDocument();
    expect(screen.getByText('Missed clock-out on abandoned terminal')).toBeInTheDocument();
  });
});
