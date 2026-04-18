/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import type { ControlPlaneShiftSession } from '@store/types';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { OwnerShiftSessionSection } from './OwnerShiftSessionSection';

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

describe('owner shift session section', () => {
  const originalFetch = globalThis.fetch;
  let shiftSessions: ControlPlaneShiftSession[] = [
    {
      id: 'shift-session-open',
      tenant_id: 'tenant-acme',
      branch_id: 'branch-1',
      shift_number: 'SHIFT-BLRFLAGSHIP-0002',
      shift_name: 'Morning counter shift',
      status: 'OPEN',
      opening_note: 'Counter ready',
      closing_note: null,
      force_close_reason: null,
      opened_at: '2026-04-18T03:30:00Z',
      closed_at: null,
      linked_attendance_sessions_count: 1,
      linked_cashier_sessions_count: 1,
    },
    {
      id: 'shift-session-closed',
      tenant_id: 'tenant-acme',
      branch_id: 'branch-1',
      shift_number: 'SHIFT-BLRFLAGSHIP-0001',
      shift_name: 'Evening counter shift',
      status: 'CLOSED',
      opening_note: 'Evening open',
      closing_note: 'Closed cleanly',
      force_close_reason: null,
      opened_at: '2026-04-17T11:00:00Z',
      closed_at: '2026-04-17T19:00:00Z',
      linked_attendance_sessions_count: 1,
      linked_cashier_sessions_count: 1,
    },
  ];

  beforeEach(() => {
    globalThis.fetch = vi.fn(async (input, init) => {
      const url = String(input);
      const method = init?.method ?? 'GET';

      if (url.endsWith('/shift-sessions') && method === 'GET') {
        return jsonResponse({ records: shiftSessions }) as never;
      }
      if (url.includes('/shift-sessions/shift-session-open/force-close') && method === 'POST') {
        const payload = JSON.parse(String(init?.body ?? '{}'));
        shiftSessions = [
          {
            ...shiftSessions[0],
            status: 'FORCED_CLOSED',
            closed_at: '2026-04-18T05:20:00Z',
            force_close_reason: payload.reason,
          },
          shiftSessions[1],
        ];
        return jsonResponse(shiftSessions[0]) as never;
      }

      throw new Error(`Unexpected fetch call: ${method} ${url}`);
    }) as typeof fetch;
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
    cleanup();
    vi.restoreAllMocks();
  });

  test('loads shift sessions and force-closes the selected open shift', async () => {
    render(
      <OwnerShiftSessionSection
        accessToken="session-owner"
        tenantId="tenant-acme"
        branchId="branch-1"
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Refresh shift sessions' }));

    expect(await screen.findByText('Active shifts')).toBeInTheDocument();
    expect(screen.getByText('Shift history')).toBeInTheDocument();
    expect(screen.getByText('SHIFT-BLRFLAGSHIP-0002 :: Morning counter shift :: attendance 1 :: cashier 1')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Force-close reason'), {
      target: { value: 'Operator left terminal open across handoff' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Force-close selected shift' }));

    await waitFor(() => {
      expect(screen.getAllByText('FORCED_CLOSED').length).toBeGreaterThan(0);
    });
    expect(screen.getByText('Operator left terminal open across handoff')).toBeInTheDocument();
  });
});
