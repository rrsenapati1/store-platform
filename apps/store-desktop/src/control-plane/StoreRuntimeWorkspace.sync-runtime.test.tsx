/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { App } from '../App';

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

describe('store runtime sync monitoring', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    const responses = [
      jsonResponse({ access_token: 'session-cashier', token_type: 'Bearer' }),
      jsonResponse({
        user_id: 'user-cashier',
        email: 'cashier@acme.local',
        full_name: 'Counter Cashier',
        is_platform_admin: false,
        tenant_memberships: [],
        branch_memberships: [{ tenant_id: 'tenant-acme', branch_id: 'branch-1', role_name: 'cashier', status: 'ACTIVE' }],
      }),
      jsonResponse({
        id: 'tenant-acme',
        name: 'Acme Retail',
        slug: 'acme-retail',
        status: 'ACTIVE',
        onboarding_status: 'BRANCH_READY',
      }),
      jsonResponse({
        records: [{ branch_id: 'branch-1', tenant_id: 'tenant-acme', name: 'Bengaluru Flagship', code: 'blr-flagship', status: 'ACTIVE' }],
      }),
      jsonResponse({ records: [] }),
      jsonResponse({ records: [] }),
      jsonResponse({ records: [] }),
      jsonResponse({ records: [] }),
      jsonResponse({
        hub_device_id: 'device-hub-1',
        source_device_id: 'BLR-HUB-01',
        branch_cursor: 7,
        last_pull_cursor: 7,
        last_heartbeat_at: '2026-04-14T10:02:00',
        last_successful_push_at: '2026-04-14T10:01:00',
        last_successful_pull_at: '2026-04-14T10:02:30',
        last_successful_push_mutations: 2,
        last_idempotency_key: 'push-2',
        open_conflict_count: 1,
        failed_push_count: 1,
        connected_spoke_count: 4,
        local_outbox_depth: 3,
        pending_mutation_count: 3,
        oldest_unsynced_mutation_age_seconds: 180,
        runtime_state: 'DEGRADED',
        last_local_spoke_sync_at: '2026-04-14T10:00:00',
      }),
      jsonResponse({
        records: [
          {
            id: 'conflict-1',
            device_id: 'device-hub-1',
            source_idempotency_key: 'push-2',
            table_name: 'sales',
            record_id: 'sale-1',
            reason: 'VERSION_MISMATCH',
            message: 'Client attempted to write against a stale server version',
            client_version: 2,
            server_version: 1,
            retry_strategy: 'PULL_LATEST_THEN_RETRY',
            status: 'OPEN',
            created_at: '2026-04-14T10:01:30',
          },
        ],
      }),
      jsonResponse({
        records: [
          {
            spoke_device_id: 'spoke-counter-01',
            hub_device_id: 'device-hub-1',
            runtime_kind: 'packaged_desktop',
            hostname: 'COUNTER-02',
            operating_system: 'windows',
            app_version: '0.1.0',
            connection_state: 'CONNECTED',
            last_seen_at: '2026-04-14T10:01:30',
            last_local_sync_at: '2026-04-14T10:01:30',
          },
          {
            spoke_device_id: 'spoke-counter-02',
            hub_device_id: 'device-hub-1',
            runtime_kind: 'browser_preview',
            hostname: 'OWNER-LAPTOP',
            operating_system: 'windows',
            app_version: '0.1.0',
            connection_state: 'DISCOVERED',
            last_seen_at: '2026-04-14T10:01:20',
            last_local_sync_at: null,
          },
        ],
      }),
      jsonResponse({
        records: [
          {
            id: 'env-1',
            device_id: 'device-hub-1',
            idempotency_key: 'push-2',
            transport: 'REST',
            direction: 'INGRESS',
            entity_type: 'sync_push',
            entity_id: null,
            status: 'CONFLICT',
            attempt_count: 1,
            last_error: 'Version conflict detected',
            created_at: '2026-04-14T10:01:30',
          },
        ],
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

  test('loads read-only sync monitoring for branch staff', async () => {
    render(<App />);

    fireEvent.change(screen.getByLabelText('Korsenex token'), {
      target: { value: 'stub:sub=cashier-1;email=cashier@acme.local;name=Counter Cashier' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Start runtime session' }));

    expect(await screen.findByText('Counter Cashier')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Load sync monitoring' }));

    expect(await screen.findByText('DEGRADED')).toBeInTheDocument();
    expect(screen.getByText(/spoke-counter-01 :: CONNECTED :: COUNTER-02/)).toBeInTheDocument();
    expect(screen.getByText(/spoke-counter-02 :: DISCOVERED :: OWNER-LAPTOP/)).toBeInTheDocument();
    expect(screen.getByText(/sales :: sale-1 :: VERSION_MISMATCH/)).toBeInTheDocument();
    expect(screen.getByText(/sync_push :: CONFLICT/)).toBeInTheDocument();
    expect(screen.getByText('Read-only branch runtime posture for staff sessions.')).toBeInTheDocument();
  });
});
