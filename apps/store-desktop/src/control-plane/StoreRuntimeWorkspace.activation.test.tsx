/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';

const { tauriState, mockInvoke } = vi.hoisted(() => ({
  tauriState: {
    cache: null as unknown,
    session: null as unknown,
    localAuth: null as unknown,
    hubIdentity: null as unknown,
  },
  mockInvoke: vi.fn(async (command: string, payload?: { snapshot?: unknown; session?: unknown; localAuth?: unknown; hubIdentity?: unknown }) => {
    if (command === 'cmd_load_store_runtime_cache') {
      return tauriState.cache;
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
      tauriState.cache = payload?.snapshot ?? null;
      return {
        backend_kind: 'native_sqlite',
        backend_label: 'Native SQLite runtime cache',
        cached_at: '2026-04-14T07:00:00.000Z',
        detail: null,
        location: 'C:/StoreRuntime/store-runtime-cache.sqlite3',
        snapshot_present: true,
      };
    }
    if (command === 'cmd_clear_store_runtime_cache') {
      tauriState.cache = null;
      return {
        backend_kind: 'native_sqlite',
        backend_label: 'Native SQLite runtime cache',
        cached_at: null,
        detail: null,
        location: 'C:/StoreRuntime/store-runtime-cache.sqlite3',
        snapshot_present: false,
      };
    }
    throw new Error(`Unexpected command: ${command}`);
  }),
}));

vi.mock('@tauri-apps/api/core', () => ({
  invoke: mockInvoke,
}));

import { App } from '../App';
import { createStoreRuntimePinSalt, hashStoreRuntimePin } from './storeRuntimePinAuth';

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

function runtimeBootstrapResponses(
  accessToken: string,
  options: {
    isBranchHub?: boolean;
    includeHubBootstrap?: boolean;
  } = {},
): MockResponse[] {
  const hubBootstrapResponses = options.includeHubBootstrap
    ? [
        jsonResponse({
          device_id: 'device-1',
          device_code: 'counter-1',
          installation_id: 'store-runtime-abcd1234efgh5678',
          sync_access_secret: 'hub-secret-1',
          issued_at: '2026-04-14T08:00:00.000Z',
        }),
      ]
    : [];
  return [
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
          is_branch_hub: options.isBranchHub ?? false,
          status: 'ACTIVE',
          assigned_staff_profile_id: 'staff-1',
          assigned_staff_full_name: 'Counter Cashier',
        },
      ],
    }),
    jsonResponse({
      claim_id: 'claim-1',
      claim_code: 'STORE-EFGH5678',
      status: 'APPROVED',
      bound_device_id: 'device-1',
      bound_device_name: 'Counter Desktop 1',
      bound_device_code: 'counter-1',
      last_access_token: accessToken,
    }),
    ...hubBootstrapResponses,
  ];
}

function createCachedRuntimeSnapshot() {
  return {
    schema_version: 1,
    cached_at: '2026-04-14T07:00:00.000Z',
    authority: 'CONTROL_PLANE_ONLY',
    actor: {
      user_id: 'user-cashier',
      email: 'cashier@acme.local',
      full_name: 'Counter Cashier',
      is_platform_admin: false,
      tenant_memberships: [],
      branch_memberships: [{ tenant_id: 'tenant-acme', branch_id: 'branch-1', role_name: 'cashier', status: 'ACTIVE' }],
    },
    tenant: {
      id: 'tenant-acme',
      name: 'Acme Retail',
      slug: 'acme-retail',
      status: 'ACTIVE',
      onboarding_status: 'BRANCH_READY',
    },
    branches: [{ branch_id: 'branch-1', tenant_id: 'tenant-acme', name: 'Bengaluru Flagship', code: 'blr-flagship', status: 'ACTIVE' }],
    branch_catalog_items: [],
    inventory_snapshot: [],
    sales: [],
    runtime_devices: [],
    selected_runtime_device_id: '',
    runtime_heartbeat: null,
    print_jobs: [],
    latest_print_job: null,
    latest_sale: null,
    latest_sale_return: null,
    latest_exchange: null,
    pending_mutations: [],
  };
}

async function createLocalAuthRecord(
  overrides: Partial<typeof tauriState.localAuth> & { offline_valid_until?: string } = {},
) {
  const pinSalt = createStoreRuntimePinSalt();
  const pinHash = await hashStoreRuntimePin('2580', pinSalt);
  return {
    schema_version: 1,
    installation_id: 'store-runtime-abcd1234efgh5678',
    device_id: 'device-1',
    staff_profile_id: 'staff-1',
    local_auth_token: 'local-auth-seed-1',
    activation_version: 1,
    offline_valid_until: '2026-04-15T18:00:00.000Z',
    pin_attempt_limit: 5,
    pin_lockout_seconds: 300,
    pin_salt: pinSalt,
    pin_hash: pinHash,
    failed_attempts: 0,
    locked_until: null,
    enrolled_at: '2026-04-14T07:00:00.000Z',
    last_unlocked_at: null,
    ...overrides,
  };
}

describe('store desktop packaged activation flow', () => {
  const originalFetch = globalThis.fetch;
  const originalTauriInternals = (window as Window & { __TAURI_INTERNALS__?: object }).__TAURI_INTERNALS__;

  beforeEach(() => {
    (window as Window & { __TAURI_INTERNALS__?: object }).__TAURI_INTERNALS__ = {};
    mockInvoke.mockClear();
    tauriState.cache = null;
    tauriState.session = null;
    tauriState.localAuth = null;
    tauriState.hubIdentity = null;

    const responses = [
      jsonResponse({
        access_token: 'session-cashier',
        token_type: 'Bearer',
        expires_at: '2026-04-14T18:00:00.000Z',
        device_id: 'device-1',
        staff_profile_id: 'staff-1',
        local_auth_token: 'local-auth-seed-1',
        offline_valid_until: '2026-04-15T18:00:00.000Z',
        activation_version: 1,
      }),
      ...runtimeBootstrapResponses('session-cashier'),
      jsonResponse({ status: 'signed_out' }),
      jsonResponse({
        access_token: 'session-cashier-unlocked',
        token_type: 'Bearer',
        expires_at: '2026-04-14T21:00:00.000Z',
        device_id: 'device-1',
        staff_profile_id: 'staff-1',
        local_auth_token: 'local-auth-seed-1',
        offline_valid_until: '2026-04-15T18:00:00.000Z',
        activation_version: 1,
      }),
      ...runtimeBootstrapResponses('session-cashier-unlocked'),
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
    (window as Window & { __TAURI_INTERNALS__?: object }).__TAURI_INTERNALS__ = originalTauriInternals;
    vi.restoreAllMocks();
  });

  test('redeems an owner-issued activation for a packaged runtime and persists the desktop session', async () => {
    render(<App />);

    expect(await screen.findByText('Desktop activation')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Activation code'), {
      target: { value: 'ACTV-1234-5678' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Activate desktop access' }));

    expect(await screen.findByText('Set runtime PIN')).toBeInTheDocument();
    expect(screen.queryByText('Counter Cashier')).not.toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('New PIN'), {
      target: { value: '2580' },
    });
    fireEvent.change(screen.getByLabelText('Confirm PIN'), {
      target: { value: '2580' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Save runtime PIN' }));

    expect(await screen.findByText('Counter Cashier')).toBeInTheDocument();
    expect(mockInvoke).toHaveBeenCalledWith(
      'cmd_save_store_runtime_session',
      expect.objectContaining({
        session: expect.objectContaining({
          access_token: 'session-cashier',
          expires_at: '2026-04-14T18:00:00.000Z',
        }),
      }),
    );
    expect(mockInvoke).toHaveBeenCalledWith(
      'cmd_save_store_runtime_local_auth',
      expect.objectContaining({
        localAuth: expect.objectContaining({
          device_id: 'device-1',
          staff_profile_id: 'staff-1',
          activation_version: 1,
          offline_valid_until: '2026-04-15T18:00:00.000Z',
        }),
      }),
    );

    fireEvent.click(screen.getByRole('button', { name: 'Sign out' }));

    expect(await screen.findByText('Unlock with PIN')).toBeInTheDocument();
    expect(mockInvoke).toHaveBeenCalledWith('cmd_clear_store_runtime_session');
    expect(globalThis.fetch).toHaveBeenCalledWith(
      '/v1/auth/sign-out',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          authorization: 'Bearer session-cashier',
        }),
      }),
    );

    fireEvent.change(screen.getByLabelText('PIN'), {
      target: { value: '2580' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Unlock runtime' }));

    expect(await screen.findByText('Counter Cashier')).toBeInTheDocument();
    expect(globalThis.fetch).toHaveBeenCalledWith(
      '/v1/auth/store-desktop/unlock',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          installation_id: 'store-runtime-abcd1234efgh5678',
          local_auth_token: 'local-auth-seed-1',
        }),
      }),
    );
  });

  test('locks packaged startup behind PIN instead of exposing cached actor data', async () => {
    tauriState.cache = createCachedRuntimeSnapshot();
    tauriState.localAuth = {
      schema_version: 1,
      installation_id: 'store-runtime-abcd1234efgh5678',
      device_id: 'device-1',
      staff_profile_id: 'staff-1',
      local_auth_token: 'local-auth-seed-1',
      activation_version: 1,
      offline_valid_until: '2026-04-15T18:00:00.000Z',
      pin_attempt_limit: 5,
      pin_lockout_seconds: 300,
      pin_salt: 'salt',
      pin_hash: 'hash',
      failed_attempts: 0,
      locked_until: null,
      enrolled_at: '2026-04-14T07:00:00.000Z',
      last_unlocked_at: null,
    };
    globalThis.fetch = vi.fn(async () => {
      throw new Error('locked startup should not trigger network bootstrap');
    }) as typeof fetch;

    render(<App />);

    expect(await screen.findByText('Unlock with PIN')).toBeInTheDocument();
    expect(screen.queryByText('Counter Cashier')).not.toBeInTheDocument();
  });

  test('clears a packaged persisted session when no local auth record exists', async () => {
    tauriState.session = {
      access_token: 'session-cashier',
      expires_at: '2026-04-14T18:00:00.000Z',
    };
    globalThis.fetch = vi.fn(async () => {
      throw new Error('packaged startup should not restore a persisted session without local auth');
    }) as typeof fetch;

    render(<App />);

    expect(await screen.findByText('Desktop activation')).toBeInTheDocument();
    expect(screen.queryByText('Counter Cashier')).not.toBeInTheDocument();
    await waitFor(() => {
      expect(mockInvoke).toHaveBeenCalledWith('cmd_clear_store_runtime_session');
    });
    expect(globalThis.fetch).not.toHaveBeenCalled();
  });

  test('unlocks cached runtime locally when the control plane is unavailable but offline unlock is still valid', async () => {
    tauriState.cache = createCachedRuntimeSnapshot();
    tauriState.localAuth = await createLocalAuthRecord();
    tauriState.session = null;
    globalThis.fetch = vi.fn(async () => {
      throw new Error('control plane unavailable');
    }) as typeof fetch;

    render(<App />);

    expect(await screen.findByText('Unlock with PIN')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('PIN'), {
      target: { value: '2580' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Unlock runtime' }));

    expect(await screen.findByText('Counter Cashier')).toBeInTheDocument();
    expect(screen.getByText('Control plane unavailable. Cached runtime unlocked locally.')).toBeInTheDocument();
    expect(globalThis.fetch).toHaveBeenCalledWith(
      '/v1/auth/store-desktop/unlock',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          installation_id: 'store-runtime-abcd1234efgh5678',
          local_auth_token: 'local-auth-seed-1',
        }),
      }),
    );
  });

  test('blocks packaged offline unlock when the cached offline window has expired', async () => {
    tauriState.cache = createCachedRuntimeSnapshot();
    tauriState.localAuth = await createLocalAuthRecord({
      offline_valid_until: '2026-04-13T18:00:00.000Z',
    });
    tauriState.session = null;
    globalThis.fetch = vi.fn(async () => {
      throw new Error('control plane unavailable');
    }) as typeof fetch;

    render(<App />);

    expect(await screen.findByText('Unlock with PIN')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('PIN'), {
      target: { value: '2580' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Unlock runtime' }));

    expect(await screen.findByText('Offline runtime unlock expired. Reconnect to the control plane to continue.')).toBeInTheDocument();
    expect(screen.queryByText('Counter Cashier')).not.toBeInTheDocument();
  });

  test('bootstraps and persists hub machine identity for a packaged branch hub device', async () => {
    const responses = [
      jsonResponse({
        access_token: 'session-hub-cashier',
        token_type: 'Bearer',
        expires_at: '2026-04-14T18:00:00.000Z',
        device_id: 'device-1',
        staff_profile_id: 'staff-1',
        local_auth_token: 'local-auth-seed-1',
        offline_valid_until: '2026-04-15T18:00:00.000Z',
        activation_version: 1,
      }),
      ...runtimeBootstrapResponses('session-hub-cashier', {
        isBranchHub: true,
        includeHubBootstrap: true,
      }),
    ];

    globalThis.fetch = vi.fn(async () => {
      const next = responses.shift();
      if (!next) {
        throw new Error('Unexpected fetch call');
      }
      return next as never;
    }) as typeof fetch;

    render(<App />);

    expect(await screen.findByText('Desktop activation')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Activation code'), {
      target: { value: 'ACTV-1234-5678' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Activate desktop access' }));

    expect(await screen.findByText('Set runtime PIN')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('New PIN'), {
      target: { value: '2580' },
    });
    fireEvent.change(screen.getByLabelText('Confirm PIN'), {
      target: { value: '2580' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Save runtime PIN' }));

    expect(await screen.findByText('Counter Cashier')).toBeInTheDocument();
    expect(mockInvoke).toHaveBeenCalledWith(
      'cmd_save_store_runtime_hub_identity',
      expect.objectContaining({
        hubIdentity: expect.objectContaining({
          installation_id: 'store-runtime-abcd1234efgh5678',
          tenant_id: 'tenant-acme',
          branch_id: 'branch-1',
          device_id: 'device-1',
          device_code: 'counter-1',
          sync_access_secret: 'hub-secret-1',
        }),
      }),
    );
  });
});
