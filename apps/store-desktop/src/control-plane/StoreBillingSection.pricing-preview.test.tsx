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
      summary: {
        mrp_total: 120,
        selling_price_subtotal: 92.5,
        automatic_discount_total: 9.25,
        promotion_code_discount_total: 20,
        loyalty_discount_total: 20,
        total_discount: 49.25,
        tax_total: 3.16,
        invoice_total: 46.41,
        grand_total: 26.41,
        store_credit_amount: 10,
        final_payable_amount: 16.41,
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
          promotion_discount_source: 'Tea Auto + WELCOME20',
          taxable_amount: 63.25,
          tax_amount: 3.16,
          line_total: 66.41,
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
    expect(pricingQueries.getByText('MRP total')).toBeInTheDocument();
    expect(pricingQueries.getByText('120')).toBeInTheDocument();
    expect(pricingQueries.getByText('Automatic discount')).toBeInTheDocument();
    expect(pricingQueries.getByText('9.25')).toBeInTheDocument();
    expect(pricingQueries.getByText('Code discount')).toBeInTheDocument();
    expect(pricingQueries.getByText('20')).toBeInTheDocument();
    expect(pricingQueries.getByText('Store credit used')).toBeInTheDocument();
    expect(pricingQueries.getByText('10')).toBeInTheDocument();
    expect(pricingQueries.getByText('Remaining payable')).toBeInTheDocument();
    expect(pricingQueries.getByText('16.41')).toBeInTheDocument();
    expect(pricingQueries.getByText('Classic Tea x 1')).toBeInTheDocument();
    expect(pricingQueries.getByText('Discount source')).toBeInTheDocument();
    expect(pricingQueries.getByText('Tea Auto + WELCOME20')).toBeInTheDocument();
  });
});
