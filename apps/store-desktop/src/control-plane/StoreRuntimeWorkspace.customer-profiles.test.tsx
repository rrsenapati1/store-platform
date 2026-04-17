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

function buildSaleResponse(overrides: Record<string, unknown> = {}) {
  return {
    id: 'sale-1',
    tenant_id: 'tenant-acme',
    branch_id: 'branch-1',
    customer_profile_id: null,
    customer_name: 'Walk-in Customer',
    customer_gstin: null,
    invoice_kind: 'B2C',
    irn_status: 'NOT_REQUIRED',
    invoice_number: 'SINV-BLRFLAGSHIP-0001',
    issued_on: '2026-04-16',
    subtotal: 92.5,
    cgst_total: 2.31,
    sgst_total: 2.31,
    igst_total: 0,
    grand_total: 97.12,
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
    ...overrides,
  };
}

function buildCustomerProfile(id: string, fullName: string, gstin: string | null) {
  return {
    id,
    tenant_id: 'tenant-acme',
    full_name: fullName,
    phone: '+919999999999',
    email: 'accounts@acme.example',
    gstin,
    default_note: 'Preferred wholesale buyer',
    tags: ['wholesale'],
    status: 'ACTIVE',
    created_at: '2026-04-16T09:00:00Z',
    updated_at: '2026-04-16T09:00:00Z',
  };
}

function buildStoreCreditResponse(customerProfileId: string) {
  return {
    customer_profile_id: customerProfileId,
    available_balance: 120,
    issued_total: 120,
    redeemed_total: 0,
    adjusted_total: 0,
    lots: [],
    ledger_entries: [],
  };
}

function buildLoyaltyProgramResponse() {
  return {
    status: 'ACTIVE',
    earn_points_per_currency_unit: 1,
    redeem_step_points: 100,
    redeem_value_per_step: 10,
    minimum_redeem_points: 200,
  };
}

function buildCustomerLoyaltyResponse(customerProfileId: string) {
  return {
    customer_profile_id: customerProfileId,
    available_points: 300,
    earned_total: 300,
    redeemed_total: 0,
    adjusted_total: 300,
    ledger_entries: [
      {
        id: 'loyalty-ledger-1',
        entry_type: 'ADJUSTED',
        source_type: 'MANUAL_ADJUSTMENT',
        source_reference_id: null,
        points_delta: 300,
        balance_after: 300,
        note: 'Welcome points',
        branch_id: null,
        created_at: '2026-04-16T09:20:00Z',
      },
    ],
  };
}

function buildCustomerVouchers(customerProfileId: string) {
  return [
    {
      id: 'voucher-1',
      tenant_id: 'tenant-acme',
      campaign_id: 'campaign-voucher-1',
      customer_profile_id: customerProfileId,
      voucher_code: 'VCH-0001',
      voucher_name: 'Welcome voucher',
      voucher_amount: 15,
      status: 'ACTIVE',
      issued_note: 'Welcome bonus',
      redeemed_sale_id: null,
      created_at: '2026-04-17T09:00:00Z',
      updated_at: '2026-04-17T09:00:00Z',
      redeemed_at: null,
    },
  ];
}

describe('store runtime checkout customer profiles', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    vi.setSystemTime(new Date('2026-04-16T10:00:00.000Z'));
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  test('creates and links a customer profile from checkout before creating a sale', async () => {
    let createdProfile = buildCustomerProfile('profile-created', 'Acme Traders', '29AAEPM0111C1Z3');
    let profileRecords = [createdProfile];
    let capturedCreateProfilePayload: Record<string, unknown> | null = null;
    let capturedSalePayload: Record<string, unknown> | null = null;
    let salesRecords = [] as Array<Record<string, unknown>>;
    let inventorySnapshot = [
      {
        product_id: 'product-1',
        product_name: 'Classic Tea',
        sku_code: 'tea-classic-250g',
        stock_on_hand: 24,
        last_entry_type: 'PURCHASE_RECEIPT',
      },
    ];

    globalThis.fetch = vi.fn(async (input, init) => {
      const url = String(input);
      const method = init?.method ?? 'GET';

      if (url.endsWith('/v1/auth/oidc/exchange') && method === 'POST') {
        return jsonResponse({ access_token: 'session-cashier', token_type: 'Bearer' }) as never;
      }
      if (url.endsWith('/v1/auth/me')) {
        return jsonResponse({
          user_id: 'user-cashier',
          email: 'cashier@acme.local',
          full_name: 'Counter Cashier',
          is_platform_admin: false,
          tenant_memberships: [],
          branch_memberships: [{ tenant_id: 'tenant-acme', branch_id: 'branch-1', role_name: 'cashier', status: 'ACTIVE' }],
        }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme')) {
        return jsonResponse({
          id: 'tenant-acme',
          name: 'Acme Retail',
          slug: 'acme-retail',
          status: 'ACTIVE',
          onboarding_status: 'BRANCH_READY',
        }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches')) {
        return jsonResponse({
          records: [{ branch_id: 'branch-1', tenant_id: 'tenant-acme', name: 'Bengaluru Flagship', code: 'blr-flagship', status: 'ACTIVE' }],
        }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/catalog-items')) {
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
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/inventory-snapshot')) {
        return jsonResponse({ records: inventorySnapshot }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/sales') && method === 'GET') {
        return jsonResponse({ records: salesRecords }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/runtime/devices')) {
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
              assigned_staff_profile_id: null,
              assigned_staff_full_name: null,
            },
          ],
        }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/checkout-payment-sessions') && method === 'GET') {
        return jsonResponse({ records: [] }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/loyalty-program') && method === 'GET') {
        return jsonResponse(buildLoyaltyProgramResponse()) as never;
      }
      if (/\/v1\/tenants\/tenant-acme\/customer-profiles\/[^/]+\/store-credit$/.test(url) && method === 'GET') {
        const customerProfileId = url.split('/customer-profiles/')[1]?.split('/store-credit')[0] ?? 'profile-created';
        return jsonResponse(buildStoreCreditResponse(customerProfileId)) as never;
      }
      if (/\/v1\/tenants\/tenant-acme\/customer-profiles\/[^/]+\/loyalty$/.test(url) && method === 'GET') {
        const customerProfileId = url.split('/customer-profiles/')[1]?.split('/loyalty')[0] ?? 'profile-created';
        return jsonResponse(buildCustomerLoyaltyResponse(customerProfileId)) as never;
      }
      if (/\/v1\/tenants\/tenant-acme\/customer-profiles\/[^/]+\/vouchers$/.test(url) && method === 'GET') {
        const customerProfileId = url.split('/customer-profiles/')[1]?.split('/vouchers')[0] ?? 'profile-created';
        return jsonResponse({ records: buildCustomerVouchers(customerProfileId) }) as never;
      }
      if (url.includes('/v1/tenants/tenant-acme/customer-profiles') && method === 'GET') {
        return jsonResponse({ records: profileRecords }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/customer-profiles') && method === 'POST') {
        const createProfilePayload = JSON.parse(String(init?.body ?? '{}')) as Record<string, unknown>;
        capturedCreateProfilePayload = createProfilePayload;
        createdProfile = buildCustomerProfile(
          'profile-created',
          String(createProfilePayload.full_name ?? 'Acme Traders'),
          typeof createProfilePayload.gstin === 'string' ? createProfilePayload.gstin : null,
        );
        profileRecords = [createdProfile];
        return jsonResponse(createdProfile) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/sales') && method === 'POST') {
        const salePayload = JSON.parse(String(init?.body ?? '{}')) as Record<string, unknown>;
        capturedSalePayload = salePayload;
        salesRecords = [
          {
            sale_id: 'sale-1',
            customer_profile_id: salePayload.customer_profile_id ?? null,
            invoice_number: 'SINV-BLRFLAGSHIP-0001',
            customer_name: String(salePayload.customer_name ?? 'Acme Traders'),
            invoice_kind: 'B2B',
            irn_status: 'IRN_PENDING',
            payment_method: 'UPI',
            grand_total: 388.5,
            issued_on: '2026-04-16',
          },
        ];
        inventorySnapshot = [
          {
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            stock_on_hand: 20,
            last_entry_type: 'SALE',
          },
        ];
        return jsonResponse(buildSaleResponse({
          customer_profile_id: salePayload.customer_profile_id ?? null,
          customer_name: salePayload.customer_name ?? 'Acme Traders',
          customer_gstin: salePayload.customer_gstin ?? '29AAEPM0111C1Z3',
          invoice_kind: 'B2B',
          irn_status: 'IRN_PENDING',
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
        })) as never;
      }

      throw new Error(`Unexpected fetch call: ${method} ${url}`);
    }) as typeof fetch;

    render(<App />);

    fireEvent.change(screen.getByLabelText('Korsenex token'), {
      target: { value: 'stub:sub=cashier-1;email=cashier@acme.local;name=Counter Cashier' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Start runtime session' }));

    expect(await screen.findByText('Counter Cashier')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Customer name'), { target: { value: 'Acme Traders' } });
    fireEvent.change(screen.getByLabelText('Customer GSTIN'), { target: { value: '29AAEPM0111C1Z3' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create customer profile from checkout' }));

    await waitFor(() => {
      expect(capturedCreateProfilePayload).not.toBeNull();
      expect(capturedCreateProfilePayload!).toMatchObject({
        full_name: 'Acme Traders',
        gstin: '29AAEPM0111C1Z3',
      });
    });
    expect(await screen.findByRole('button', { name: 'Use manual customer details' })).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Sale quantity'), { target: { value: '4' } });
    fireEvent.change(screen.getByLabelText('Payment method'), { target: { value: 'UPI' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create sales invoice' }));

    await waitFor(() => {
      expect(capturedSalePayload).not.toBeNull();
      expect(capturedSalePayload!).toMatchObject({
        customer_profile_id: 'profile-created',
        customer_name: 'Acme Traders',
        customer_gstin: '29AAEPM0111C1Z3',
      });
      expect(screen.getAllByText('SINV-BLRFLAGSHIP-0001').length).toBeGreaterThan(0);
    });
  });

  test('clears a selected customer profile and falls back to manual checkout details', async () => {
    let capturedSalePayload: Record<string, unknown> | null = null;

    globalThis.fetch = vi.fn(async (input, init) => {
      const url = String(input);
      const method = init?.method ?? 'GET';

      if (url.endsWith('/v1/auth/oidc/exchange') && method === 'POST') {
        return jsonResponse({ access_token: 'session-cashier', token_type: 'Bearer' }) as never;
      }
      if (url.endsWith('/v1/auth/me')) {
        return jsonResponse({
          user_id: 'user-cashier',
          email: 'cashier@acme.local',
          full_name: 'Counter Cashier',
          is_platform_admin: false,
          tenant_memberships: [],
          branch_memberships: [{ tenant_id: 'tenant-acme', branch_id: 'branch-1', role_name: 'cashier', status: 'ACTIVE' }],
        }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme')) {
        return jsonResponse({
          id: 'tenant-acme',
          name: 'Acme Retail',
          slug: 'acme-retail',
          status: 'ACTIVE',
          onboarding_status: 'BRANCH_READY',
        }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches')) {
        return jsonResponse({
          records: [{ branch_id: 'branch-1', tenant_id: 'tenant-acme', name: 'Bengaluru Flagship', code: 'blr-flagship', status: 'ACTIVE' }],
        }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/catalog-items')) {
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
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/inventory-snapshot')) {
        return jsonResponse({
          records: [
            {
              product_id: 'product-1',
              product_name: 'Classic Tea',
              sku_code: 'tea-classic-250g',
              stock_on_hand: 24,
              last_entry_type: 'PURCHASE_RECEIPT',
            },
          ],
        }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/sales') && method === 'GET') {
        return jsonResponse({ records: [] }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/runtime/devices')) {
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
              assigned_staff_profile_id: null,
              assigned_staff_full_name: null,
            },
          ],
        }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/checkout-payment-sessions') && method === 'GET') {
        return jsonResponse({ records: [] }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/loyalty-program') && method === 'GET') {
        return jsonResponse(buildLoyaltyProgramResponse()) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/customer-profiles/profile-1/store-credit') && method === 'GET') {
        return jsonResponse(buildStoreCreditResponse('profile-1')) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/customer-profiles/profile-1/vouchers') && method === 'GET') {
        return jsonResponse({ records: buildCustomerVouchers('profile-1') }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/customer-profiles/profile-1/loyalty') && method === 'GET') {
        return jsonResponse(buildCustomerLoyaltyResponse('profile-1')) as never;
      }
      if (url.includes('/v1/tenants/tenant-acme/customer-profiles') && method === 'GET') {
        return jsonResponse({
          records: [buildCustomerProfile('profile-1', 'Acme Traders', '29AAEPM0111C1Z3')],
        }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/sales') && method === 'POST') {
        const salePayload = JSON.parse(String(init?.body ?? '{}')) as Record<string, unknown>;
        capturedSalePayload = salePayload;
        return jsonResponse(buildSaleResponse({
          customer_name: salePayload.customer_name ?? 'Walk-in Customer',
          customer_gstin: salePayload.customer_gstin ?? null,
          customer_profile_id: salePayload.customer_profile_id ?? null,
          payment: { payment_method: 'Cash', amount: 97.12 },
        })) as never;
      }

      throw new Error(`Unexpected fetch call: ${method} ${url}`);
    }) as typeof fetch;

    render(<App />);

    fireEvent.change(screen.getByLabelText('Korsenex token'), {
      target: { value: 'stub:sub=cashier-1;email=cashier@acme.local;name=Counter Cashier' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Start runtime session' }));

    expect(await screen.findByText('Counter Cashier')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Customer profile search'), { target: { value: 'Acme' } });
    fireEvent.click(screen.getByRole('button', { name: 'Find customer profiles' }));
    fireEvent.click(await screen.findByRole('button', { name: /Use customer profile Acme Traders/i }));
    expect(await screen.findByText('Available store credit')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Use manual customer details' }));

    fireEvent.change(screen.getByLabelText('Customer name'), { target: { value: 'Walk-in Customer' } });
    fireEvent.change(screen.getByLabelText('Customer GSTIN'), { target: { value: '' } });
    fireEvent.change(screen.getByLabelText('Sale quantity'), { target: { value: '1' } });
    fireEvent.change(screen.getByLabelText('Payment method'), { target: { value: 'Cash' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create sales invoice' }));

    await waitFor(() => {
      expect(capturedSalePayload?.customer_name).toBe('Walk-in Customer');
      expect(capturedSalePayload?.customer_gstin).toBeNull();
      expect(capturedSalePayload).not.toHaveProperty('customer_profile_id');
    });
  });

  test('loads customer loyalty posture when a customer profile is selected', async () => {
    globalThis.fetch = vi.fn(async (input, init) => {
      const url = String(input);
      const method = init?.method ?? 'GET';

      if (url.endsWith('/v1/auth/oidc/exchange') && method === 'POST') {
        return jsonResponse({ access_token: 'session-cashier', token_type: 'Bearer' }) as never;
      }
      if (url.endsWith('/v1/auth/me')) {
        return jsonResponse({
          user_id: 'user-cashier',
          email: 'cashier@acme.local',
          full_name: 'Counter Cashier',
          is_platform_admin: false,
          tenant_memberships: [],
          branch_memberships: [{ tenant_id: 'tenant-acme', branch_id: 'branch-1', role_name: 'cashier', status: 'ACTIVE' }],
        }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme')) {
        return jsonResponse({
          id: 'tenant-acme',
          name: 'Acme Retail',
          slug: 'acme-retail',
          status: 'ACTIVE',
          onboarding_status: 'BRANCH_READY',
        }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches')) {
        return jsonResponse({
          records: [{ branch_id: 'branch-1', tenant_id: 'tenant-acme', name: 'Bengaluru Flagship', code: 'blr-flagship', status: 'ACTIVE' }],
        }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/catalog-items')) {
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
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/inventory-snapshot')) {
        return jsonResponse({
          records: [
            {
              product_id: 'product-1',
              product_name: 'Classic Tea',
              sku_code: 'tea-classic-250g',
              stock_on_hand: 24,
              last_entry_type: 'PURCHASE_RECEIPT',
            },
          ],
        }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/sales') && method === 'GET') {
        return jsonResponse({ records: [] }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/runtime/devices')) {
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
              assigned_staff_profile_id: null,
              assigned_staff_full_name: null,
            },
          ],
        }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/checkout-payment-sessions') && method === 'GET') {
        return jsonResponse({ records: [] }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/loyalty-program') && method === 'GET') {
        return jsonResponse(buildLoyaltyProgramResponse()) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/customer-profiles/profile-1/store-credit') && method === 'GET') {
        return jsonResponse(buildStoreCreditResponse('profile-1')) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/customer-profiles/profile-1/vouchers') && method === 'GET') {
        return jsonResponse({ records: buildCustomerVouchers('profile-1') }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/customer-profiles/profile-1/loyalty') && method === 'GET') {
        return jsonResponse(buildCustomerLoyaltyResponse('profile-1')) as never;
      }
      if (url.includes('/v1/tenants/tenant-acme/customer-profiles') && method === 'GET') {
        return jsonResponse({
          records: [buildCustomerProfile('profile-1', 'Acme Traders', '29AAEPM0111C1Z3')],
        }) as never;
      }

      throw new Error(`Unexpected fetch call: ${method} ${url}`);
    }) as typeof fetch;

    render(<App />);

    fireEvent.change(screen.getByLabelText('Korsenex token'), {
      target: { value: 'stub:sub=cashier-1;email=cashier@acme.local;name=Counter Cashier' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Start runtime session' }));

    expect(await screen.findByText('Counter Cashier')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Customer profile search'), { target: { value: 'Acme' } });
    fireEvent.click(screen.getByRole('button', { name: 'Find customer profiles' }));
    fireEvent.click(await screen.findByRole('button', { name: /Use customer profile Acme Traders/i }));

    expect(await screen.findByText('Available loyalty points')).toBeInTheDocument();
    expect(screen.getAllByText('300').length).toBeGreaterThan(0);
  });

  test('selects customer vouchers, keeps them mutually exclusive with promotion codes, and sends voucher posture in direct sale creation', async () => {
    let capturedSalePayload: Record<string, unknown> | null = null;
    let salesRecords = [] as Array<Record<string, unknown>>;

    globalThis.fetch = vi.fn(async (input, init) => {
      const url = String(input);
      const method = init?.method ?? 'GET';

      if (url.endsWith('/v1/auth/oidc/exchange') && method === 'POST') {
        return jsonResponse({ access_token: 'session-cashier', token_type: 'Bearer' }) as never;
      }
      if (url.endsWith('/v1/auth/me')) {
        return jsonResponse({
          user_id: 'user-cashier',
          email: 'cashier@acme.local',
          full_name: 'Counter Cashier',
          is_platform_admin: false,
          tenant_memberships: [],
          branch_memberships: [{ tenant_id: 'tenant-acme', branch_id: 'branch-1', role_name: 'cashier', status: 'ACTIVE' }],
        }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme')) {
        return jsonResponse({
          id: 'tenant-acme',
          name: 'Acme Retail',
          slug: 'acme-retail',
          status: 'ACTIVE',
          onboarding_status: 'BRANCH_READY',
        }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches')) {
        return jsonResponse({
          records: [{ branch_id: 'branch-1', tenant_id: 'tenant-acme', name: 'Bengaluru Flagship', code: 'blr-flagship', status: 'ACTIVE' }],
        }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/catalog-items')) {
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
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/inventory-snapshot')) {
        return jsonResponse({
          records: [
            {
              product_id: 'product-1',
              product_name: 'Classic Tea',
              sku_code: 'tea-classic-250g',
              stock_on_hand: 24,
              last_entry_type: 'PURCHASE_RECEIPT',
            },
          ],
        }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/sales') && method === 'GET') {
        return jsonResponse({ records: salesRecords }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/runtime/devices')) {
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
              assigned_staff_profile_id: null,
              assigned_staff_full_name: null,
            },
          ],
        }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/checkout-payment-sessions') && method === 'GET') {
        return jsonResponse({ records: [] }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/loyalty-program') && method === 'GET') {
        return jsonResponse(buildLoyaltyProgramResponse()) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/customer-profiles/profile-1/store-credit') && method === 'GET') {
        return jsonResponse(buildStoreCreditResponse('profile-1')) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/customer-profiles/profile-1/vouchers') && method === 'GET') {
        return jsonResponse({ records: buildCustomerVouchers('profile-1') }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/customer-profiles/profile-1/loyalty') && method === 'GET') {
        return jsonResponse(buildCustomerLoyaltyResponse('profile-1')) as never;
      }
      if (url.includes('/v1/tenants/tenant-acme/customer-profiles') && method === 'GET') {
        return jsonResponse({
          records: [buildCustomerProfile('profile-1', 'Acme Traders', '29AAEPM0111C1Z3')],
        }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/sales') && method === 'POST') {
        const salePayload = JSON.parse(String(init?.body ?? '{}')) as Record<string, unknown>;
        capturedSalePayload = salePayload;
        salesRecords = [
          {
            sale_id: 'sale-1',
            customer_profile_id: 'profile-1',
            invoice_number: 'SINV-BLRFLAGSHIP-0001',
            customer_name: 'Acme Traders',
            invoice_kind: 'B2B',
            irn_status: 'NOT_REQUIRED',
            payment_method: 'Cash',
            promotion_code: null,
            customer_voucher_id: 'voucher-1',
            customer_voucher_name: 'Welcome voucher',
            customer_voucher_discount_total: 15,
            promotion_discount_amount: 0,
            store_credit_amount: 0,
            loyalty_points_redeemed: 0,
            loyalty_discount_amount: 0,
            loyalty_points_earned: 1,
            grand_total: 82.43,
            issued_on: '2026-04-17',
          },
        ];
        return jsonResponse(buildSaleResponse({
          customer_profile_id: 'profile-1',
          customer_name: 'Acme Traders',
          customer_gstin: '29AAEPM0111C1Z3',
          invoice_kind: 'B2B',
          grand_total: 82.43,
          payment: { payment_method: 'Cash', amount: 82.43 },
          customer_voucher_id: 'voucher-1',
          customer_voucher_name: 'Welcome voucher',
          customer_voucher_discount_total: 15,
          promotion_code: null,
          promotion_discount_amount: 0,
        })) as never;
      }

      throw new Error(`Unexpected fetch call: ${method} ${url}`);
    }) as typeof fetch;

    render(<App />);

    fireEvent.change(screen.getByLabelText('Korsenex token'), {
      target: { value: 'stub:sub=cashier-1;email=cashier@acme.local;name=Counter Cashier' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Start runtime session' }));

    expect(await screen.findByText('Counter Cashier')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Customer profile search'), { target: { value: 'Acme' } });
    fireEvent.click(screen.getByRole('button', { name: 'Find customer profiles' }));
    fireEvent.click(await screen.findByRole('button', { name: /Use customer profile Acme Traders/i }));

    expect(await screen.findByText('Apply voucher VCH-0001')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Apply voucher VCH-0001' }));
    expect(await screen.findByText('Welcome voucher (15)')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Promotion code'), { target: { value: 'WELCOME20' } });
    expect(await screen.findByText('None')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Apply voucher VCH-0001' }));
    expect(await screen.findByText('Welcome voucher (15)')).toBeInTheDocument();
    expect(screen.getByLabelText('Promotion code')).toHaveValue('');

    fireEvent.click(screen.getByRole('button', { name: 'Create sales invoice' }));

    await waitFor(() => {
      expect(capturedSalePayload).not.toBeNull();
      expect(capturedSalePayload!).toMatchObject({
        customer_profile_id: 'profile-1',
        customer_voucher_id: 'voucher-1',
      });
      expect(capturedSalePayload?.promotion_code).toBeNull();
    });
  });

  test('passes the selected customer profile into Cashfree checkout session creation', async () => {
    let capturedCheckoutPayload: Record<string, unknown> | null = null;

    globalThis.fetch = vi.fn(async (input, init) => {
      const url = String(input);
      const method = init?.method ?? 'GET';

      if (url.endsWith('/v1/auth/oidc/exchange') && method === 'POST') {
        return jsonResponse({ access_token: 'session-cashier', token_type: 'Bearer' }) as never;
      }
      if (url.endsWith('/v1/auth/me')) {
        return jsonResponse({
          user_id: 'user-cashier',
          email: 'cashier@acme.local',
          full_name: 'Counter Cashier',
          is_platform_admin: false,
          tenant_memberships: [],
          branch_memberships: [{ tenant_id: 'tenant-acme', branch_id: 'branch-1', role_name: 'cashier', status: 'ACTIVE' }],
        }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme')) {
        return jsonResponse({
          id: 'tenant-acme',
          name: 'Acme Retail',
          slug: 'acme-retail',
          status: 'ACTIVE',
          onboarding_status: 'BRANCH_READY',
        }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches')) {
        return jsonResponse({
          records: [{ branch_id: 'branch-1', tenant_id: 'tenant-acme', name: 'Bengaluru Flagship', code: 'blr-flagship', status: 'ACTIVE' }],
        }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/catalog-items')) {
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
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/inventory-snapshot')) {
        return jsonResponse({
          records: [
            {
              product_id: 'product-1',
              product_name: 'Classic Tea',
              sku_code: 'tea-classic-250g',
              stock_on_hand: 24,
              last_entry_type: 'PURCHASE_RECEIPT',
            },
          ],
        }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/sales') && method === 'GET') {
        return jsonResponse({ records: [] }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/runtime/devices')) {
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
              assigned_staff_profile_id: null,
              assigned_staff_full_name: null,
            },
          ],
        }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/checkout-payment-sessions') && method === 'GET') {
        return jsonResponse({ records: [] }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/loyalty-program') && method === 'GET') {
        return jsonResponse(buildLoyaltyProgramResponse()) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/customer-profiles/profile-1/store-credit') && method === 'GET') {
        return jsonResponse(buildStoreCreditResponse('profile-1')) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/customer-profiles/profile-1/vouchers') && method === 'GET') {
        return jsonResponse({ records: buildCustomerVouchers('profile-1') }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/customer-profiles/profile-1/loyalty') && method === 'GET') {
        return jsonResponse(buildCustomerLoyaltyResponse('profile-1')) as never;
      }
      if (url.includes('/v1/tenants/tenant-acme/customer-profiles') && method === 'GET') {
        return jsonResponse({
          records: [buildCustomerProfile('profile-1', 'Acme Traders', '29AAEPM0111C1Z3')],
        }) as never;
      }
      if (url.endsWith('/v1/tenants/tenant-acme/branches/branch-1/checkout-payment-sessions') && method === 'POST') {
        const checkoutPayload = JSON.parse(String(init?.body ?? '{}')) as Record<string, unknown>;
        capturedCheckoutPayload = checkoutPayload;
        return jsonResponse({
          id: 'checkout-1',
          tenant_id: 'tenant-acme',
          branch_id: 'branch-1',
          customer_profile_id: checkoutPayload.customer_profile_id ?? null,
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
          action_expires_at: '2026-04-16T10:10:00.000Z',
          qr_payload: { format: 'upi_qr', value: 'upi://pay?tr=cf_order_checkout-1' },
          qr_expires_at: '2026-04-16T10:10:00.000Z',
          last_error_message: null,
          last_reconciled_at: '2026-04-16T10:01:00.000Z',
          recovery_state: 'ACTIVE',
          sale: null,
        }) as never;
      }

      throw new Error(`Unexpected fetch call: ${method} ${url}`);
    }) as typeof fetch;

    render(<App />);

    fireEvent.change(screen.getByLabelText('Korsenex token'), {
      target: { value: 'stub:sub=cashier-1;email=cashier@acme.local;name=Counter Cashier' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Start runtime session' }));

    expect(await screen.findByText('Counter Cashier')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Customer profile search'), { target: { value: 'Acme' } });
    fireEvent.click(screen.getByRole('button', { name: 'Find customer profiles' }));
    fireEvent.click(await screen.findByRole('button', { name: /Use customer profile Acme Traders/i }));
    expect(await screen.findByText('Available store credit')).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Apply store credit amount'), { target: { value: '30' } });
    fireEvent.change(screen.getByLabelText('Redeem loyalty points'), { target: { value: '200' } });
    fireEvent.change(screen.getByLabelText('Sale quantity'), { target: { value: '4' } });
    fireEvent.change(screen.getByLabelText('Payment method'), { target: { value: 'CASHFREE_UPI_QR' } });
    fireEvent.click(screen.getByRole('button', { name: 'Start branded UPI QR' }));

    await waitFor(() => {
      expect(capturedCheckoutPayload).not.toBeNull();
      expect(capturedCheckoutPayload!).toMatchObject({
        customer_profile_id: 'profile-1',
        customer_name: 'Acme Traders',
        customer_gstin: '29AAEPM0111C1Z3',
        loyalty_points_to_redeem: 200,
        store_credit_amount: 30,
      });
    });
  });
});
