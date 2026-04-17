/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { OwnerCustomerInsightsSection } from './OwnerCustomerInsightsSection';

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

describe('owner customer insights section', () => {
  const originalFetch = globalThis.fetch;
  let profileStatus: 'ACTIVE' | 'ARCHIVED';
  let profileName: string;
  let storeCreditAvailableBalance: number;
  let storeCreditIssuedTotal: number;
  let storeCreditRedeemedTotal: number;
  let storeCreditAdjustedTotal: number;
  let storeCreditLots: Array<{
    id: string;
    source_type: string;
    source_reference_id?: string | null;
    original_amount: number;
    remaining_amount: number;
    status: string;
    issued_at: string;
    branch_id?: string | null;
  }>;
  let storeCreditLedgerEntries: Array<{
    id: string;
    entry_type: string;
    source_type: string;
    source_reference_id?: string | null;
    amount: number;
    running_balance: number;
    note?: string | null;
    lot_id?: string | null;
    branch_id?: string | null;
    created_at: string;
  }>;
  let loyaltyProgramStatus: 'ACTIVE' | 'DISABLED';
  let loyaltyEarnRate: number;
  let loyaltyRedeemStepPoints: number;
  let loyaltyRedeemValuePerStep: number;
  let loyaltyMinimumRedeemPoints: number;
  let loyaltyAvailablePoints: number;
  let loyaltyEarnedTotal: number;
  let loyaltyRedeemedTotal: number;
  let loyaltyAdjustedTotal: number;
  let loyaltyLedgerEntries: Array<{
    id: string;
    entry_type: string;
    source_type: string;
    source_reference_id?: string | null;
    points_delta: number;
    balance_after: number;
    note?: string | null;
    branch_id?: string | null;
    created_at: string;
  }>;
  let customerVouchers: Array<{
    id: string;
    tenant_id: string;
    campaign_id: string;
    customer_profile_id: string;
    voucher_code: string;
    voucher_name: string;
    voucher_amount: number;
    status: string;
    issued_note?: string | null;
    redeemed_sale_id?: string | null;
    created_at: string;
    updated_at: string;
    redeemed_at?: string | null;
  }>;
  let profileDefaultPriceTierId: string | null;
  let profileDefaultPriceTierCode: string | null;
  let profileDefaultPriceTierDisplayName: string | null;

  function buildStoreCreditResponse() {
    return {
      customer_profile_id: 'profile-1',
      available_balance: storeCreditAvailableBalance,
      issued_total: storeCreditIssuedTotal,
      redeemed_total: storeCreditRedeemedTotal,
      adjusted_total: storeCreditAdjustedTotal,
      lots: storeCreditLots,
      ledger_entries: storeCreditLedgerEntries,
    };
  }

  function buildLoyaltyProgramResponse() {
    return {
      status: loyaltyProgramStatus,
      earn_points_per_currency_unit: loyaltyEarnRate,
      redeem_step_points: loyaltyRedeemStepPoints,
      redeem_value_per_step: loyaltyRedeemValuePerStep,
      minimum_redeem_points: loyaltyMinimumRedeemPoints,
    };
  }

  function buildCustomerLoyaltyResponse() {
    return {
      customer_profile_id: 'profile-1',
      available_points: loyaltyAvailablePoints,
      earned_total: loyaltyEarnedTotal,
      redeemed_total: loyaltyRedeemedTotal,
      adjusted_total: loyaltyAdjustedTotal,
      ledger_entries: loyaltyLedgerEntries,
    };
  }

  beforeEach(() => {
    profileStatus = 'ACTIVE';
    profileName = 'Acme Traders';
    storeCreditAvailableBalance = 250;
    storeCreditIssuedTotal = 250;
    storeCreditRedeemedTotal = 0;
    storeCreditAdjustedTotal = 0;
    storeCreditLots = [
      {
        id: 'lot-1',
        source_type: 'RETURN_REFUND',
        source_reference_id: 'sale-return-1',
        original_amount: 250,
        remaining_amount: 250,
        status: 'ACTIVE',
        issued_at: '2026-04-16T09:20:00Z',
        branch_id: 'branch-1',
      },
    ];
    storeCreditLedgerEntries = [
      {
        id: 'ledger-1',
        entry_type: 'ISSUED',
        source_type: 'RETURN_REFUND',
        source_reference_id: 'sale-return-1',
        amount: 250,
        running_balance: 250,
        note: 'Refunded to store credit',
        lot_id: 'lot-1',
        branch_id: 'branch-1',
        created_at: '2026-04-16T09:20:00Z',
      },
    ];
    loyaltyProgramStatus = 'ACTIVE';
    loyaltyEarnRate = 1;
    loyaltyRedeemStepPoints = 100;
    loyaltyRedeemValuePerStep = 10;
    loyaltyMinimumRedeemPoints = 200;
    loyaltyAvailablePoints = 300;
    loyaltyEarnedTotal = 120;
    loyaltyRedeemedTotal = 20;
    loyaltyAdjustedTotal = 200;
    profileDefaultPriceTierId = null;
    profileDefaultPriceTierCode = null;
    profileDefaultPriceTierDisplayName = null;
    loyaltyLedgerEntries = [
      {
        id: 'loyalty-ledger-1',
        entry_type: 'ADJUSTED',
        source_type: 'MANUAL_ADJUSTMENT',
        source_reference_id: null,
        points_delta: 200,
        balance_after: 200,
        note: 'Opening points',
        branch_id: null,
        created_at: '2026-04-16T09:10:00Z',
      },
      {
        id: 'loyalty-ledger-2',
        entry_type: 'EARNED',
        source_type: 'SALE_EARN',
        source_reference_id: 'sale-2',
        points_delta: 120,
        balance_after: 320,
        note: 'Sale SINV-BLRFLAGSHIP-0002',
        branch_id: 'branch-1',
        created_at: '2026-04-16T09:35:00Z',
      },
      {
        id: 'loyalty-ledger-3',
        entry_type: 'REDEEMED',
        source_type: 'SALE_REDEMPTION',
        source_reference_id: 'sale-3',
        points_delta: -20,
        balance_after: 300,
        note: 'Sale SINV-BLRFLAGSHIP-0003',
        branch_id: 'branch-1',
        created_at: '2026-04-16T09:45:00Z',
      },
    ];
    customerVouchers = [];

    globalThis.fetch = vi.fn(async (input, init) => {
      const url = String(input);
      const method = init?.method ?? 'GET';
      if (url.endsWith('/loyalty-program') && method === 'GET') {
        return jsonResponse(buildLoyaltyProgramResponse()) as never;
      }
      if (url.endsWith('/loyalty-program') && method === 'PUT') {
        const payload = JSON.parse(String(init?.body ?? '{}'));
        loyaltyProgramStatus = payload.status ?? loyaltyProgramStatus;
        loyaltyEarnRate = Number(payload.earn_points_per_currency_unit ?? loyaltyEarnRate);
        loyaltyRedeemStepPoints = Number(payload.redeem_step_points ?? loyaltyRedeemStepPoints);
        loyaltyRedeemValuePerStep = Number(payload.redeem_value_per_step ?? loyaltyRedeemValuePerStep);
        loyaltyMinimumRedeemPoints = Number(payload.minimum_redeem_points ?? loyaltyMinimumRedeemPoints);
        return jsonResponse(buildLoyaltyProgramResponse()) as never;
      }
      if (url.endsWith('/customer-profiles') && method === 'GET') {
        return jsonResponse({
          records: [
            {
              id: 'profile-1',
              tenant_id: 'tenant-acme',
              full_name: profileName,
              phone: '+919999999999',
              email: 'accounts@acme.example',
              gstin: '29AAEPM0111C1Z3',
              default_note: 'Preferred wholesale buyer',
              tags: ['wholesale', 'priority'],
              default_price_tier_id: profileDefaultPriceTierId,
              default_price_tier_code: profileDefaultPriceTierCode,
              default_price_tier_display_name: profileDefaultPriceTierDisplayName,
              status: profileStatus,
              created_at: '2026-04-16T09:00:00Z',
              updated_at: '2026-04-16T09:00:00Z',
            },
          ],
        }) as never;
      }
      if (url.endsWith('/price-tiers') && method === 'GET') {
        return jsonResponse({
          records: [
            {
              id: 'tier-1',
              tenant_id: 'tenant-acme',
              code: 'WHOLESALE',
              display_name: 'Wholesale',
              status: 'ACTIVE',
              created_at: '2026-04-17T08:00:00Z',
              updated_at: '2026-04-17T08:00:00Z',
            },
          ],
        }) as never;
      }
      if (url.endsWith('/customer-profiles/profile-1') && method === 'GET') {
        return jsonResponse({
          id: 'profile-1',
          tenant_id: 'tenant-acme',
          full_name: profileName,
          phone: '+919999999999',
          email: 'accounts@acme.example',
          gstin: '29AAEPM0111C1Z3',
          default_note: 'Preferred wholesale buyer',
          tags: ['wholesale', 'priority'],
          default_price_tier_id: profileDefaultPriceTierId,
          default_price_tier_code: profileDefaultPriceTierCode,
          default_price_tier_display_name: profileDefaultPriceTierDisplayName,
          status: profileStatus,
          created_at: '2026-04-16T09:00:00Z',
          updated_at: '2026-04-16T09:00:00Z',
        }) as never;
      }
      if (url.endsWith('/customer-profiles/profile-1') && method === 'PATCH') {
        const payload = JSON.parse(String(init?.body ?? '{}'));
        profileName = payload.full_name ?? profileName;
        profileDefaultPriceTierId = payload.default_price_tier_id ?? null;
        profileDefaultPriceTierCode = profileDefaultPriceTierId ? 'WHOLESALE' : null;
        profileDefaultPriceTierDisplayName = profileDefaultPriceTierId ? 'Wholesale' : null;
        return jsonResponse({
          id: 'profile-1',
          tenant_id: 'tenant-acme',
          full_name: profileName,
          phone: payload.phone ?? '+919999999999',
          email: payload.email ?? 'accounts@acme.example',
          gstin: payload.gstin ?? '29AAEPM0111C1Z3',
          default_note: payload.default_note ?? 'Preferred wholesale buyer',
          tags: payload.tags ?? ['wholesale', 'priority'],
          default_price_tier_id: profileDefaultPriceTierId,
          default_price_tier_code: profileDefaultPriceTierCode,
          default_price_tier_display_name: profileDefaultPriceTierDisplayName,
          status: profileStatus,
          created_at: '2026-04-16T09:00:00Z',
          updated_at: '2026-04-16T09:05:00Z',
        }) as never;
      }
      if (url.endsWith('/customer-profiles/profile-1/archive') && method === 'POST') {
        profileStatus = 'ARCHIVED';
        return jsonResponse({
          id: 'profile-1',
          tenant_id: 'tenant-acme',
          full_name: profileName,
          phone: '+919999999999',
          email: 'accounts@acme.example',
          gstin: '29AAEPM0111C1Z3',
          default_note: 'Preferred wholesale buyer',
          tags: ['wholesale', 'priority'],
          status: profileStatus,
          created_at: '2026-04-16T09:00:00Z',
          updated_at: '2026-04-16T09:10:00Z',
        }) as never;
      }
      if (url.endsWith('/customer-profiles/profile-1/reactivate') && method === 'POST') {
        profileStatus = 'ACTIVE';
        return jsonResponse({
          id: 'profile-1',
          tenant_id: 'tenant-acme',
          full_name: profileName,
          phone: '+919999999999',
          email: 'accounts@acme.example',
          gstin: '29AAEPM0111C1Z3',
          default_note: 'Preferred wholesale buyer',
          tags: ['wholesale', 'priority'],
          status: profileStatus,
          created_at: '2026-04-16T09:00:00Z',
          updated_at: '2026-04-16T09:15:00Z',
        }) as never;
      }
      if (url.endsWith('/customer-profiles/profile-1/store-credit') && method === 'GET') {
        return jsonResponse(buildStoreCreditResponse()) as never;
      }
      if (url.endsWith('/promotion-campaigns') && method === 'GET') {
        return jsonResponse({
          records: [
            {
              id: 'campaign-voucher-1',
              tenant_id: 'tenant-acme',
              name: 'Customer welcome voucher',
              status: 'ACTIVE',
              trigger_mode: 'ASSIGNED_VOUCHER',
              scope: 'CART',
              discount_type: 'FLAT_AMOUNT',
              discount_value: 50,
              minimum_order_amount: 100,
              maximum_discount_amount: null,
              redemption_limit_total: null,
              redemption_count: 0,
              target_product_ids: [],
              target_category_codes: [],
              created_at: '2026-04-17T09:00:00Z',
              updated_at: '2026-04-17T09:00:00Z',
              codes: [],
            },
          ],
        }) as never;
      }
      if (url.endsWith('/customer-profiles/profile-1/vouchers') && method === 'GET') {
        return jsonResponse({ records: customerVouchers }) as never;
      }
      if (url.endsWith('/customer-profiles/profile-1/vouchers') && method === 'POST') {
        const payload = JSON.parse(String(init?.body ?? '{}'));
        const createdVoucher = {
          id: 'voucher-1',
          tenant_id: 'tenant-acme',
          campaign_id: String(payload.campaign_id ?? 'campaign-voucher-1'),
          customer_profile_id: 'profile-1',
          voucher_code: 'VCH-0001',
          voucher_name: 'Customer welcome voucher',
          voucher_amount: 50,
          status: 'ACTIVE',
          issued_note: payload.note ?? null,
          redeemed_sale_id: null,
          created_at: '2026-04-17T09:10:00Z',
          updated_at: '2026-04-17T09:10:00Z',
          redeemed_at: null,
        };
        customerVouchers = [createdVoucher, ...customerVouchers];
        return jsonResponse(createdVoucher) as never;
      }
      if (url.endsWith('/customer-profiles/profile-1/vouchers/voucher-1/cancel') && method === 'POST') {
        const payload = JSON.parse(String(init?.body ?? '{}'));
        customerVouchers = customerVouchers.map((voucher) => (
          voucher.id === 'voucher-1'
            ? { ...voucher, status: 'CANCELED', issued_note: voucher.issued_note, updated_at: '2026-04-17T09:20:00Z' }
            : voucher
        ));
        return jsonResponse({
          ...customerVouchers.find((voucher) => voucher.id === 'voucher-1'),
          issued_note: customerVouchers.find((voucher) => voucher.id === 'voucher-1')?.issued_note ?? null,
          redeemed_sale_id: null,
          redeemed_at: null,
          canceled_note: payload.note ?? null,
        }) as never;
      }
      if (url.endsWith('/customer-profiles/profile-1/loyalty') && method === 'GET') {
        return jsonResponse(buildCustomerLoyaltyResponse()) as never;
      }
      if (url.endsWith('/customer-profiles/profile-1/loyalty/adjust') && method === 'POST') {
        const payload = JSON.parse(String(init?.body ?? '{}'));
        const pointsDelta = Number(payload.points_delta ?? 0);
        loyaltyAvailablePoints += pointsDelta;
        loyaltyAdjustedTotal += pointsDelta;
        loyaltyLedgerEntries = [
          {
            id: 'loyalty-ledger-4',
            entry_type: 'ADJUSTED',
            source_type: 'MANUAL_ADJUSTMENT',
            source_reference_id: null,
            points_delta: pointsDelta,
            balance_after: loyaltyAvailablePoints,
            note: payload.note ?? null,
            branch_id: null,
            created_at: '2026-04-16T09:55:00Z',
          },
          ...loyaltyLedgerEntries,
        ];
        return jsonResponse(buildCustomerLoyaltyResponse()) as never;
      }
      if (url.endsWith('/customer-profiles/profile-1/store-credit/issue') && method === 'POST') {
        const payload = JSON.parse(String(init?.body ?? '{}'));
        const amount = Number(payload.amount ?? 0);
        storeCreditAvailableBalance += amount;
        storeCreditIssuedTotal += amount;
        storeCreditLots = [
          {
            id: 'lot-2',
            source_type: 'MANUAL_ISSUE',
            source_reference_id: null,
            original_amount: amount,
            remaining_amount: amount,
            status: 'ACTIVE',
            issued_at: '2026-04-16T09:30:00Z',
            branch_id: 'branch-1',
          },
          ...storeCreditLots,
        ];
        storeCreditLedgerEntries = [
          {
            id: 'ledger-2',
            entry_type: 'ISSUED',
            source_type: 'MANUAL_ISSUE',
            source_reference_id: null,
            amount,
            running_balance: storeCreditAvailableBalance,
            note: payload.note ?? null,
            lot_id: 'lot-2',
            branch_id: 'branch-1',
            created_at: '2026-04-16T09:30:00Z',
          },
          ...storeCreditLedgerEntries,
        ];
        return jsonResponse(buildStoreCreditResponse()) as never;
      }
      if (url.endsWith('/customer-profiles/profile-1/store-credit/adjust') && method === 'POST') {
        const payload = JSON.parse(String(init?.body ?? '{}'));
        const amountDelta = Number(payload.amount_delta ?? 0);
        storeCreditAvailableBalance += amountDelta;
        storeCreditAdjustedTotal += amountDelta;
        storeCreditLedgerEntries = [
          {
            id: 'ledger-3',
            entry_type: 'ADJUSTED',
            source_type: 'MANUAL_ADJUSTMENT',
            source_reference_id: null,
            amount: amountDelta,
            running_balance: storeCreditAvailableBalance,
            note: payload.note ?? null,
            lot_id: null,
            branch_id: 'branch-1',
            created_at: '2026-04-16T09:40:00Z',
          },
          ...storeCreditLedgerEntries,
        ];
        return jsonResponse(buildStoreCreditResponse()) as never;
      }
      if (url.includes('/customers') && !url.includes('/history')) {
        return jsonResponse({
          records: [
            {
              customer_id: 'profile-1',
              customer_profile_id: 'profile-1',
              name: profileName,
              phone: '+919999999999',
              email: 'accounts@acme.example',
              gstin: '29AAEPM0111C1Z3',
              visit_count: 2,
              lifetime_value: 582.75,
              last_sale_id: 'sale-2',
              last_invoice_number: 'SINV-BLRFLAGSHIP-0002',
              last_branch_id: 'branch-1',
            },
          ],
        }) as never;
      }
      if (url.includes('/customer-report')) {
        return jsonResponse({
          branch_id: 'branch-1',
          customer_count: 1,
          repeat_customer_count: 1,
          anonymous_sales_count: 1,
          anonymous_sales_total: 97.12,
          top_customers: [
            {
              customer_id: 'profile-1',
              customer_profile_id: 'profile-1',
              customer_name: profileName,
              sales_count: 2,
              sales_total: 582.75,
              last_invoice_number: 'SINV-BLRFLAGSHIP-0002',
            },
          ],
          return_activity: [
            {
              customer_id: 'profile-1',
              customer_profile_id: 'profile-1',
              customer_name: profileName,
              return_count: 1,
              credit_note_total: 97.12,
              exchange_count: 1,
            },
          ],
        }) as never;
      }
      if (url.includes('/customers/profile-1/history')) {
        return jsonResponse({
          customer: {
            customer_id: 'profile-1',
            customer_profile_id: 'profile-1',
            name: profileName,
            phone: '+919999999999',
            email: 'accounts@acme.example',
            gstin: '29AAEPM0111C1Z3',
            visit_count: 2,
            lifetime_value: 582.75,
            last_sale_id: 'sale-2',
          },
          sales_summary: {
            sales_count: 2,
            sales_total: 582.75,
            return_count: 1,
            credit_note_total: 97.12,
            exchange_count: 1,
          },
          sales: [
            {
              sale_id: 'sale-1',
              branch_id: 'branch-1',
              invoice_id: 'invoice-1',
              invoice_number: 'SINV-BLRFLAGSHIP-0001',
              grand_total: 291.38,
              payment_method: 'Cash',
            },
            {
              sale_id: 'sale-2',
              branch_id: 'branch-1',
              invoice_id: 'invoice-2',
              invoice_number: 'SINV-BLRFLAGSHIP-0002',
              grand_total: 291.37,
              payment_method: 'MIXED',
            },
          ],
          returns: [],
          exchanges: [],
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

  test('loads customer profiles alongside reporting and selected history', async () => {
    render(
      <OwnerCustomerInsightsSection
        accessToken="session-owner"
        tenantId="tenant-acme"
        branchId="branch-1"
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Load customer insights' }));

    expect(await screen.findByRole('button', { name: /Acme Traders \(29AAEPM0111C1Z3\) ACTIVE/ })).toBeInTheDocument();
    expect(screen.getByText('Repeat customers')).toBeInTheDocument();
    expect(screen.getByText('Sales history')).toBeInTheDocument();
    expect(screen.getByLabelText('Customer profile search')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Acme Traders')).toBeInTheDocument();
    expect(screen.getByDisplayValue('+919999999999')).toBeInTheDocument();
    expect(screen.getByDisplayValue('accounts@acme.example')).toBeInTheDocument();
    expect(screen.getByDisplayValue('wholesale, priority')).toBeInTheDocument();
  });

  test('updates and archives or reactivates the selected customer profile', async () => {
    render(
      <OwnerCustomerInsightsSection
        accessToken="session-owner"
        tenantId="tenant-acme"
        branchId="branch-1"
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Load customer insights' }));

    const nameField = await screen.findByLabelText('Profile full name');
    fireEvent.change(nameField, { target: { value: 'Acme Traders LLP' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save customer profile' }));

    await waitFor(() => {
      const updateCall = vi.mocked(globalThis.fetch).mock.calls.find(
        ([url, init]) =>
          String(url).includes('/v1/tenants/tenant-acme/customer-profiles/profile-1') &&
          init?.method === 'PATCH',
      );
      expect(updateCall).toBeDefined();
      expect(JSON.parse(String(updateCall?.[1]?.body ?? '{}')).full_name).toBe('Acme Traders LLP');
    });

    fireEvent.click(screen.getByRole('button', { name: 'Archive customer profile' }));
    expect(await screen.findByText('ARCHIVED')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Reactivate customer profile' }));
    expect(await screen.findByText('ACTIVE')).toBeInTheDocument();
  });

  test('loads selected customer store credit summary and ledger', async () => {
    render(
      <OwnerCustomerInsightsSection
        accessToken="session-owner"
        tenantId="tenant-acme"
        branchId="branch-1"
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Load customer insights' }));

    expect(await screen.findByText('Available store credit')).toBeInTheDocument();
    expect(screen.getAllByText('250').length).toBeGreaterThan(0);
    expect(screen.getByText(/RETURN_REFUND/)).toBeInTheDocument();
    expect(screen.getByText(/Refunded to store credit/)).toBeInTheDocument();
  });

  test('issues and adjusts store credit for the selected customer profile', async () => {
    render(
      <OwnerCustomerInsightsSection
        accessToken="session-owner"
        tenantId="tenant-acme"
        branchId="branch-1"
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Load customer insights' }));
    await screen.findByText('Available store credit');

    fireEvent.change(screen.getByLabelText('Issue store credit amount'), { target: { value: '75' } });
    fireEvent.change(screen.getByLabelText('Issue store credit note'), { target: { value: 'Festival goodwill' } });
    fireEvent.click(screen.getByRole('button', { name: 'Issue store credit' }));

    await waitFor(() => {
      const issueCall = vi.mocked(globalThis.fetch).mock.calls.find(
        ([url, init]) =>
          String(url).includes('/v1/tenants/tenant-acme/customer-profiles/profile-1/store-credit/issue') &&
          init?.method === 'POST',
      );
      expect(issueCall).toBeDefined();
      expect(JSON.parse(String(issueCall?.[1]?.body ?? '{}'))).toEqual({
        amount: 75,
        note: 'Festival goodwill',
      });
    });

    await waitFor(() => {
      expect(screen.getAllByText('325').length).toBeGreaterThan(0);
    });
    expect(screen.getByText(/Festival goodwill/)).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Adjust store credit delta'), { target: { value: '-25' } });
    fireEvent.change(screen.getByLabelText('Adjust store credit note'), { target: { value: 'Counter correction' } });
    fireEvent.click(screen.getByRole('button', { name: 'Adjust store credit' }));

    await waitFor(() => {
      const adjustCall = vi.mocked(globalThis.fetch).mock.calls.find(
        ([url, init]) =>
          String(url).includes('/v1/tenants/tenant-acme/customer-profiles/profile-1/store-credit/adjust') &&
          init?.method === 'POST',
      );
      expect(adjustCall).toBeDefined();
      expect(JSON.parse(String(adjustCall?.[1]?.body ?? '{}'))).toEqual({
        amount_delta: -25,
        note: 'Counter correction',
      });
    });

    expect(
      await screen.findByText((content) =>
        content.includes('ADJUSTED')
        && content.includes('MANUAL_ADJUSTMENT')
        && content.includes('-25')
        && content.includes('Counter correction'),
      ),
    ).toBeInTheDocument();
  });

  test('issues and cancels customer vouchers for the selected profile', async () => {
    render(
      <OwnerCustomerInsightsSection
        accessToken="session-owner"
        tenantId="tenant-acme"
        branchId="branch-1"
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Load customer insights' }));
    await screen.findByText('Customer vouchers');

    fireEvent.click(screen.getByRole('button', { name: 'Use voucher campaign Customer welcome voucher' }));
    fireEvent.change(screen.getByLabelText('Issue voucher note'), { target: { value: 'Welcome bonus' } });
    fireEvent.click(screen.getByRole('button', { name: 'Issue customer voucher' }));

    await waitFor(() => {
      const issueCall = vi.mocked(globalThis.fetch).mock.calls.find(
        ([url, init]) =>
          String(url).includes('/v1/tenants/tenant-acme/customer-profiles/profile-1/vouchers')
          && !String(url).includes('/cancel')
          && init?.method === 'POST',
      );
      expect(issueCall).toBeDefined();
      expect(JSON.parse(String(issueCall?.[1]?.body ?? '{}'))).toEqual({
        campaign_id: 'campaign-voucher-1',
        note: 'Welcome bonus',
      });
    });

    expect(await screen.findByText(/Customer welcome voucher VCH-0001 ACTIVE 50/)).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Cancel voucher note'), { target: { value: 'Issued in error' } });
    fireEvent.click(screen.getByRole('button', { name: 'Cancel voucher VCH-0001' }));

    await waitFor(() => {
      const cancelCall = vi.mocked(globalThis.fetch).mock.calls.find(
        ([url, init]) =>
          String(url).includes('/v1/tenants/tenant-acme/customer-profiles/profile-1/vouchers/voucher-1/cancel')
          && init?.method === 'POST',
      );
      expect(cancelCall).toBeDefined();
      expect(JSON.parse(String(cancelCall?.[1]?.body ?? '{}'))).toEqual({
        note: 'Issued in error',
      });
    });

    expect(await screen.findByText(/Customer welcome voucher VCH-0001 CANCELED 50/)).toBeInTheDocument();
  });

  test('assigns a default price tier to the selected customer profile', async () => {
    render(
      <OwnerCustomerInsightsSection
        accessToken="session-owner"
        tenantId="tenant-acme"
        branchId="branch-1"
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Load customer insights' }));
    await screen.findByText('Customer profile management');

    fireEvent.click(screen.getByRole('button', { name: 'Use price tier Wholesale' }));
    fireEvent.click(screen.getByRole('button', { name: 'Save customer profile' }));

    await waitFor(() => {
      const saveCall = vi.mocked(globalThis.fetch).mock.calls.find(
        ([url, init]) =>
          String(url).includes('/v1/tenants/tenant-acme/customer-profiles/profile-1')
          && init?.method === 'PATCH',
      );
      expect(saveCall).toBeDefined();
      expect(JSON.parse(String(saveCall?.[1]?.body ?? '{}'))).toMatchObject({
        default_price_tier_id: 'tier-1',
      });
    });

    expect(await screen.findByText('Wholesale')).toBeInTheDocument();
  });

  test('loads and manages loyalty program and customer loyalty points', async () => {
    render(
      <OwnerCustomerInsightsSection
        accessToken="session-owner"
        tenantId="tenant-acme"
        branchId="branch-1"
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Load customer insights' }));

    expect(await screen.findByText('Loyalty program')).toBeInTheDocument();
    expect(await screen.findByText('Available loyalty points')).toBeInTheDocument();
    expect(screen.getAllByText('300').length).toBeGreaterThan(0);
    expect(screen.getByText(/Opening points/)).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Earn points per currency unit'), { target: { value: '2' } });
    fireEvent.change(screen.getByLabelText('Minimum redeem points'), { target: { value: '500' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save loyalty program' }));

    await waitFor(() => {
      const programCall = vi.mocked(globalThis.fetch).mock.calls.find(
        ([url, init]) => String(url).endsWith('/v1/tenants/tenant-acme/loyalty-program') && init?.method === 'PUT',
      );
      expect(programCall).toBeDefined();
      expect(JSON.parse(String(programCall?.[1]?.body ?? '{}'))).toEqual({
        status: 'ACTIVE',
        earn_points_per_currency_unit: 2,
        redeem_step_points: 100,
        redeem_value_per_step: 10,
        minimum_redeem_points: 500,
      });
    });

    fireEvent.change(screen.getByLabelText('Adjust loyalty points delta'), { target: { value: '50' } });
    fireEvent.change(screen.getByLabelText('Adjust loyalty note'), { target: { value: 'Festival bonus' } });
    fireEvent.click(screen.getByRole('button', { name: 'Adjust loyalty points' }));

    await waitFor(() => {
      const adjustCall = vi.mocked(globalThis.fetch).mock.calls.find(
        ([url, init]) =>
          String(url).includes('/v1/tenants/tenant-acme/customer-profiles/profile-1/loyalty/adjust') &&
          init?.method === 'POST',
      );
      expect(adjustCall).toBeDefined();
      expect(JSON.parse(String(adjustCall?.[1]?.body ?? '{}'))).toEqual({
        points_delta: 50,
        note: 'Festival bonus',
      });
    });

    await waitFor(() => {
      expect(screen.getAllByText('350').length).toBeGreaterThan(0);
    });
    expect(screen.getByText(/Festival bonus/)).toBeInTheDocument();
  });
});
