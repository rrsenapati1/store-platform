/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
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

describe('store runtime exchange flow', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    let activeCashierSession: Record<string, unknown> | null = null;
    let latestSaleId: string | null = null;
    let stockOnHand = 24;

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
              stock_on_hand: stockOnHand,
              last_entry_type: stockOnHand === 24 ? 'PURCHASE_RECEIPT' : 'SALE',
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
                payment_method: 'Cash',
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
        return jsonResponse(activeCashierSession) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/sales') && method === 'POST') {
        latestSaleId = 'sale-1';
        stockOnHand = 20;
        return jsonResponse({
          id: 'sale-1',
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
          payment: { payment_method: 'Cash', amount: 388.5 },
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
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/sales/sale-1/exchanges') && method === 'POST') {
        stockOnHand = 19;
        return jsonResponse({
          id: 'exchange-1',
          tenant_id: 'tenant-acme',
          branch_id: 'branch-1',
          original_sale_id: 'sale-1',
          replacement_sale_id: 'sale-2',
          sale_return_id: 'sale-return-1',
          status: 'COMPLETED',
          balance_direction: 'COLLECT_FROM_CUSTOMER',
          balance_amount: 97.13,
          settlement_method: 'UPI',
          payment_allocations: [
            { payment_method: 'EXCHANGE_CREDIT', amount: 97.12 },
            { payment_method: 'UPI', amount: 97.13 },
          ],
          sale_return: {
            id: 'sale-return-1',
            tenant_id: 'tenant-acme',
            branch_id: 'branch-1',
            sale_id: 'sale-1',
            status: 'EXCHANGE_SETTLED',
            refund_amount: 0,
            refund_method: 'EXCHANGE_CREDIT',
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
              issued_on: '2026-04-13',
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
          },
          replacement_sale: {
            id: 'sale-2',
            tenant_id: 'tenant-acme',
            branch_id: 'branch-1',
            customer_name: 'Acme Traders',
            customer_gstin: '29AAEPM0111C1Z3',
            invoice_kind: 'B2B',
            irn_status: 'IRN_PENDING',
            invoice_number: 'SINV-BLRFLAGSHIP-0002',
            issued_on: '2026-04-13',
            subtotal: 185,
            cgst_total: 4.63,
            sgst_total: 4.62,
            igst_total: 0,
            grand_total: 194.25,
            payment: { payment_method: 'MIXED', amount: 194.25 },
            lines: [
              {
                product_id: 'product-1',
                product_name: 'Classic Tea',
                sku_code: 'tea-classic-250g',
                hsn_sac_code: '0902',
                quantity: 2,
                unit_price: 92.5,
                gst_rate: 5,
                line_subtotal: 185,
                tax_total: 9.25,
                line_total: 194.25,
              },
            ],
            tax_lines: [
              { tax_type: 'CGST', tax_rate: 2.5, taxable_amount: 185, tax_amount: 4.63 },
              { tax_type: 'SGST', tax_rate: 2.5, taxable_amount: 185, tax_amount: 4.62 },
            ],
          },
        }) as never;
      }

      throw new Error(`Unexpected fetch call: ${method} ${url}`);
    }) as typeof fetch;
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  test('creates an exchange and refreshes stock', async () => {
    render(<App />);

    fireEvent.change(screen.getByLabelText('Korsenex token'), {
      target: { value: 'stub:sub=cashier-1;email=cashier@acme.local;name=Counter Cashier' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Start runtime session' }));

    expect((await screen.findAllByText('Counter Cashier')).length).toBeGreaterThan(0);
    fireEvent.change(screen.getByLabelText('Opening float amount'), { target: { value: '150' } });
    fireEvent.click(screen.getByRole('button', { name: 'Open cashier session' }));
    expect(await screen.findByText('Active cashier session')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Customer name'), { target: { value: 'Acme Traders' } });
    fireEvent.change(screen.getByLabelText('Customer GSTIN'), { target: { value: '29AAEPM0111C1Z3' } });
    fireEvent.change(screen.getByLabelText('Sale quantity'), { target: { value: '4' } });
    fireEvent.change(screen.getByLabelText('Payment method'), { target: { value: 'Cash' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create sales invoice' }));

    expect(await screen.findAllByText('SINV-BLRFLAGSHIP-0001')).toHaveLength(3);

    fireEvent.change(screen.getByLabelText('Exchange return quantity'), { target: { value: '1' } });
    fireEvent.change(screen.getByLabelText('Replacement quantity'), { target: { value: '2' } });
    fireEvent.change(screen.getByLabelText('Exchange settlement method'), { target: { value: 'UPI' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create exchange' }));

    await waitFor(() => {
      expect(screen.getByText('Latest exchange')).toBeInTheDocument();
      expect(screen.getByText('COLLECT_FROM_CUSTOMER 97.13')).toBeInTheDocument();
      expect(screen.getAllByText('SINV-BLRFLAGSHIP-0002').length).toBeGreaterThan(0);
      expect(screen.getAllByText('SCN-BLRFLAGSHIP-0001').length).toBeGreaterThan(0);
      expect(screen.getByText('Classic Tea -> 19')).toBeInTheDocument();
    });
  });
});
