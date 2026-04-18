/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { OwnerWorkforceAuditSection } from './OwnerWorkforceAuditSection';

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

describe('owner workforce audit section', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    globalThis.fetch = vi.fn(async (input, init) => {
      const url = String(input);
      const method = init?.method ?? 'GET';

      if (url.endsWith('/workforce-audit-events') && method === 'GET') {
        return jsonResponse({
          records: [
            {
              id: 'audit-1',
              action: 'shift_session.opened',
              entity_type: 'shift_session',
              entity_id: 'shift-session-open',
              tenant_id: 'tenant-acme',
              branch_id: 'branch-1',
              created_at: '2026-04-18T03:45:00Z',
              payload: { shift_number: 'SHIFT-BLRFLAGSHIP-0002' },
            },
          ],
        }) as never;
      }
      if (url.endsWith('/workforce-audit-export') && method === 'GET') {
        return jsonResponse({
          filename: 'workforce-audit-branch-1.csv',
          content_type: 'text/csv',
          content: 'created_at,action,entity_type,entity_id,branch_id,payload\n2026-04-18T03:45:00Z,shift_session.opened,shift_session,shift-session-open,branch-1,"{\\"shift_number\\": \\"SHIFT-BLRFLAGSHIP-0002\\"}"',
        }) as never;
      }

      throw new Error(`Unexpected fetch call: ${method} ${url}`);
    }) as typeof fetch;
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
    cleanup();
    vi.restoreAllMocks();
  });

  test('loads workforce audit events and previews the CSV export', async () => {
    render(
      <OwnerWorkforceAuditSection
        accessToken="session-owner"
        tenantId="tenant-acme"
        branchId="branch-1"
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Refresh workforce audit' }));
    expect(await screen.findByText('shift_session.opened :: shift_session :: shift-session-open')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Export workforce audit CSV' }));
    await waitFor(() => {
      expect(screen.getByText('workforce-audit-branch-1.csv')).toBeInTheDocument();
    });
    expect(screen.getAllByText(/shift_session\.opened/).length).toBeGreaterThan(0);
  });
});
