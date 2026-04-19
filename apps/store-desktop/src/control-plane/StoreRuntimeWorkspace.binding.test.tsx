/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';

const { tauriState, mockInvoke } = vi.hoisted(() => ({
  tauriState: {
    session: null as unknown,
    localAuth: null as unknown,
    hubIdentity: null as unknown,
  },
  mockInvoke: vi.fn(async (command: string, payload?: { session?: unknown; localAuth?: unknown; hubIdentity?: unknown }) => {
    if (command === 'cmd_load_store_runtime_cache') {
      return null;
    }
    if (command === 'cmd_get_store_runtime_cache_status') {
      return {
        backend_kind: 'native_sqlite',
        backend_label: 'Native SQLite runtime cache',
        cached_at: null,
        detail: null,
        location: 'C:/StoreRuntime/store-runtime-cache.sqlite3',
        snapshot_present: false,
      };
    }
    if (command === 'cmd_get_store_runtime_shell_status') {
      return {
        runtime_kind: 'packaged_desktop',
        runtime_label: 'Store Desktop packaged runtime',
        bridge_state: 'ready',
        app_version: '0.1.0',
        hostname: 'COUNTER-01',
        operating_system: 'windows',
        architecture: 'x86_64',
        installation_id: 'store-runtime-abcd1234efgh5678',
        claim_code: 'STORE-EFGH5678',
        runtime_home: 'C:/StoreRuntime',
        cache_db_path: 'C:/StoreRuntime/store-runtime-cache.sqlite3',
      };
    }
    if (command === 'cmd_load_store_runtime_session') {
      return tauriState.session;
    }
    if (command === 'cmd_save_store_runtime_session') {
      tauriState.session = payload?.session ?? null;
      return tauriState.session;
    }
    if (command === 'cmd_clear_store_runtime_session') {
      tauriState.session = null;
      return null;
    }
    if (command === 'cmd_load_store_runtime_local_auth') {
      return tauriState.localAuth;
    }
    if (command === 'cmd_save_store_runtime_local_auth') {
      tauriState.localAuth = payload?.localAuth ?? null;
      return tauriState.localAuth;
    }
    if (command === 'cmd_clear_store_runtime_local_auth') {
      tauriState.localAuth = null;
      return null;
    }
    if (command === 'cmd_load_store_runtime_hub_identity') {
      return tauriState.hubIdentity;
    }
    if (command === 'cmd_save_store_runtime_hub_identity') {
      tauriState.hubIdentity = payload?.hubIdentity ?? null;
      return tauriState.hubIdentity;
    }
    if (command === 'cmd_clear_store_runtime_hub_identity') {
      tauriState.hubIdentity = null;
      return null;
    }
    if (command === 'cmd_save_store_runtime_cache') {
      return {
        backend_kind: 'native_sqlite',
        backend_label: 'Native SQLite runtime cache',
        cached_at: '2026-04-14T07:00:00.000Z',
        detail: null,
        location: 'C:/StoreRuntime/store-runtime-cache.sqlite3',
        snapshot_present: true,
      };
    }
    throw new Error(`Unexpected command: ${command}`);
  }),
}));

vi.mock('@tauri-apps/api/core', () => ({
  invoke: mockInvoke,
}));

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

describe('packaged runtime device binding', () => {
  const originalFetch = globalThis.fetch;
  const originalTauriInternals = (window as Window & { __TAURI_INTERNALS__?: object }).__TAURI_INTERNALS__;

  beforeEach(() => {
    (window as Window & { __TAURI_INTERNALS__?: object }).__TAURI_INTERNALS__ = {};
    tauriState.session = null;
    tauriState.localAuth = null;
    tauriState.hubIdentity = null;

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
      jsonResponse({
        records: [
          {
            id: 'catalog-item-1',
            tenant_id: 'tenant-acme',
            branch_id: 'branch-1',
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            barcode: '8901234567890',
            hsn_sac_code: '0902',
            gst_rate: 5,
            base_selling_price: 92.5,
            selling_price_override: null,
            effective_selling_price: 92.5,
            availability_status: 'ACTIVE',
          },
        ],
      }),
      jsonResponse({
        records: [
          {
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            stock_on_hand: 24,
            last_entry_type: 'PURCHASE_RECEIPT',
          },
        ],
      }),
      jsonResponse({ records: [] }),
      jsonResponse({
        records: [
          {
            id: 'device-1',
            tenant_id: 'tenant-acme',
            branch_id: 'branch-1',
            device_name: 'Counter Desktop 1',
            device_code: 'counter-1',
            session_surface: 'store_desktop',
            status: 'ACTIVE',
            assigned_staff_profile_id: null,
            assigned_staff_full_name: null,
          },
        ],
      }),
      jsonResponse({
        claim_id: 'claim-1',
        claim_code: 'STORE-EFGH5678',
        status: 'PENDING',
        bound_device_id: null,
        bound_device_name: null,
        bound_device_code: null,
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
    (window as Window & { __TAURI_INTERNALS__?: object }).__TAURI_INTERNALS__ = originalTauriInternals;
    vi.restoreAllMocks();
  });

  test('does not auto-select the first branch device while the packaged shell claim is still pending approval', async () => {
    const view = render(<App />);

    fireEvent.change(screen.getByLabelText('Korsenex token'), {
      target: { value: 'stub:sub=cashier-1;email=cashier@acme.local;name=Counter Cashier' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Start runtime session' }));

    fireEvent.click(await screen.findByRole('button', { name: 'Operations' }));
    expect(await screen.findByText('Shell identity')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByLabelText('Runtime device')).toHaveValue('');
    });
    expect(screen.getByRole('button', { name: 'Send device heartbeat' })).toBeDisabled();

    view.unmount();
    await new Promise((resolve) => {
      setTimeout(resolve, 0);
    });
  });
});
