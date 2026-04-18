/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';

const { tauriState, mockInvoke } = vi.hoisted(() => ({
  tauriState: {
    cache: null as unknown,
    continuity: null as unknown,
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
    if (command === 'cmd_load_store_runtime_continuity') {
      return tauriState.continuity;
    }
    if (command === 'cmd_save_store_runtime_continuity') {
      tauriState.continuity = payload?.snapshot ?? null;
      return {
        authority: 'BRANCH_HUB_CONTINUITY',
        backend_kind: 'native_sqlite',
        backend_label: 'Native SQLite continuity store',
        cached_at: (payload?.snapshot as { cached_at?: string } | undefined)?.cached_at ?? null,
        detail: null,
        location: 'C:/StoreRuntime/store-runtime-continuity.sqlite3',
        snapshot_present: Boolean(payload?.snapshot),
      };
    }
    if (command === 'cmd_get_store_runtime_continuity_status') {
      return {
        authority: 'BRANCH_HUB_CONTINUITY',
        backend_kind: 'native_sqlite',
        backend_label: 'Native SQLite continuity store',
        cached_at: (tauriState.continuity as { cached_at?: string } | null)?.cached_at ?? null,
        detail: null,
        location: 'C:/StoreRuntime/store-runtime-continuity.sqlite3',
        snapshot_present: Boolean(tauriState.continuity),
      };
    }
    if (command === 'cmd_clear_store_runtime_continuity') {
      tauriState.continuity = null;
      return {
        authority: 'BRANCH_HUB_CONTINUITY',
        backend_kind: 'native_sqlite',
        backend_label: 'Native SQLite continuity store',
        cached_at: null,
        detail: null,
        location: 'C:/StoreRuntime/store-runtime-continuity.sqlite3',
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

function buildCheckoutPricePreview(quantity: number) {
  const mrp = 120;
  const unitSellingPrice = 92.5;
  const sellingSubtotal = Number((unitSellingPrice * quantity).toFixed(2));
  const taxTotal = Number((sellingSubtotal * 0.05).toFixed(2));
  const grandTotal = Number((sellingSubtotal + taxTotal).toFixed(2));
  const splitTax = Number((taxTotal / 2).toFixed(2));

  return {
    customer_profile_id: null,
    customer_name: 'Acme Traders',
    customer_gstin: '29AAEPM0111C1Z3',
    automatic_campaign: null,
    promotion_code_campaign: null,
    customer_voucher: null,
    gift_card: null,
    summary: {
      mrp_total: Number((mrp * quantity).toFixed(2)),
      selling_price_subtotal: sellingSubtotal,
      automatic_discount_total: 0,
      promotion_code_discount_total: 0,
      customer_voucher_discount_total: 0,
      loyalty_discount_total: 0,
      total_discount: 0,
      tax_total: taxTotal,
      invoice_total: grandTotal,
      grand_total: grandTotal,
      store_credit_amount: 0,
      gift_card_amount: 0,
      final_payable_amount: grandTotal,
    },
    lines: [
      {
        product_id: 'product-1',
        product_name: 'Classic Tea',
        sku_code: 'tea-classic-250g',
        quantity,
        mrp,
        unit_selling_price: unitSellingPrice,
        automatic_discount_amount: 0,
        promotion_code_discount_amount: 0,
        customer_voucher_discount_amount: 0,
        promotion_discount_source: null,
        taxable_amount: sellingSubtotal,
        tax_amount: taxTotal,
        line_total: grandTotal,
      },
    ],
    tax_lines: [
      { tax_type: 'CGST', tax_rate: 2.5, taxable_amount: sellingSubtotal, tax_amount: splitTax },
      { tax_type: 'SGST', tax_rate: 2.5, taxable_amount: sellingSubtotal, tax_amount: Number((taxTotal - splitTax).toFixed(2)) },
    ],
  };
}

function buildFetchedSalesRecord() {
  return {
    sale_id: 'sale-1',
    cashier_session_id: 'cashier-session-1',
    invoice_number: 'SINV-BLRFLAGSHIP-0001',
    customer_name: 'Acme Traders',
    invoice_kind: 'B2B',
    irn_status: 'IRN_PENDING',
    payment_method: 'UPI',
    grand_total: 388.5,
    issued_on: '2026-04-14',
  };
}

function buildCreatedSaleResponse() {
  return {
    id: 'sale-1',
    tenant_id: 'tenant-acme',
    branch_id: 'branch-1',
    cashier_session_id: 'cashier-session-1',
    customer_name: 'Acme Traders',
    customer_gstin: '29AAEPM0111C1Z3',
    invoice_kind: 'B2B',
    irn_status: 'IRN_PENDING',
    invoice_number: 'SINV-BLRFLAGSHIP-0001',
    issued_on: '2026-04-14',
    subtotal: 370,
    cgst_total: 9.25,
    sgst_total: 9.25,
    igst_total: 0,
    grand_total: 388.5,
    payment: { payment_method: 'UPI', amount: 388.5 },
    lines: [
      {
        product_id: 'product-1',
        product_name: 'Classic Tea',
        sku_code: 'tea-classic-250g',
        hsn_sac_code: '0902',
        quantity: 4,
        unit_price: 92.5,
        gst_rate: 5,
        line_subtotal: 370,
        tax_total: 18.5,
        line_total: 388.5,
      },
    ],
    tax_lines: [
      { tax_type: 'CGST', tax_rate: 2.5, taxable_amount: 370, tax_amount: 9.25 },
      { tax_type: 'SGST', tax_rate: 2.5, taxable_amount: 370, tax_amount: 9.25 },
    ],
  };
}

function installRuntimeFetchMock(options: {
  activeCashierSessions?: unknown[];
  failSaleCreate?: boolean;
  runtimePolicy?: {
    require_shift_for_attendance?: boolean;
    require_attendance_for_cashier?: boolean;
    require_assigned_staff_for_device?: boolean;
    allow_offline_sales?: boolean;
    max_pending_offline_sales?: number;
  };
  onReplayRequest?: (body: Record<string, unknown>) => void;
}) {
  let latestSaleId: string | null = null;
  let stockOnHand = 24;

  globalThis.fetch = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    const method = init?.method ?? 'GET';
    const path = url.replace(/^https?:\/\/[^/]+/, '');

    if (path.endsWith('/v1/auth/store-desktop/unlock') && method === 'POST') {
      return jsonResponse({
        access_token: 'session-cashier-unlocked',
        token_type: 'Bearer',
        expires_at: '2026-04-14T21:00:00.000Z',
        device_id: 'device-1',
        staff_profile_id: 'staff-1',
        local_auth_token: 'local-auth-seed-1',
        offline_valid_until: '2026-04-15T18:00:00.000Z',
        activation_version: 1,
      }) as never;
    }
    if (path.endsWith('/v1/auth/me') && method === 'GET') {
      return jsonResponse({
        user_id: 'user-cashier',
        email: 'cashier@acme.local',
        full_name: 'Counter Cashier',
        is_platform_admin: false,
        tenant_memberships: [],
        branch_memberships: [{ tenant_id: 'tenant-acme', branch_id: 'branch-1', role_name: 'cashier', status: 'ACTIVE' }],
      }) as never;
    }
    if (path.endsWith('/v1/tenants/tenant-acme') && method === 'GET') {
      return jsonResponse({
        id: 'tenant-acme',
        name: 'Acme Retail',
        slug: 'acme-retail',
        status: 'ACTIVE',
        onboarding_status: 'BRANCH_READY',
      }) as never;
    }
    if (path.endsWith('/v1/tenants/tenant-acme/branches') && method === 'GET') {
      return jsonResponse({
        records: [
          {
            branch_id: 'branch-1',
            tenant_id: 'tenant-acme',
            name: 'Bengaluru Flagship',
            code: 'blr-flagship',
            gstin: '29ABCDE1234F1Z5',
            status: 'ACTIVE',
          },
        ],
      }) as never;
    }
    if (path.endsWith('/v1/tenants/tenant-acme/branches/branch-1/catalog-items') && method === 'GET') {
      return jsonResponse({
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
      }) as never;
    }
    if (path.endsWith('/v1/tenants/tenant-acme/branches/branch-1/inventory-snapshot') && method === 'GET') {
      return jsonResponse({
        records: [
          {
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            stock_on_hand: stockOnHand,
            last_entry_type: latestSaleId ? 'SALE' : 'PURCHASE_RECEIPT',
          },
        ],
      }) as never;
    }
    if (path.endsWith('/v1/tenants/tenant-acme/branches/branch-1/sales') && method === 'GET') {
      return jsonResponse({
        records: latestSaleId ? [buildFetchedSalesRecord()] : [],
      }) as never;
    }
    if (path.endsWith('/v1/tenants/tenant-acme/branches/branch-1/runtime/devices') && method === 'GET') {
      return jsonResponse({
        records: [
          {
            id: 'device-1',
            tenant_id: 'tenant-acme',
            branch_id: 'branch-1',
            device_name: 'Branch Hub',
            device_code: 'blr-hub-01',
            session_surface: 'store_desktop',
            runtime_profile: 'branch_hub',
            is_branch_hub: true,
            status: 'ACTIVE',
            assigned_staff_profile_id: 'staff-1',
            assigned_staff_full_name: 'Counter Cashier',
          },
        ],
      }) as never;
    }
    if (path.endsWith('/v1/tenants/tenant-acme/branches/branch-1/runtime/device-claim') && method === 'POST') {
      return jsonResponse({
        claim_id: 'claim-1',
        claim_code: 'STORE-EFGH5678',
        status: 'APPROVED',
        bound_device_id: 'device-1',
        bound_device_name: 'Branch Hub',
        bound_device_code: 'blr-hub-01',
        last_access_token: 'session-cashier-unlocked',
      }) as never;
    }
    if (path.endsWith('/v1/tenants/tenant-acme/branches/branch-1/runtime/sync-conflicts') && method === 'GET') {
      return jsonResponse({ records: [] }) as never;
    }
    if (path.endsWith('/v1/tenants/tenant-acme/branches/branch-1/runtime/sync-spokes') && method === 'GET') {
      return jsonResponse({ records: [] }) as never;
    }
    if (path.endsWith('/v1/tenants/tenant-acme/branches/branch-1/runtime-policy') && method === 'GET') {
      return jsonResponse({
        id: 'runtime-policy-1',
        tenant_id: 'tenant-acme',
        branch_id: 'branch-1',
        require_shift_for_attendance: options.runtimePolicy?.require_shift_for_attendance ?? false,
        require_attendance_for_cashier: options.runtimePolicy?.require_attendance_for_cashier ?? true,
        require_assigned_staff_for_device: options.runtimePolicy?.require_assigned_staff_for_device ?? true,
        allow_offline_sales: options.runtimePolicy?.allow_offline_sales ?? true,
        max_pending_offline_sales: options.runtimePolicy?.max_pending_offline_sales ?? 25,
        updated_by_user_id: 'user-owner',
      }) as never;
    }
    if (path.includes('/v1/tenants/tenant-acme/branches/branch-1/shift-sessions') && method === 'GET') {
      return jsonResponse({ records: [] }) as never;
    }
    if (path.includes('/v1/tenants/tenant-acme/branches/branch-1/cashier-sessions') && method === 'GET') {
      return jsonResponse({ records: options.activeCashierSessions ?? [] }) as never;
    }
    if (path.endsWith('/v1/tenants/tenant-acme/branches/branch-1/checkout-price-preview') && method === 'POST') {
      const payload = JSON.parse(String(init?.body ?? '{}')) as { lines?: Array<{ quantity?: number }> };
      return jsonResponse(buildCheckoutPricePreview(payload.lines?.[0]?.quantity ?? 1)) as never;
    }
    if (path.endsWith('/v1/tenants/tenant-acme/branches/branch-1/sales') && method === 'POST') {
      if (options.failSaleCreate) {
        throw new Error('control plane unavailable');
      }
      latestSaleId = 'sale-1';
      stockOnHand = 20;
      return jsonResponse(buildCreatedSaleResponse()) as never;
    }
    if (path.endsWith('/v1/sync/offline-sales/replay') && method === 'POST') {
      const payload = JSON.parse(String(init?.body ?? '{}')) as Record<string, unknown>;
      options.onReplayRequest?.(payload);
      latestSaleId = 'sale-1';
      stockOnHand = 20;
      return jsonResponse({
        result: 'accepted',
        duplicate: false,
        continuity_sale_id: 'offline-sale-1',
        sale_id: 'sale-1',
        invoice_number: 'SINV-BLRFLAGSHIP-0001',
        conflict_id: null,
        message: null,
      }) as never;
    }

    throw new Error(`Unexpected fetch call: ${method} ${url}`);
  }) as typeof fetch;
}

function buildActiveCashierSession() {
  return {
    id: 'cashier-session-1',
    tenant_id: 'tenant-acme',
    branch_id: 'branch-1',
    device_registration_id: 'device-1',
    device_name: 'Branch Hub',
    device_code: 'blr-hub-01',
    staff_profile_id: 'staff-1',
    staff_full_name: 'Counter Cashier',
    runtime_user_id: 'user-cashier',
    opened_by_user_id: 'user-cashier',
    closed_by_user_id: null,
    status: 'OPEN',
    session_number: 'CS-BLRFLAGSHIP-0001',
    opening_float_amount: 150,
    opening_note: null,
    closing_note: null,
    force_close_reason: null,
    opened_at: '2026-04-17T09:00:00Z',
    closed_at: null,
    last_activity_at: '2026-04-17T09:00:00Z',
    linked_sales_count: 0,
    linked_returns_count: 0,
    gross_billed_amount: 0,
  };
}

function buildContinuitySnapshot() {
  return {
    schema_version: 1,
    authority: 'BRANCH_HUB_CONTINUITY',
    cached_at: '2026-04-14T18:00:00.000Z',
    tenant_id: 'tenant-acme',
    branch_id: 'branch-1',
    branch_code: 'blr-flagship',
    hub_device_id: 'device-1',
    next_continuity_invoice_sequence: 2,
    inventory_snapshot: [
      {
        product_id: 'product-1',
        product_name: 'Classic Tea',
        sku_code: 'tea-classic-250g',
        stock_on_hand: 20,
        last_entry_type: 'OFFLINE_SALE',
      },
    ],
    offline_sales: [
      {
        continuity_sale_id: 'offline-sale-1',
        continuity_invoice_number: 'OFF-BLRFLAGSHIP-0001',
        tenant_id: 'tenant-acme',
        branch_id: 'branch-1',
        cashier_session_id: 'cashier-session-1',
        hub_device_id: 'device-1',
        staff_actor_id: 'user-cashier',
        customer_name: 'Acme Traders',
        customer_gstin: '29AAEPM0111C1Z3',
        invoice_kind: 'B2B',
        irn_status: 'IRN_PENDING',
        payment_method: 'UPI',
        subtotal: 370,
        cgst_total: 9.25,
        sgst_total: 9.25,
        igst_total: 0,
        grand_total: 388.5,
        issued_offline_at: '2026-04-14T18:00:00.000Z',
        idempotency_key: 'offline-replay-offline-sale-1',
        reconciliation_state: 'PENDING_REPLAY',
        lines: [
          {
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            hsn_sac_code: '0902',
            quantity: 4,
            unit_price: 92.5,
            gst_rate: 5,
            line_subtotal: 370,
            tax_total: 18.5,
            line_total: 388.5,
          },
        ],
        tax_lines: [
          { tax_type: 'CGST', tax_rate: 2.5, taxable_amount: 370, tax_amount: 9.25 },
          { tax_type: 'SGST', tax_rate: 2.5, taxable_amount: 370, tax_amount: 9.25 },
        ],
        replayed_sale_id: null,
        replayed_invoice_number: null,
        replay_error: null,
      },
    ],
    conflicts: [],
    last_reconciled_at: null,
  };
}

async function createLocalAuthRecord() {
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
  };
}

function createHubIdentityRecord() {
  return {
    schema_version: 1,
    installation_id: 'store-runtime-abcd1234efgh5678',
    tenant_id: 'tenant-acme',
    branch_id: 'branch-1',
    device_id: 'device-1',
    device_code: 'blr-hub-01',
    sync_access_secret: 'hub-secret-1',
    issued_at: '2026-04-14T08:00:00.000Z',
  };
}

describe('store runtime offline continuity flow', () => {
  const originalFetch = globalThis.fetch;
  const originalTauriInternals = (window as Window & { __TAURI_INTERNALS__?: object }).__TAURI_INTERNALS__;

  beforeEach(async () => {
    (window as Window & { __TAURI_INTERNALS__?: object }).__TAURI_INTERNALS__ = {};
    mockInvoke.mockClear();
    tauriState.cache = null;
    tauriState.continuity = null;
    tauriState.session = null;
    tauriState.localAuth = await createLocalAuthRecord();
    tauriState.hubIdentity = createHubIdentityRecord();
  });

  afterEach(() => {
    cleanup();
    globalThis.fetch = originalFetch;
    (window as Window & { __TAURI_INTERNALS__?: object }).__TAURI_INTERNALS__ = originalTauriInternals;
    vi.restoreAllMocks();
  });

  test('falls back to an offline sale draft when the cloud sale request fails on a branch hub', async () => {
    installRuntimeFetchMock({
      activeCashierSessions: [buildActiveCashierSession()],
      failSaleCreate: true,
    });

    render(<App />);

    expect(await screen.findByText('Unlock with PIN')).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('PIN'), {
      target: { value: '2580' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Unlock runtime' }));

    expect((await screen.findAllByText('Counter Cashier')).length).toBeGreaterThan(0);

    fireEvent.change(screen.getByLabelText('Customer name'), { target: { value: 'Acme Traders' } });
    fireEvent.change(screen.getByLabelText('Customer GSTIN'), { target: { value: '29AAEPM0111C1Z3' } });
    fireEvent.change(screen.getByLabelText('Sale quantity'), { target: { value: '4' } });
    fireEvent.change(screen.getByLabelText('Payment method'), { target: { value: 'UPI' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create sales invoice' }));

    await waitFor(() => {
      expect(screen.getByText('Cloud unavailable. Branch continuity mode is active.')).toBeInTheDocument();
      expect(screen.getByText(/OFF-BLRFLAGSHIP-0001/)).toBeInTheDocument();
      expect(screen.getByText('Pending reconciliation')).toBeInTheDocument();
      expect(screen.getByText('Classic Tea -> 20')).toBeInTheDocument();
    }, { timeout: 10000 });

    expect(mockInvoke).toHaveBeenCalledWith(
      'cmd_save_store_runtime_continuity',
      expect.objectContaining({
        snapshot: expect.objectContaining({
          next_continuity_invoice_sequence: 2,
        }),
      }),
    );
    expect(
      (tauriState.continuity as { offline_sales?: Array<{ cashier_session_id?: string | null }> } | null)?.offline_sales?.[0]?.cashier_session_id,
    ).toBe('cashier-session-1');
  }, 15000);

  test('replays a pending offline sale through the sync-authenticated branch hub route', async () => {
    tauriState.continuity = buildContinuitySnapshot();
    let replayBody: ({ cashier_session_id?: string | null } & Record<string, unknown>) | null = null;
    installRuntimeFetchMock({
      activeCashierSessions: [buildActiveCashierSession()],
      onReplayRequest(body) {
        replayBody = body;
      },
    });

    render(<App />);

    expect(await screen.findByText('Unlock with PIN')).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('PIN'), {
      target: { value: '2580' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Unlock runtime' }));

    expect((await screen.findAllByText('Counter Cashier')).length).toBeGreaterThan(0);
    const replayButton = await screen.findByRole('button', { name: 'Replay offline sales' });

    fireEvent.click(replayButton);

    await waitFor(() => {
      expect(screen.getByText('Reconciled')).toBeInTheDocument();
      expect(screen.getAllByText(/SINV-BLRFLAGSHIP-0001/).length).toBeGreaterThan(0);
    }, { timeout: 10000 });

    const replayCall = vi.mocked(globalThis.fetch).mock.calls.find(
      ([url]) => url === 'http://127.0.0.1:8000/v1/sync/offline-sales/replay',
    );
    expect(replayCall).toBeDefined();
    expect(replayCall?.[1]).toEqual(expect.objectContaining({
      method: 'POST',
      headers: expect.objectContaining({
        'x-store-device-id': 'device-1',
        'x-store-device-secret': 'hub-secret-1',
      }),
    }));
    expect((replayBody as { cashier_session_id?: string | null } | null)?.cashier_session_id).toBe('cashier-session-1');
  });

  test('shows branch policy blocking when offline sales are disabled', async () => {
    installRuntimeFetchMock({
      activeCashierSessions: [buildActiveCashierSession()],
      runtimePolicy: {
        allow_offline_sales: false,
        max_pending_offline_sales: 0,
      },
    });

    render(<App />);

    expect(await screen.findByText('Unlock with PIN')).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('PIN'), {
      target: { value: '2580' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Unlock runtime' }));

    expect((await screen.findAllByText('Counter Cashier')).length).toBeGreaterThan(0);
    expect(await screen.findByText('Offline sales are disabled by branch policy. Replay remains available for any already-recorded pending offline sales.')).toBeInTheDocument();
  });
});
