/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { OwnerSyncRuntimeSection } from './OwnerSyncRuntimeSection';

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

describe('owner sync runtime section', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    const responses = [
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

  test('loads sync status, conflicts, and recent envelopes', async () => {
    render(<OwnerSyncRuntimeSection accessToken="session-owner" tenantId="tenant-acme" branchId="branch-1" />);

    fireEvent.click(screen.getByRole('button', { name: 'Load sync monitoring' }));

    expect(await screen.findByText('Hub device')).toBeInTheDocument();
    expect(screen.getByText('DEGRADED')).toBeInTheDocument();
    expect(screen.getByText(/sales :: sale-1 :: VERSION_MISMATCH/)).toBeInTheDocument();
    expect(screen.getByText(/sync_push :: CONFLICT/)).toBeInTheDocument();
  });
});
