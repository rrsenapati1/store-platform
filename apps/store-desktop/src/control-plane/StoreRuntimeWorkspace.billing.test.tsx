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

describe('store runtime billing foundation flow', () => {
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
      jsonResponse({ records: [] }),
      jsonResponse({
        id: 'sale-1',
        tenant_id: 'tenant-acme',
        branch_id: 'branch-1',
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
      }),
      jsonResponse({
        records: [
          {
            sale_id: 'sale-1',
            invoice_number: 'SINV-BLRFLAGSHIP-0001',
            customer_name: 'Acme Traders',
            invoice_kind: 'B2B',
            irn_status: 'IRN_PENDING',
            payment_method: 'UPI',
            grand_total: 388.5,
            issued_on: '2026-04-13',
          },
        ],
      }),
      jsonResponse({
        records: [
          {
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            stock_on_hand: 20,
            last_entry_type: 'SALE',
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
    vi.useRealTimers();
  });

  test('creates a GST invoice and refreshes branch stock', async () => {
    render(<App />);

    fireEvent.change(screen.getByLabelText('Korsenex token'), {
      target: { value: 'stub:sub=cashier-1;email=cashier@acme.local;name=Counter Cashier' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Start runtime session' }));

    expect(await screen.findByText('Counter Cashier')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Customer name'), { target: { value: 'Acme Traders' } });
    fireEvent.change(screen.getByLabelText('Customer GSTIN'), { target: { value: '29AAEPM0111C1Z3' } });
    fireEvent.change(screen.getByLabelText('Sale quantity'), { target: { value: '4' } });
    fireEvent.change(screen.getByLabelText('Payment method'), { target: { value: 'UPI' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create sales invoice' }));

    await waitFor(() => {
      expect(screen.getByText('Latest sales invoice')).toBeInTheDocument();
      expect(screen.getAllByText('SINV-BLRFLAGSHIP-0001').length).toBeGreaterThan(0);
      expect(screen.getByText('IRN_PENDING')).toBeInTheDocument();
      expect(screen.getByText('Sales register')).toBeInTheDocument();
      expect(screen.getByText('Live inventory snapshot')).toBeInTheDocument();
      expect(screen.getByText('Classic Tea -> 20')).toBeInTheDocument();
    });
  });

  test('starts a Cashfree UPI QR session and finalizes the sale after payment confirmation', async () => {
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
      jsonResponse({ records: [] }),
      jsonResponse({
        id: 'checkout-1',
        tenant_id: 'tenant-acme',
        branch_id: 'branch-1',
        provider_name: 'cashfree',
        provider_order_id: 'cf_order_checkout-1',
        provider_payment_session_id: 'cf_ps_checkout-1',
        provider_payment_id: null,
        payment_method: 'CASHFREE_UPI_QR',
        handoff_surface: 'BRANDED_UPI_QR',
        provider_payment_mode: 'cashfree_upi',
        lifecycle_status: 'ACTION_READY',
        provider_status: 'ACTIVE',
        order_amount: 388.5,
        currency_code: 'INR',
        action_payload: {
          kind: 'upi_qr',
          value: 'upi://pay?tr=cf_order_checkout-1',
          label: 'Korsenex customer UPI QR',
          description: 'Scan with any UPI app to complete this checkout.',
        },
        action_expires_at: '2026-04-15T12:10:00.000Z',
        qr_payload: { format: 'upi_qr', value: 'upi://pay?tr=cf_order_checkout-1' },
        qr_expires_at: '2026-04-15T12:10:00.000Z',
        last_error_message: null,
        last_reconciled_at: '2026-04-15T12:01:00.000Z',
        recovery_state: 'ACTIVE',
        sale: null,
      }),
      jsonResponse({
        records: [
          {
            id: 'checkout-1',
            tenant_id: 'tenant-acme',
            branch_id: 'branch-1',
            provider_name: 'cashfree',
            provider_order_id: 'cf_order_checkout-1',
            provider_payment_session_id: 'cf_ps_checkout-1',
            provider_payment_id: null,
            payment_method: 'CASHFREE_UPI_QR',
            handoff_surface: 'BRANDED_UPI_QR',
            provider_payment_mode: 'cashfree_upi',
            lifecycle_status: 'ACTION_READY',
            provider_status: 'ACTIVE',
            order_amount: 388.5,
            currency_code: 'INR',
            action_payload: {
              kind: 'upi_qr',
              value: 'upi://pay?tr=cf_order_checkout-1',
              label: 'Korsenex customer UPI QR',
              description: 'Scan with any UPI app to complete this checkout.',
            },
            action_expires_at: '2026-04-15T12:10:00.000Z',
            qr_payload: { format: 'upi_qr', value: 'upi://pay?tr=cf_order_checkout-1' },
            qr_expires_at: '2026-04-15T12:10:00.000Z',
            last_error_message: null,
            last_reconciled_at: '2026-04-15T12:01:00.000Z',
            recovery_state: 'ACTIVE',
            sale: null,
          },
        ],
      }),
      jsonResponse({
        id: 'checkout-1',
        tenant_id: 'tenant-acme',
        branch_id: 'branch-1',
        provider_name: 'cashfree',
        provider_order_id: 'cf_order_checkout-1',
        provider_payment_session_id: 'cf_ps_checkout-1',
        provider_payment_id: 'cfpay_123456',
        payment_method: 'CASHFREE_UPI_QR',
        handoff_surface: 'BRANDED_UPI_QR',
        provider_payment_mode: 'cashfree_upi',
        lifecycle_status: 'FINALIZED',
        provider_status: 'SUCCESS',
        order_amount: 388.5,
        currency_code: 'INR',
        action_payload: {
          kind: 'upi_qr',
          value: 'upi://pay?tr=cf_order_checkout-1',
          label: 'Korsenex customer UPI QR',
          description: 'Scan with any UPI app to complete this checkout.',
        },
        action_expires_at: '2026-04-15T12:10:00.000Z',
        qr_payload: { format: 'upi_qr', value: 'upi://pay?tr=cf_order_checkout-1' },
        qr_expires_at: '2026-04-15T12:10:00.000Z',
        last_error_message: null,
        last_reconciled_at: '2026-04-15T12:02:00.000Z',
        recovery_state: 'CLOSED',
        sale: {
          id: 'sale-1',
          tenant_id: 'tenant-acme',
          branch_id: 'branch-1',
          customer_name: 'Acme Traders',
          customer_gstin: '29AAEPM0111C1Z3',
          invoice_kind: 'B2B',
          irn_status: 'IRN_PENDING',
          invoice_number: 'SINV-BLRFLAGSHIP-0001',
          issued_on: '2026-04-15',
          subtotal: 370,
          cgst_total: 9.25,
          sgst_total: 9.25,
          igst_total: 0,
          grand_total: 388.5,
          payment: { payment_method: 'CASHFREE_UPI_QR', amount: 388.5 },
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
        },
      }),
      jsonResponse({
        records: [
          {
            id: 'checkout-1',
            tenant_id: 'tenant-acme',
            branch_id: 'branch-1',
            provider_name: 'cashfree',
            provider_order_id: 'cf_order_checkout-1',
            provider_payment_session_id: 'cf_ps_checkout-1',
            provider_payment_id: 'cfpay_123456',
            payment_method: 'CASHFREE_UPI_QR',
            handoff_surface: 'BRANDED_UPI_QR',
            provider_payment_mode: 'cashfree_upi',
            lifecycle_status: 'FINALIZED',
            provider_status: 'SUCCESS',
            order_amount: 388.5,
            currency_code: 'INR',
            action_payload: {
              kind: 'upi_qr',
              value: 'upi://pay?tr=cf_order_checkout-1',
              label: 'Korsenex customer UPI QR',
              description: 'Scan with any UPI app to complete this checkout.',
            },
            action_expires_at: '2026-04-15T12:10:00.000Z',
            qr_payload: { format: 'upi_qr', value: 'upi://pay?tr=cf_order_checkout-1' },
            qr_expires_at: '2026-04-15T12:10:00.000Z',
            last_error_message: null,
            last_reconciled_at: '2026-04-15T12:02:00.000Z',
            recovery_state: 'CLOSED',
            sale: {
              id: 'sale-1',
              tenant_id: 'tenant-acme',
              branch_id: 'branch-1',
              customer_name: 'Acme Traders',
              customer_gstin: '29AAEPM0111C1Z3',
              invoice_kind: 'B2B',
              irn_status: 'IRN_PENDING',
              invoice_number: 'SINV-BLRFLAGSHIP-0001',
              issued_on: '2026-04-15',
              subtotal: 370,
              cgst_total: 9.25,
              sgst_total: 9.25,
              igst_total: 0,
              grand_total: 388.5,
              payment: { payment_method: 'CASHFREE_UPI_QR', amount: 388.5 },
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
            },
          },
        ],
      }),
      jsonResponse({
        records: [
          {
            sale_id: 'sale-1',
            invoice_number: 'SINV-BLRFLAGSHIP-0001',
            customer_name: 'Acme Traders',
            invoice_kind: 'B2B',
            irn_status: 'IRN_PENDING',
            payment_method: 'CASHFREE_UPI_QR',
            grand_total: 388.5,
            issued_on: '2026-04-15',
          },
        ],
      }),
      jsonResponse({
        records: [
          {
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            stock_on_hand: 20,
            last_entry_type: 'SALE',
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

    render(<App />);

    fireEvent.change(screen.getByLabelText('Korsenex token'), {
      target: { value: 'stub:sub=cashier-1;email=cashier@acme.local;name=Counter Cashier' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Start runtime session' }));

    expect(await screen.findByText('Counter Cashier')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Customer name'), { target: { value: 'Acme Traders' } });
    fireEvent.change(screen.getByLabelText('Customer GSTIN'), { target: { value: '29AAEPM0111C1Z3' } });
    fireEvent.change(screen.getByLabelText('Sale quantity'), { target: { value: '4' } });
    fireEvent.change(screen.getByLabelText('Payment method'), { target: { value: 'CASHFREE_UPI_QR' } });
    fireEvent.click(screen.getByRole('button', { name: 'Start branded UPI QR' }));

    expect(await screen.findByText(/Waiting for customer payment/i)).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getAllByText('cf_order_checkout-1').length).toBeGreaterThan(0);
    });

    await waitFor(() => {
      expect(screen.getAllByText('SINV-BLRFLAGSHIP-0001').length).toBeGreaterThan(0);
      expect(screen.getByText('Classic Tea -> 20')).toBeInTheDocument();
    }, { timeout: 5000 });
  });
});
