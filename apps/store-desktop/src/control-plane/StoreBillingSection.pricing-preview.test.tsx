/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { render, screen, within } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';
import { StoreBillingSection } from './StoreBillingSection';
import type { StoreRuntimeWorkspaceState } from './useStoreRuntimeWorkspace';

function buildWorkspace(overrides: Partial<StoreRuntimeWorkspaceState> = {}): StoreRuntimeWorkspaceState {
  return {
    branchCatalogItems: [
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
    customerProfiles: [],
    customerProfileSearchQuery: '',
    selectedCustomerProfile: {
      id: 'profile-1',
      tenant_id: 'tenant-acme',
      full_name: 'Acme Traders',
      phone: '+919999999999',
      email: 'accounts@acme.example',
      gstin: '29AAEPM0111C1Z3',
      status: 'ACTIVE',
      created_at: '2026-04-16T09:00:00Z',
      updated_at: '2026-04-16T09:00:00Z',
    },
    selectedCustomerVouchers: [
      {
        id: 'voucher-1',
        tenant_id: 'tenant-acme',
        campaign_id: 'campaign-voucher-1',
        customer_profile_id: 'profile-1',
        voucher_code: 'VCH-0001',
        voucher_name: 'Welcome voucher',
        voucher_amount: 15,
        status: 'ACTIVE',
        issued_note: 'Welcome gift',
        redeemed_sale_id: null,
        created_at: '2026-04-17T09:00:00Z',
        updated_at: '2026-04-17T09:00:00Z',
        redeemed_at: null,
      },
    ],
    selectedCustomerVoucher: {
      id: 'voucher-1',
      tenant_id: 'tenant-acme',
      campaign_id: 'campaign-voucher-1',
      customer_profile_id: 'profile-1',
      voucher_code: 'VCH-0001',
      voucher_name: 'Welcome voucher',
      voucher_amount: 15,
      status: 'ACTIVE',
      issued_note: 'Welcome gift',
      redeemed_sale_id: null,
      created_at: '2026-04-17T09:00:00Z',
      updated_at: '2026-04-17T09:00:00Z',
      redeemed_at: null,
    },
    selectedCustomerVoucherId: 'voucher-1',
    selectedCustomerStoreCredit: {
      customer_profile_id: 'profile-1',
      available_balance: 120,
      issued_total: 120,
      redeemed_total: 0,
      adjusted_total: 0,
      lots: [],
      ledger_entries: [],
    },
    selectedCustomerLoyalty: {
      customer_profile_id: 'profile-1',
      available_points: 300,
      earned_total: 300,
      redeemed_total: 0,
      adjusted_total: 300,
      ledger_entries: [],
    },
    loyaltyProgram: {
      status: 'ACTIVE',
      earn_points_per_currency_unit: 1,
      redeem_step_points: 100,
      redeem_value_per_step: 10,
      minimum_redeem_points: 200,
    },
    customerName: 'Acme Traders',
    customerGstin: '29AAEPM0111C1Z3',
    promotionCode: 'WELCOME20',
    storeCreditAmount: '10',
    loyaltyPointsToRedeem: '200',
    saleQuantity: '1',
    paymentMethod: 'UPI',
    setCustomerProfileSearchQuery: vi.fn(),
    loadCustomerProfiles: vi.fn(),
    createCustomerProfileFromCheckout: vi.fn(),
    clearSelectedCustomerProfile: vi.fn(),
    selectCustomerProfile: vi.fn(),
    setStoreCreditAmount: vi.fn(),
    setLoyaltyPointsToRedeem: vi.fn(),
    selectCustomerVoucher: vi.fn(),
    clearSelectedCustomerVoucher: vi.fn(),
    setPromotionCode: vi.fn(),
    clearPromotionCode: vi.fn(),
    setCustomerName: vi.fn(),
    setCustomerGstin: vi.fn(),
    setSaleQuantity: vi.fn(),
    setPaymentMethod: vi.fn(),
    createSalesInvoice: vi.fn(),
    isBusy: false,
    isCheckoutPaymentBusy: false,
    isSessionLive: true,
    offlineContinuityReady: false,
    actor: {
      user_id: 'user-cashier',
      email: 'cashier@acme.local',
      full_name: 'Counter Cashier',
      is_platform_admin: false,
      tenant_memberships: [],
      branch_memberships: [{ tenant_id: 'tenant-acme', branch_id: 'branch-1', role_name: 'cashier', status: 'ACTIVE' }],
    },
    checkoutPaymentSession: null,
    checkoutPaymentHistory: [],
    refreshCheckoutPaymentSession: vi.fn(),
    finalizeCheckoutPaymentSession: vi.fn(),
    retryCheckoutPaymentSession: vi.fn(),
    cancelCheckoutPaymentSession: vi.fn(),
    useManualCheckoutFallback: vi.fn(),
    checkoutPricePreview: {
      customer_profile_id: 'profile-1',
      customer_name: 'Acme Traders',
      customer_gstin: '29AAEPM0111C1Z3',
      automatic_campaign: {
        id: 'campaign-auto-1',
        name: 'Tea Auto',
        trigger_mode: 'AUTOMATIC',
        scope: 'ITEM_CATEGORY',
        discount_type: 'PERCENTAGE',
        discount_value: 10,
      },
      promotion_code_campaign: {
        id: 'campaign-code-1',
        code_id: 'code-1',
        code: 'WELCOME20',
        name: 'Welcome Discount',
        trigger_mode: 'CODE',
        scope: 'CART',
        discount_type: 'FLAT_AMOUNT',
        discount_value: 20,
      },
      customer_voucher: {
        id: 'voucher-1',
        voucher_code: 'VCH-0001',
        voucher_name: 'Welcome voucher',
        voucher_amount: 15,
      },
      summary: {
        mrp_total: 120,
        selling_price_subtotal: 92.5,
        automatic_discount_total: 9.25,
        promotion_code_discount_total: 20,
        customer_voucher_discount_total: 15,
        loyalty_discount_total: 20,
        total_discount: 64.25,
        tax_total: 2.41,
        invoice_total: 31.41,
        grand_total: 11.41,
        store_credit_amount: 10,
        final_payable_amount: 1.41,
      },
      lines: [
        {
          product_id: 'product-1',
          product_name: 'Classic Tea',
          sku_code: 'tea-classic-250g',
          quantity: 1,
          mrp: 120,
          unit_selling_price: 92.5,
          automatic_discount_amount: 9.25,
          promotion_code_discount_amount: 20,
          customer_voucher_discount_amount: 15,
          promotion_discount_source: 'AUTOMATIC_ITEM_CATEGORY+CODE+ASSIGNED_VOUCHER',
          taxable_amount: 48.25,
          tax_amount: 2.41,
          line_total: 50.66,
        },
      ],
      tax_lines: [],
    },
    checkoutPricePreviewError: '',
    refreshCheckoutPricePreview: vi.fn(),
    latestSale: null,
    sales: [],
    inventorySnapshot: [],
    ...overrides,
  } as unknown as StoreRuntimeWorkspaceState;
}

describe('store billing section pricing preview', () => {
  test('renders previewed commercial breakdown and settlement posture', () => {
    render(<StoreBillingSection workspace={buildWorkspace()} />);

    const pricingSection = screen.getByText('Checkout pricing').closest('section');
    expect(pricingSection).not.toBeNull();
    const pricingQueries = within(pricingSection as HTMLElement);

    expect(pricingQueries.getByText('Checkout pricing')).toBeInTheDocument();
    expect(pricingQueries.getByText('Tea Auto')).toBeInTheDocument();
    expect(pricingQueries.getByText('WELCOME20')).toBeInTheDocument();
    expect(pricingQueries.getByText('VCH-0001')).toBeInTheDocument();
    expect(pricingQueries.getByText('MRP total')).toBeInTheDocument();
    expect(pricingQueries.getByText('120')).toBeInTheDocument();
    expect(pricingQueries.getByText('Automatic discount')).toBeInTheDocument();
    expect(pricingQueries.getByText('9.25')).toBeInTheDocument();
    expect(pricingQueries.getByText('Code discount')).toBeInTheDocument();
    expect(pricingQueries.getByText('20')).toBeInTheDocument();
    expect(pricingQueries.getByText('Voucher discount')).toBeInTheDocument();
    expect(pricingQueries.getByText('15')).toBeInTheDocument();
    expect(pricingQueries.getByText('Store credit used')).toBeInTheDocument();
    expect(pricingQueries.getByText('10')).toBeInTheDocument();
    expect(pricingQueries.getByText('Remaining payable')).toBeInTheDocument();
    expect(pricingQueries.getByText('1.41')).toBeInTheDocument();
    expect(pricingQueries.getByText('Classic Tea x 1')).toBeInTheDocument();
    expect(pricingQueries.getByText('Discount source')).toBeInTheDocument();
    expect(pricingQueries.getByText('Tea Auto + WELCOME20 + VCH-0001')).toBeInTheDocument();
    expect(screen.getByText('Apply voucher VCH-0001')).toBeInTheDocument();
  });
});
