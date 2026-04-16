/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { App } from '../App';
import { StoreSyncRuntimeSection } from './StoreSyncRuntimeSection';

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
            runtime_profile: 'desktop_spoke',
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
            runtime_profile: 'desktop_spoke',
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
    cleanup();
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
    expect(screen.getByText(/desktop_spoke :: CONNECTED :: COUNTER-02/)).toBeInTheDocument();
    expect(screen.getByText(/desktop_spoke :: DISCOVERED :: OWNER-LAPTOP/)).toBeInTheDocument();
    expect(screen.getByText(/sales :: sale-1 :: VERSION_MISMATCH/)).toBeInTheDocument();
    expect(screen.getByText(/sync_push :: CONFLICT/)).toBeInTheDocument();
    expect(screen.getByText('Read-only branch runtime posture for staff sessions.')).toBeInTheDocument();
  });

  test('prepares spoke activation through the local hub surface and shows relay posture', async () => {
    globalThis.fetch = vi.fn(async (input: RequestInfo | URL) => {
      const url = typeof input === 'string' ? input : input.toString();
      if (url.endsWith('/v1/spoke-manifest')) {
        return jsonResponse({
          installation_id: 'store-runtime-abcd1234efgh5678',
          tenant_id: 'tenant-acme',
          branch_id: 'branch-1',
          hub_device_id: 'device-hub-1',
          hub_device_code: 'BLR-HUB-01',
          auth_mode: 'spoke_runtime_token_pending',
          issued_at: '2026-04-14T08:00:00.000Z',
          supported_runtime_profiles: ['desktop_spoke'],
          pairing_modes: ['qr', 'approval_code'],
          register_url: 'http://127.0.0.1:45123/v1/spokes/register',
          relay_base_url: 'http://127.0.0.1:45123/v1/relay',
          manifest_version: 1,
        }) as never;
      }
      if (url.endsWith('/v1/spokes/activate')) {
        return jsonResponse({
          activation_code: 'ACTV-ABCD-1234',
          pairing_mode: 'qr',
          runtime_profile: 'desktop_spoke',
          hub_device_id: 'device-hub-1',
          expires_at: '2099-01-01T00:00:00Z',
        }) as never;
      }
      if (url.endsWith('/runtime/sync-status')) {
        return jsonResponse({
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
          connected_spoke_count: 1,
          local_outbox_depth: 3,
          pending_mutation_count: 3,
          oldest_unsynced_mutation_age_seconds: 180,
          runtime_state: 'DEGRADED',
          last_local_spoke_sync_at: '2026-04-14T10:00:00',
        }) as never;
      }
      if (url.endsWith('/runtime/sync-conflicts')) {
        return jsonResponse({ records: [] }) as never;
      }
      if (url.endsWith('/runtime/sync-spokes')) {
        return jsonResponse({
          records: [
            {
              spoke_device_id: 'spoke-counter-01',
              hub_device_id: 'device-hub-1',
              runtime_kind: 'packaged_desktop',
              runtime_profile: 'desktop_spoke',
              hostname: 'COUNTER-02',
              operating_system: 'windows',
              app_version: '0.1.0',
              connection_state: 'REGISTERED',
              last_seen_at: '2026-04-14T10:01:30',
              last_local_sync_at: null,
            },
          ],
        }) as never;
      }
      if (url.endsWith('/runtime/sync-envelopes')) {
        return jsonResponse({ records: [] }) as never;
      }
      throw new Error(`Unexpected fetch call: ${url}`);
    }) as typeof fetch;

    render(
      <StoreSyncRuntimeSection
        accessToken="session-cashier"
        tenantId="tenant-acme"
        branchId="branch-1"
        runtimeHubServiceUrl="http://127.0.0.1:45123"
        runtimeHubManifestUrl="http://127.0.0.1:45123/v1/spoke-manifest"
      />,
    );

    expect(
      await screen.findByRole('heading', { name: 'Prepare spoke activation' }),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Prepare spoke activation' }));
    expect(await screen.findByText('ACTV-ABCD-1234')).toBeInTheDocument();
    expect(screen.getByText(/runtime.print_jobs.submit :: allowed/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Load sync monitoring' }));
    expect(await screen.findByText(/desktop_spoke :: REGISTERED :: COUNTER-02/)).toBeInTheDocument();
  });
});
