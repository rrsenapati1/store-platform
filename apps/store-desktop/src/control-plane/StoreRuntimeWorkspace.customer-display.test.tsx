/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { App } from '../App';
import { clearCustomerDisplayPayload, loadCustomerDisplayPayload } from '../customer-display/customerDisplayModel';

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

function buildAssignedRuntimeDevice() {
  return {
    id: 'device-1',
    tenant_id: 'tenant-acme',
    branch_id: 'branch-1',
    device_name: 'Counter Desktop 1',
    device_code: 'counter-1',
    session_surface: 'store_desktop',
    status: 'ACTIVE',
    assigned_staff_profile_id: 'staff-1',
    assigned_staff_full_name: 'Counter Cashier',
  };
}

function buildActiveCashierSession() {
  return {
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
    opened_at: '2026-04-14T10:30:00Z',
    closed_at: null,
    last_activity_at: '2026-04-14T10:30:00Z',
    linked_sales_count: 0,
    linked_returns_count: 0,
    gross_billed_amount: 0,
  };
}

function buildInventorySnapshot(stockOnHand: number, lastEntryType: string) {
  return {
    records: [
      {
        product_id: 'product-1',
        product_name: 'Classic Tea',
        sku_code: 'tea-classic-250g',
        stock_on_hand: stockOnHand,
        last_entry_type: lastEntryType,
      },
    ],
  };
}

function buildCompletedSale(paymentMethod: string) {
  return {
    id: 'sale-1',
    tenant_id: 'tenant-acme',
    branch_id: 'branch-1',
    customer_name: 'Acme Traders',
    customer_gstin: '29AAEPM0111C1Z3',
    invoice_kind: 'B2B',
    irn_status: 'IRN_PENDING',
    invoice_number: 'SINV-BLRFLAGSHIP-0001',
    issued_on: '2026-04-15T12:04:00.000Z',
    subtotal: 185,
    cgst_total: 4.63,
    sgst_total: 4.62,
    igst_total: 0,
    grand_total: 194.25,
    payment: { payment_method: paymentMethod, amount: 194.25 },
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
  };
}

function buildSaleRecords(paymentMethod: string) {
  return {
    records: [
      {
        sale_id: 'sale-1',
        invoice_number: 'SINV-BLRFLAGSHIP-0001',
        customer_name: 'Acme Traders',
        invoice_kind: 'B2B',
        irn_status: 'IRN_PENDING',
        payment_method: paymentMethod,
        grand_total: 194.25,
        issued_on: '2026-04-15',
      },
    ],
  };
}

function buildCheckoutPaymentSession(lifecycleStatus: string, sale: ReturnType<typeof buildCompletedSale> | null) {
  const providerPaymentId = lifecycleStatus === 'FINALIZED' ? 'cfpay_123456' : null;
  const providerStatus = lifecycleStatus === 'FINALIZED' ? 'SUCCESS' : 'ACTIVE';
  const recoveryState = lifecycleStatus === 'FINALIZED' ? 'CLOSED' : 'ACTIVE';
  const lastReconciledAt = lifecycleStatus === 'FINALIZED'
    ? '2026-04-15T12:02:00.000Z'
    : '2026-04-15T12:01:00.000Z';

  return {
    id: 'checkout-1',
    tenant_id: 'tenant-acme',
    branch_id: 'branch-1',
    provider_name: 'cashfree',
    provider_order_id: 'cf_order_checkout-1',
    provider_payment_session_id: 'cf_ps_checkout-1',
    provider_payment_id: providerPaymentId,
    payment_method: 'CASHFREE_UPI_QR',
    handoff_surface: 'BRANDED_UPI_QR',
    provider_payment_mode: 'cashfree_upi',
    lifecycle_status: lifecycleStatus,
    provider_status: providerStatus,
    order_amount: 194.25,
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
    last_reconciled_at: lastReconciledAt,
    recovery_state: recoveryState,
    sale,
  };
}

function createMemoryStorage(): Storage {
  const storage = new Map<string, string>();
  return {
    get length() {
      return storage.size;
    },
    clear() {
      storage.clear();
    },
    getItem(key: string) {
      return storage.has(key) ? storage.get(key)! : null;
    },
    key(index: number) {
      return Array.from(storage.keys())[index] ?? null;
    },
    removeItem(key: string) {
      storage.delete(key);
    },
    setItem(key: string, value: string) {
      storage.set(key, value);
    },
  };
}

describe('store runtime customer display flow', () => {
  const originalFetch = globalThis.fetch;
  const originalOpen = window.open;
  const originalWindowStorage = Object.getOwnPropertyDescriptor(window, 'localStorage');
  const originalGlobalStorage = Object.getOwnPropertyDescriptor(globalThis, 'localStorage');

  beforeEach(() => {
    const storage = createMemoryStorage();
    Object.defineProperty(window, 'localStorage', { configurable: true, value: storage });
    Object.defineProperty(globalThis, 'localStorage', { configurable: true, value: storage });
    clearCustomerDisplayPayload();
    window.open = vi.fn(() => ({ focus: vi.fn(), close: vi.fn(), closed: false } as unknown as WindowProxy));
    let saleCreated = false;
    globalThis.fetch = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
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
        return jsonResponse(buildInventorySnapshot(saleCreated ? 22 : 24, saleCreated ? 'SALE' : 'PURCHASE_RECEIPT')) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/runtime/sync-conflicts') && method === 'GET') {
        return jsonResponse({ records: [] }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/runtime/sync-spokes') && method === 'GET') {
        return jsonResponse({ records: [] }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/runtime/devices') && method === 'GET') {
        return jsonResponse({ records: [buildAssignedRuntimeDevice()] }) as never;
      }
      if (url.includes('/v1/tenants/tenant-acme/branches/branch-1/cashier-sessions') && url.includes('status=OPEN') && method === 'GET') {
        return jsonResponse({ records: [buildActiveCashierSession()] }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/checkout-payment-sessions') && method === 'GET') {
        return jsonResponse({ records: [] }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/sales') && method === 'POST') {
        saleCreated = true;
        return jsonResponse(buildCompletedSale('UPI')) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/sales') && method === 'GET') {
        return jsonResponse(saleCreated ? buildSaleRecords('UPI') : { records: [] }) as never;
      }

      throw new Error(`Unexpected fetch call: ${method} ${url}`);
    }) as typeof fetch;
  });

  afterEach(() => {
    clearCustomerDisplayPayload();
    window.open = originalOpen;
    globalThis.fetch = originalFetch;
    if (originalWindowStorage) {
      Object.defineProperty(window, 'localStorage', originalWindowStorage);
    }
    if (originalGlobalStorage) {
      Object.defineProperty(globalThis, 'localStorage', originalGlobalStorage);
    }
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  test('publishes active QR payment posture to the customer display before sale finalization', async () => {
    let checkoutFinalized = false;
    let saleCreated = false;
    const finalizedSale = buildCompletedSale('CASHFREE_UPI_QR');

    globalThis.fetch = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
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
        return jsonResponse(buildInventorySnapshot(saleCreated ? 22 : 24, saleCreated ? 'SALE' : 'PURCHASE_RECEIPT')) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/runtime/sync-conflicts') && method === 'GET') {
        return jsonResponse({ records: [] }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/runtime/sync-spokes') && method === 'GET') {
        return jsonResponse({ records: [] }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/runtime/devices') && method === 'GET') {
        return jsonResponse({ records: [buildAssignedRuntimeDevice()] }) as never;
      }
      if (url.includes('/v1/tenants/tenant-acme/branches/branch-1/cashier-sessions') && url.includes('status=OPEN') && method === 'GET') {
        return jsonResponse({ records: [buildActiveCashierSession()] }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/checkout-payment-sessions') && method === 'GET') {
        if (!saleCreated && !checkoutFinalized) {
          return jsonResponse({ records: [] }) as never;
        }
        return jsonResponse({
          records: [buildCheckoutPaymentSession(checkoutFinalized ? 'FINALIZED' : 'ACTION_READY', checkoutFinalized ? finalizedSale : null)],
        }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/checkout-payment-sessions') && method === 'POST') {
        return jsonResponse(buildCheckoutPaymentSession('ACTION_READY', null)) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/checkout-payment-sessions/checkout-1/refresh') && method === 'POST') {
        checkoutFinalized = true;
        saleCreated = true;
        return jsonResponse(buildCheckoutPaymentSession('FINALIZED', finalizedSale)) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/sales') && method === 'GET') {
        return jsonResponse(saleCreated ? buildSaleRecords('CASHFREE_UPI_QR') : { records: [] }) as never;
      }

      throw new Error(`Unexpected fetch call: ${method} ${url}`);
    }) as typeof fetch;

    render(<App />);

    fireEvent.change(screen.getByLabelText('Korsenex token'), {
      target: { value: 'stub:sub=cashier-1;email=cashier@acme.local;name=Counter Cashier' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Start runtime session' }));

    expect((await screen.findAllByText('Counter Cashier')).length).toBeGreaterThan(0);
    expect(await screen.findByText('Active cashier session')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Customer name'), { target: { value: 'Acme Traders' } });
    fireEvent.change(screen.getByLabelText('Sale quantity'), { target: { value: '2' } });
    fireEvent.change(screen.getByLabelText('Payment method'), { target: { value: 'CASHFREE_UPI_QR' } });
    await waitForEnabledButton('Open customer display');
    fireEvent.click(screen.getByRole('button', { name: 'Open customer display' }));
    await waitForEnabledButton('Start branded UPI QR');
    fireEvent.click(screen.getByRole('button', { name: 'Start branded UPI QR' }));
    await waitFor(() => {
      const activePayload = loadCustomerDisplayPayload();
      expect(activePayload?.state).toBe('payment_in_progress');
      expect(activePayload?.payment_qr?.value).toBe('upi://pay?tr=cf_order_checkout-1');
      expect(activePayload?.message).toContain('UPI app');
    }, { timeout: 5000 });

    await waitFor(() => {
      const completedPayload = loadCustomerDisplayPayload();
      expect(completedPayload?.state).toBe('sale_complete');
      expect(completedPayload?.message).toContain('SINV-BLRFLAGSHIP-0001');
    }, { timeout: 5000 });
  }, 20000);

  test('publishes cart preview and completed sale posture to the customer display', async () => {
    render(<App />);

    fireEvent.change(screen.getByLabelText('Korsenex token'), {
      target: { value: 'stub:sub=cashier-1;email=cashier@acme.local;name=Counter Cashier' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Start runtime session' }));

    expect((await screen.findAllByText('Counter Cashier')).length).toBeGreaterThan(0);

    fireEvent.change(screen.getByLabelText('Customer name'), { target: { value: 'Acme Traders' } });
    fireEvent.change(screen.getByLabelText('Sale quantity'), { target: { value: '2' } });
    fireEvent.change(screen.getByLabelText('Payment method'), { target: { value: 'UPI' } });
    await waitForEnabledButton('Open customer display');
    fireEvent.click(screen.getByRole('button', { name: 'Open customer display' }));

    await waitFor(() => {
      const payload = loadCustomerDisplayPayload();
      expect(payload?.state).toBe('active_cart');
      expect(payload?.grand_total).toBe(194.25);
    });

    fireEvent.change(screen.getByLabelText('Customer GSTIN'), { target: { value: '29AAEPM0111C1Z3' } });
    await waitForEnabledButton('Create sales invoice');
    fireEvent.click(screen.getByRole('button', { name: 'Create sales invoice' }));

    await waitFor(() => {
      const payload = loadCustomerDisplayPayload();
      expect(payload?.state).toBe('sale_complete');
      expect(payload?.message).toContain('SINV-BLRFLAGSHIP-0001');
    });
  });
});
