/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, test, vi } from 'vitest';
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

function installAttendanceFetchMock() {
  let activeAttendanceSession: Record<string, unknown> | null = null;
  let activeCashierSession: Record<string, unknown> | null = null;
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
              issued_on: '2026-04-18',
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
        opened_at: '2026-04-18T09:00:00Z',
        closed_at: null,
        last_activity_at: '2026-04-18T09:00:00Z',
        linked_cashier_sessions_count: 0,
      };
      return jsonResponse(activeAttendanceSession) as never;
    }
    if (url.includes('/attendance-sessions/attendance-session-1/close') && method === 'POST') {
      const payload = JSON.parse(String(init?.body ?? '{}'));
      activeAttendanceSession = activeAttendanceSession
        ? {
          ...activeAttendanceSession,
          status: 'CLOSED',
          clock_out_note: payload.clock_out_note ?? null,
          closed_by_user_id: 'user-cashier',
          closed_at: '2026-04-18T18:00:00Z',
        }
        : null;
      return jsonResponse(activeAttendanceSession) as never;
    }
    if (url.includes('/v1/tenants/tenant-acme/branches/branch-1/cashier-sessions') && method === 'GET') {
      return jsonResponse({ records: activeCashierSession ? [activeCashierSession] : [] }) as never;
    }
    if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/cashier-sessions') && method === 'POST') {
      const payload = JSON.parse(String(init?.body ?? '{}'));
      if (!activeAttendanceSession) {
        return jsonResponse({ detail: 'Open an attendance session before opening a cashier session.' }, 400) as never;
      }
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
        opened_at: '2026-04-18T09:05:00Z',
        closed_at: null,
        last_activity_at: '2026-04-18T09:05:00Z',
        linked_sales_count: 0,
        linked_returns_count: 0,
        gross_billed_amount: 0,
      };
      return jsonResponse(activeCashierSession) as never;
    }
    if (url.includes('/cashier-sessions/cashier-session-1/close') && method === 'POST') {
      const payload = JSON.parse(String(init?.body ?? '{}'));
      activeCashierSession = activeCashierSession
        ? {
          ...activeCashierSession,
          status: 'CLOSED',
          closing_note: payload.closing_note ?? null,
          closed_by_user_id: 'user-cashier',
          closed_at: '2026-04-18T17:55:00Z',
          last_activity_at: '2026-04-18T17:55:00Z',
        }
        : null;
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
        issued_on: '2026-04-18',
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

    throw new Error(`Unexpected fetch call: ${method} ${url}`);
  }) as typeof fetch;
}

describe('store runtime attendance foundation', () => {
  const originalFetch = globalThis.fetch;

  afterEach(() => {
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  test('requires attendance before cashier session and supports clock in/out on the runtime device', async () => {
    installAttendanceFetchMock();

    render(<App />);

    fireEvent.change(screen.getByLabelText('Korsenex token'), {
      target: { value: 'stub:sub=cashier-1;email=cashier@acme.local;name=Counter Cashier' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Start runtime session' }));

    expect((await screen.findAllByText('Counter Cashier')).length).toBeGreaterThan(0);

    fireEvent.change(screen.getByLabelText('Opening float amount'), { target: { value: '250' } });
    fireEvent.change(screen.getByLabelText('Opening note'), { target: { value: 'Morning float' } });
    fireEvent.click(screen.getByRole('button', { name: 'Open cashier session' }));

    expect(await screen.findByText('Open an attendance session before opening a cashier session.')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Clock-in note'), { target: { value: 'Morning shift start' } });
    fireEvent.click(screen.getByRole('button', { name: 'Clock in' }));

    expect(await screen.findByText('Active attendance session')).toBeInTheDocument();
    expect(screen.getByText('ATTD-BLRFLAGSHIP-0001')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Open cashier session' }));
    expect(await screen.findByText('Active cashier session')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Closing note'), { target: { value: 'Till handoff complete' } });
    fireEvent.click(screen.getByRole('button', { name: 'Close cashier session' }));

    await waitFor(() => {
      expect(screen.queryByText('Active cashier session')).not.toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText('Clock-out note'), { target: { value: 'Shift complete' } });
    fireEvent.click(screen.getByRole('button', { name: 'Clock out' }));

    expect(await screen.findByText('Attendance history')).toBeInTheDocument();
    expect(screen.getByText('Shift complete')).toBeInTheDocument();
  });
});
