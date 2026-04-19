/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { App } from '../App';
import { clearRuntimeBrowserState } from './storeRuntimeTestHelpers';

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

async function waitForEnabledButton(name: string) {
  await waitFor(() => {
    expect(screen.getByRole('button', { name })).not.toBeDisabled();
  });
}

function installCashierSessionFetchMock(options?: { requireShiftForAttendance?: boolean }) {
  let activeAttendanceSession: Record<string, unknown> | null = null;
  let activeCashierSession: Record<string, unknown> | null = null;
  let activeShiftSession: Record<string, unknown> | null = null;
  let latestSaleId: string | null = null;

  globalThis.fetch = vi.fn(async (input, init) => {
    const url = String(input);
    const method = init?.method ?? 'GET';

    if (url.endsWith('/v1/auth/oidc/exchange') && method === 'POST') {
      return jsonResponse({ access_token: 'session-cashier', token_type: 'Bearer' }) as never;
    }
    if (url.endsWith('/v1/auth/me') && method === 'GET') {
      return jsonResponse({
        user_id: 'user-cashier',
        email: 'cashier@acme.local',
        full_name: 'Counter Cashier',
        is_platform_admin: false,
        tenant_memberships: [],
        branch_memberships: [{ tenant_id: 'tenant-acme', branch_id: 'branch-1', role_name: 'cashier', status: 'ACTIVE' }],
      }) as never;
    }
    if (url.endsWith('/v1/tenants/tenant-acme') && method === 'GET') {
      return jsonResponse({
        id: 'tenant-acme',
        name: 'Acme Retail',
        slug: 'acme-retail',
        status: 'ACTIVE',
        onboarding_status: 'BRANCH_READY',
      }) as never;
    }
    if (url.endsWith('/v1/tenants/tenant-acme/branches') && method === 'GET') {
      return jsonResponse({
        records: [{ branch_id: 'branch-1', tenant_id: 'tenant-acme', name: 'Bengaluru Flagship', code: 'blr-flagship', status: 'ACTIVE' }],
      }) as never;
    }
    if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/catalog-items') && method === 'GET') {
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
    if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/inventory-snapshot') && method === 'GET') {
      return jsonResponse({
        records: [
          {
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            stock_on_hand: latestSaleId ? 20 : 24,
            last_entry_type: latestSaleId ? 'SALE' : 'PURCHASE_RECEIPT',
          },
        ],
      }) as never;
    }
    if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/sales') && method === 'GET') {
      return jsonResponse({
        records: latestSaleId
          ? [
            {
              sale_id: latestSaleId,
              customer_profile_id: null,
              invoice_number: 'SINV-BLRFLAGSHIP-0001',
              customer_name: 'Walk-in customer',
              invoice_kind: 'B2C',
              irn_status: 'NOT_APPLICABLE',
              payment_method: 'Cash',
              grand_total: 97.12,
              store_credit_amount: 0,
              loyalty_points_redeemed: 0,
              loyalty_discount_amount: 0,
              loyalty_points_earned: 0,
              issued_on: '2026-04-17',
            },
          ]
          : [],
      }) as never;
    }
    if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/runtime/devices') && method === 'GET') {
      return jsonResponse({
        records: [
          {
            id: 'device-1',
            tenant_id: 'tenant-acme',
            branch_id: 'branch-1',
            device_name: 'Counter Desktop 1',
            device_code: 'counter-1',
            session_surface: 'store_desktop',
            status: 'ACTIVE',
            assigned_staff_profile_id: 'staff-1',
            assigned_staff_full_name: 'Counter Cashier',
          },
        ],
      }) as never;
    }
    if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/runtime/sync-conflicts') && method === 'GET') {
      return jsonResponse({ records: [] }) as never;
    }
    if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/runtime/sync-spokes') && method === 'GET') {
      return jsonResponse({ records: [] }) as never;
    }
    if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/runtime-policy') && method === 'GET') {
      return jsonResponse({
        id: 'runtime-policy-1',
        tenant_id: 'tenant-acme',
        branch_id: 'branch-1',
        require_shift_for_attendance: options?.requireShiftForAttendance ?? false,
        require_attendance_for_cashier: true,
        require_assigned_staff_for_device: true,
        allow_offline_sales: true,
        max_pending_offline_sales: 25,
        updated_by_user_id: 'user-owner',
      }) as never;
    }
    if (url.includes('/v1/tenants/tenant-acme/branches/branch-1/shift-sessions') && method === 'GET') {
      return jsonResponse({ records: activeShiftSession ? [activeShiftSession] : [] }) as never;
    }
    if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/shift-sessions') && method === 'POST') {
      const payload = JSON.parse(String(init?.body ?? '{}'));
      activeShiftSession = {
        id: 'shift-session-1',
        tenant_id: 'tenant-acme',
        branch_id: 'branch-1',
        shift_number: 'SHIFT-BLRFLAGSHIP-0001',
        shift_name: payload.shift_name,
        status: 'OPEN',
        opening_note: payload.opening_note ?? null,
        closing_note: null,
        force_close_reason: null,
        opened_at: '2026-04-17T08:45:00Z',
        closed_at: null,
        linked_attendance_sessions_count: 0,
        linked_cashier_sessions_count: 0,
      };
      return jsonResponse(activeShiftSession) as never;
    }
    if (url.includes('/v1/tenants/tenant-acme/branches/branch-1/attendance-sessions') && method === 'GET') {
      return jsonResponse({ records: activeAttendanceSession ? [activeAttendanceSession] : [] }) as never;
    }
    if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/attendance-sessions') && method === 'POST') {
      const payload = JSON.parse(String(init?.body ?? '{}'));
      activeAttendanceSession = {
        id: 'attendance-session-1',
        tenant_id: 'tenant-acme',
        branch_id: 'branch-1',
        device_registration_id: payload.device_registration_id,
        device_name: 'Counter Desktop 1',
        device_code: 'counter-1',
        staff_profile_id: payload.staff_profile_id,
        staff_full_name: 'Counter Cashier',
        runtime_user_id: 'user-cashier',
        opened_by_user_id: 'user-cashier',
        closed_by_user_id: null,
        status: 'OPEN',
        attendance_number: 'ATTD-BLRFLAGSHIP-0001',
        clock_in_note: payload.clock_in_note ?? null,
        clock_out_note: null,
        force_close_reason: null,
        shift_session_id: activeShiftSession?.id ?? null,
        opened_at: '2026-04-17T08:55:00Z',
        closed_at: null,
        last_activity_at: '2026-04-17T08:55:00Z',
        linked_cashier_sessions_count: 0,
      };
      if (activeShiftSession) {
        activeShiftSession = {
          ...activeShiftSession,
          linked_attendance_sessions_count: 1,
        };
      }
      return jsonResponse(activeAttendanceSession) as never;
    }
    if (url.includes('/v1/tenants/tenant-acme/branches/branch-1/cashier-sessions') && method === 'GET') {
      return jsonResponse({ records: activeCashierSession ? [activeCashierSession] : [] }) as never;
    }
    if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/cashier-sessions') && method === 'POST') {
      const payload = JSON.parse(String(init?.body ?? '{}'));
      activeCashierSession = {
        id: 'cashier-session-1',
        tenant_id: 'tenant-acme',
        branch_id: 'branch-1',
        device_registration_id: payload.device_registration_id,
        device_name: 'Counter Desktop 1',
        device_code: 'counter-1',
        staff_profile_id: payload.staff_profile_id,
        staff_full_name: 'Counter Cashier',
        runtime_user_id: 'user-cashier',
        opened_by_user_id: 'user-cashier',
        closed_by_user_id: null,
        status: 'OPEN',
        session_number: 'CS-BLRFLAGSHIP-0001',
        opening_float_amount: payload.opening_float_amount,
        opening_note: payload.opening_note ?? null,
        closing_note: null,
        force_close_reason: null,
        opened_at: '2026-04-17T09:00:00Z',
        closed_at: null,
        last_activity_at: '2026-04-17T09:00:00Z',
        linked_sales_count: 0,
        linked_returns_count: 0,
        gross_billed_amount: 0,
      };
      if (activeShiftSession) {
        activeShiftSession = {
          ...activeShiftSession,
          linked_cashier_sessions_count: 1,
        };
      }
      return jsonResponse(activeCashierSession) as never;
    }
    if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/sales') && method === 'POST') {
      const payload = JSON.parse(String(init?.body ?? '{}'));
      if (!payload.cashier_session_id) {
        return jsonResponse({ detail: 'Cashier session is required before billing' }, 400) as never;
      }
      latestSaleId = 'sale-1';
      return jsonResponse({
        id: latestSaleId,
        tenant_id: 'tenant-acme',
        branch_id: 'branch-1',
        cashier_session_id: payload.cashier_session_id,
        customer_profile_id: null,
        customer_name: 'Walk-in customer',
        customer_gstin: null,
        invoice_kind: 'B2C',
        irn_status: 'NOT_APPLICABLE',
        invoice_number: 'SINV-BLRFLAGSHIP-0001',
        issued_on: '2026-04-17',
        subtotal: 92.5,
        cgst_total: 2.31,
        sgst_total: 2.31,
        igst_total: 0,
        grand_total: 97.12,
        promotion_discount_amount: 0,
        store_credit_amount: 0,
        loyalty_points_redeemed: 0,
        loyalty_discount_amount: 0,
        loyalty_points_earned: 0,
        payment: { payment_method: 'Cash', amount: 97.12 },
        lines: [
          {
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            hsn_sac_code: '0902',
            quantity: 1,
            unit_price: 92.5,
            gst_rate: 5,
            line_subtotal: 92.5,
            tax_total: 4.62,
            line_total: 97.12,
          },
        ],
        tax_lines: [
          { tax_type: 'CGST', tax_rate: 2.5, taxable_amount: 92.5, tax_amount: 2.31 },
          { tax_type: 'SGST', tax_rate: 2.5, taxable_amount: 92.5, tax_amount: 2.31 },
        ],
      }) as never;
    }
    if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/sales/sale-1/returns') && method === 'POST') {
      const payload = JSON.parse(String(init?.body ?? '{}'));
      if (!payload.cashier_session_id) {
        return jsonResponse({ detail: 'Cashier session is required before processing returns' }, 400) as never;
      }
      return jsonResponse({
        id: 'sale-return-1',
        tenant_id: 'tenant-acme',
        branch_id: 'branch-1',
        sale_id: 'sale-1',
        cashier_session_id: payload.cashier_session_id,
        status: 'REFUND_PENDING_APPROVAL',
        refund_amount: 97.12,
        refund_method: 'Cash',
        lines: [
          {
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            hsn_sac_code: '0902',
            quantity: 1,
            unit_price: 92.5,
            gst_rate: 5,
            line_subtotal: 92.5,
            tax_total: 4.62,
            line_total: 97.12,
          },
        ],
        credit_note: {
          id: 'credit-note-1',
          credit_note_number: 'SCN-BLRFLAGSHIP-0001',
          issued_on: '2026-04-17',
          subtotal: 92.5,
          cgst_total: 2.31,
          sgst_total: 2.31,
          igst_total: 0,
          grand_total: 97.12,
          tax_lines: [
            { tax_type: 'CGST', tax_rate: 2.5, taxable_amount: 92.5, tax_amount: 2.31 },
            { tax_type: 'SGST', tax_rate: 2.5, taxable_amount: 92.5, tax_amount: 2.31 },
          ],
        },
      }) as never;
    }

    throw new Error(`Unexpected fetch call: ${method} ${url}`);
  }) as typeof fetch;
}

describe('store runtime cashier session governance', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    clearRuntimeBrowserState();
  });

  afterEach(() => {
    clearRuntimeBrowserState();
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  test('requires an open cashier session before billing and includes cashier_session_id after opening one', async () => {
    installCashierSessionFetchMock();

    render(<App />);

    fireEvent.change(screen.getByLabelText('Korsenex token'), {
      target: { value: 'stub:sub=cashier-1;email=cashier@acme.local;name=Counter Cashier' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Start runtime session' }));

    expect((await screen.findAllByText('Counter Cashier')).length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole('button', { name: 'Sell' }));
    await screen.findByLabelText('Sale quantity');

    fireEvent.change(screen.getByLabelText('Sale quantity'), { target: { value: '1' } });
    fireEvent.change(screen.getByLabelText('Payment method'), { target: { value: 'Cash' } });
    await waitForEnabledButton('Create sales invoice');
    fireEvent.click(screen.getByRole('button', { name: 'Create sales invoice' }));

    expect(await screen.findByText('Open a cashier session before billing.')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Entry' }));
    await screen.findByRole('heading', { name: 'Store access' });
    fireEvent.click(screen.getByRole('button', { name: 'Clock in' }));
    fireEvent.change(screen.getByLabelText('Opening float amount'), { target: { value: '250' } });
    fireEvent.change(screen.getByLabelText('Opening note'), { target: { value: 'Morning float' } });
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Open register' })).toBeEnabled();
    });
    fireEvent.click(screen.getByRole('button', { name: 'Open register' }));

    expect((await screen.findAllByText('CS-BLRFLAGSHIP-0001')).length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole('button', { name: 'Resume selling' }));

    await waitForEnabledButton('Create sales invoice');
    fireEvent.click(screen.getByRole('button', { name: 'Create sales invoice' }));

    await waitFor(() => {
      const createSaleCall = vi.mocked(globalThis.fetch).mock.calls.find(
        ([url, init]) =>
          String(url).includes('/v1/tenants/tenant-acme/branches/branch-1/sales')
          && init?.method === 'POST',
      );
      expect(createSaleCall).toBeDefined();
      expect(JSON.parse(String(createSaleCall?.[1]?.body ?? '{}'))).toMatchObject({
        cashier_session_id: 'cashier-session-1',
      });
    });
  });

  test('includes cashier_session_id when creating a sale return', async () => {
    installCashierSessionFetchMock();

    render(<App />);

    fireEvent.change(screen.getByLabelText('Korsenex token'), {
      target: { value: 'stub:sub=cashier-1;email=cashier@acme.local;name=Counter Cashier' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Start runtime session' }));

    expect((await screen.findAllByText('Counter Cashier')).length).toBeGreaterThan(0);

    fireEvent.click(screen.getByRole('button', { name: 'Entry' }));
    await screen.findByRole('heading', { name: 'Store access' });
    fireEvent.click(screen.getByRole('button', { name: 'Clock in' }));
    fireEvent.change(screen.getByLabelText('Opening float amount'), { target: { value: '150' } });
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Open register' })).toBeEnabled();
    });
    fireEvent.click(screen.getByRole('button', { name: 'Open register' }));

    expect((await screen.findAllByText('CS-BLRFLAGSHIP-0001')).length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole('button', { name: 'Resume selling' }));

    await waitForEnabledButton('Create sales invoice');
    fireEvent.click(screen.getByRole('button', { name: 'Create sales invoice' }));
    expect(await screen.findAllByText('SINV-BLRFLAGSHIP-0001')).not.toHaveLength(0);
    fireEvent.click(screen.getByRole('button', { name: 'Returns' }));
    await screen.findByRole('heading', { name: 'Returns and exchanges' });
    await screen.findByLabelText('Return quantity');

    fireEvent.change(screen.getByLabelText('Return quantity'), { target: { value: '1' } });
    fireEvent.change(screen.getByLabelText('Refund amount'), { target: { value: '97.12' } });
    fireEvent.change(screen.getByLabelText('Refund method'), { target: { value: 'Cash' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create sale return' }));

    await waitFor(() => {
      const createReturnCall = vi.mocked(globalThis.fetch).mock.calls.find(
        ([url, init]) =>
          String(url).includes('/v1/tenants/tenant-acme/branches/branch-1/sales/sale-1/returns')
          && init?.method === 'POST',
      );
      expect(createReturnCall).toBeDefined();
      expect(JSON.parse(String(createReturnCall?.[1]?.body ?? '{}'))).toMatchObject({
        cashier_session_id: 'cashier-session-1',
      });
    });
  });

  test('requires an open shift before attendance when the branch runtime policy enables shift governance', async () => {
    installCashierSessionFetchMock({ requireShiftForAttendance: true });

    render(<App />);

    fireEvent.change(screen.getByLabelText('Korsenex token'), {
      target: { value: 'stub:sub=cashier-1;email=cashier@acme.local;name=Counter Cashier' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Start runtime session' }));

    expect((await screen.findAllByText('Counter Cashier')).length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole('button', { name: 'Entry' }));
    await screen.findByRole('heading', { name: 'Store access' });
    expect(await screen.findByText(/Open a branch shift before clocking in/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Clock in' })).toBeDisabled();

    fireEvent.change(screen.getByLabelText('Shift name'), { target: { value: 'Morning counter shift' } });
    fireEvent.change(screen.getByLabelText('Shift opening note'), { target: { value: 'Float counted before attendance' } });
    fireEvent.click(screen.getByRole('button', { name: 'Open shift session' }));

    expect(await screen.findByText('Active shift session')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Clock in' })).not.toBeDisabled();

    fireEvent.click(screen.getByRole('button', { name: 'Clock in' }));
    fireEvent.change(screen.getByLabelText('Opening float amount'), { target: { value: '200' } });

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Open register' })).toBeEnabled();
    });

    await waitFor(() => {
      const createShiftCall = vi.mocked(globalThis.fetch).mock.calls.find(
        ([url, init]) =>
          String(url).includes('/v1/tenants/tenant-acme/branches/branch-1/shift-sessions')
          && init?.method === 'POST',
      );
      expect(createShiftCall).toBeDefined();
      expect(JSON.parse(String(createShiftCall?.[1]?.body ?? '{}'))).toMatchObject({
        shift_name: 'Morning counter shift',
      });
    });
  });
});
