/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
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

describe('store runtime print queue flow', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    let activeAttendanceSession: Record<string, unknown> | null = null;
    let activeCashierSession: Record<string, unknown> | null = null;
    let latestSaleId: string | null = null;
    let printJobStatus: 'QUEUED' | 'COMPLETED' = 'QUEUED';

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
                invoice_number: 'SINV-BLRFLAGSHIP-0001',
                customer_name: 'Acme Traders',
                invoice_kind: 'B2B',
                irn_status: 'IRN_PENDING',
                payment_method: 'UPI',
                grand_total: 388.5,
                issued_on: '2026-04-13',
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
        activeAttendanceSession = {
          id: 'attendance-session-1',
          tenant_id: 'tenant-acme',
          branch_id: 'branch-1',
          device_registration_id: 'device-1',
          device_name: 'Counter Desktop 1',
          device_code: 'counter-1',
          staff_profile_id: 'staff-1',
          staff_full_name: 'Counter Cashier',
          runtime_user_id: 'user-cashier',
          opened_by_user_id: 'user-cashier',
          closed_by_user_id: null,
          status: 'OPEN',
          attendance_number: 'ATTD-BLRFLAGSHIP-0001',
          clock_in_note: 'Morning shift start',
          clock_out_note: null,
          force_close_reason: null,
          opened_at: '2026-04-17T08:55:00Z',
          closed_at: null,
          last_activity_at: '2026-04-17T08:55:00Z',
          linked_cashier_sessions_count: 0,
        };
        return jsonResponse(activeAttendanceSession) as never;
      }
      if (url.includes('/v1/tenants/tenant-acme/branches/branch-1/cashier-sessions') && method === 'GET') {
        return jsonResponse({ records: activeCashierSession ? [activeCashierSession] : [] }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/cashier-sessions') && method === 'POST') {
        activeCashierSession = {
          id: 'cashier-session-1',
          tenant_id: 'tenant-acme',
          branch_id: 'branch-1',
          device_registration_id: 'device-1',
          device_name: 'Counter Desktop 1',
          device_code: 'counter-1',
          staff_profile_id: 'staff-1',
          staff_full_name: 'Counter Cashier',
          runtime_user_id: 'user-cashier',
          opened_by_user_id: 'user-cashier',
          closed_by_user_id: null,
          status: 'OPEN',
          session_number: 'CS-BLRFLAGSHIP-0001',
          opening_float_amount: 250,
          opening_note: 'Morning float',
          closing_note: null,
          force_close_reason: null,
          opened_at: '2026-04-17T09:00:00Z',
          closed_at: null,
          last_activity_at: '2026-04-17T09:00:00Z',
          linked_sales_count: 0,
          linked_returns_count: 0,
          gross_billed_amount: 0,
        };
        return jsonResponse(activeCashierSession) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/sales') && method === 'POST') {
        latestSaleId = 'sale-1';
        return jsonResponse({
          id: latestSaleId,
          tenant_id: 'tenant-acme',
          branch_id: 'branch-1',
          cashier_session_id: 'cashier-session-1',
          customer_name: 'Acme Traders',
          customer_gstin: '29AAEPM0111C1Z3',
          invoice_kind: 'B2B',
          irn_status: 'IRN_PENDING',
          invoice_number: 'SINV-BLRFLAGSHIP-0001',
          issued_on: '2026-04-13',
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
        }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/runtime/print-jobs/sales/sale-1') && method === 'POST') {
        printJobStatus = 'QUEUED';
        return jsonResponse({
          id: 'print-job-1',
          tenant_id: 'tenant-acme',
          branch_id: 'branch-1',
          device_id: 'device-1',
          job_type: 'SALES_INVOICE',
          copies: 1,
          status: 'QUEUED',
          failure_reason: null,
          payload: { receipt_lines: ['STORE TAX INVOICE', 'Invoice: SINV-BLRFLAGSHIP-0001'] },
        }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/runtime/devices/device-1/heartbeat') && method === 'POST') {
        return jsonResponse({
          device_id: 'device-1',
          status: 'ACTIVE',
          last_seen_at: '2026-04-13T23:10:00',
          queued_job_count: 1,
        }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/runtime/devices/device-1/print-jobs') && method === 'GET') {
        return jsonResponse({
          records: [
            {
              id: 'print-job-1',
              tenant_id: 'tenant-acme',
              branch_id: 'branch-1',
              device_id: 'device-1',
              job_type: 'SALES_INVOICE',
              copies: 1,
              status: printJobStatus,
              failure_reason: null,
              payload: { receipt_lines: ['STORE TAX INVOICE', 'Invoice: SINV-BLRFLAGSHIP-0001'] },
            },
          ],
        }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/runtime/devices/device-1/print-jobs/print-job-1/complete') && method === 'POST') {
        printJobStatus = 'COMPLETED';
        return jsonResponse({
          id: 'print-job-1',
          tenant_id: 'tenant-acme',
          branch_id: 'branch-1',
          device_id: 'device-1',
          job_type: 'SALES_INVOICE',
          copies: 1,
          status: 'COMPLETED',
          failure_reason: null,
          payload: { receipt_lines: ['STORE TAX INVOICE', 'Invoice: SINV-BLRFLAGSHIP-0001'] },
        }) as never;
      }

      throw new Error(`Unexpected fetch call: ${method} ${url}`);
    }) as typeof fetch;
  });

  afterEach(() => {
    cleanup();
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  test('queues an invoice print and polls the runtime device queue', async () => {
    render(<App />);

    fireEvent.change(screen.getByLabelText('Korsenex token'), {
      target: { value: 'stub:sub=cashier-1;email=cashier@acme.local;name=Counter Cashier' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Start runtime session' }));

    expect((await screen.findAllByText('Counter Cashier')).length).toBeGreaterThan(0);
    expect((await screen.findAllByText('Counter Desktop 1')).length).toBeGreaterThan(0);
    fireEvent.change(screen.getByLabelText('Clock-in note'), { target: { value: 'Morning shift start' } });
    fireEvent.click(screen.getByRole('button', { name: 'Clock in' }));
    expect(await screen.findByText('Active attendance session')).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Opening float amount'), { target: { value: '250' } });
    fireEvent.change(screen.getByLabelText('Opening note'), { target: { value: 'Morning float' } });
    fireEvent.click(screen.getByRole('button', { name: 'Open cashier session' }));
    expect(await screen.findByText('Active cashier session')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Customer name'), { target: { value: 'Acme Traders' } });
    fireEvent.change(screen.getByLabelText('Customer GSTIN'), { target: { value: '29AAEPM0111C1Z3' } });
    fireEvent.change(screen.getByLabelText('Sale quantity'), { target: { value: '4' } });
    fireEvent.change(screen.getByLabelText('Payment method'), { target: { value: 'UPI' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create sales invoice' }));

    expect((await screen.findAllByText('SINV-BLRFLAGSHIP-0001')).length).toBeGreaterThan(0);

    fireEvent.click(screen.getByRole('button', { name: 'Queue latest invoice print' }));

    await waitFor(() => {
      expect(screen.getByText('Queued print job')).toBeInTheDocument();
      expect(screen.getByText('print-job-1')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: 'Send device heartbeat' }));

    await waitFor(() => {
      expect(screen.getByText('Queued jobs')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: 'Refresh print queue' }));

    await waitFor(() => {
      expect(screen.getByText('Queued jobs: 1')).toBeInTheDocument();
      expect(screen.getByText('SALES_INVOICE')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: 'Mark first job completed' }));

    await waitFor(() => {
      expect(screen.getByText('COMPLETED')).toBeInTheDocument();
    });
  });
});
