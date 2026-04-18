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
        tracking_mode: 'STANDARD',
        compliance_profile: 'NONE',
        compliance_config: {},
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
      default_price_tier_id: 'tier-1',
      default_price_tier_code: 'WHOLESALE',
      default_price_tier_display_name: 'Wholesale',
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
    giftCardCode: 'GIFT-1000',
    giftCardAmount: '1.41',
    storeCreditAmount: '10',
    loyaltyPointsToRedeem: '200',
    saleQuantity: '1',
    saleSerialNumbers: '',
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
    setGiftCardCode: vi.fn(),
    setGiftCardAmount: vi.fn(),
    setCustomerName: vi.fn(),
    setCustomerGstin: vi.fn(),
    setSaleQuantity: vi.fn(),
    setSaleSerialNumbers: vi.fn(),
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
      gift_card: {
        id: 'gift-card-1',
        gift_card_code: 'GIFT-1000',
        display_name: 'Diwali gift card',
        status: 'ACTIVE',
        available_balance: 300,
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
        gift_card_amount: 1.41,
        final_payable_amount: 0,
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
    expect(pricingQueries.getByText('GIFT-1000')).toBeInTheDocument();
    expect(screen.getByText(/Wholesale price tier/)).toBeInTheDocument();
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
    expect(pricingQueries.getByText('Gift card used')).toBeInTheDocument();
    expect(pricingQueries.getByText('1.41')).toBeInTheDocument();
    expect(pricingQueries.getByText('Remaining payable')).toBeInTheDocument();
    expect(pricingQueries.getByText('0')).toBeInTheDocument();
    expect(pricingQueries.getByText('Classic Tea x 1')).toBeInTheDocument();
    expect(pricingQueries.getByText('Discount source')).toBeInTheDocument();
    expect(pricingQueries.getByText('Tea Auto + WELCOME20 + VCH-0001')).toBeInTheDocument();
    expect(screen.getByText('Apply voucher VCH-0001')).toBeInTheDocument();
  });

  test('requires exact serial assignments for serialized checkout lines', () => {
    render(
      <StoreBillingSection
        workspace={buildWorkspace({
          branchCatalogItems: [
            {
              id: 'catalog-item-serial-1',
              tenant_id: 'tenant-acme',
              branch_id: 'branch-1',
              product_id: 'product-serial-1',
              product_name: 'Serialized Phone',
              sku_code: 'phone-x1',
              barcode: '8901234567001',
              hsn_sac_code: '8517',
              gst_rate: 18,
              mrp: 15999,
              base_selling_price: 14999,
              selling_price_override: null,
              effective_selling_price: 14999,
              tracking_mode: 'SERIALIZED',
              compliance_profile: 'NONE',
              compliance_config: {},
              availability_status: 'ACTIVE',
            },
          ],
          saleQuantity: '2',
          saleSerialNumbers: 'IMEI-0001',
          checkoutPricePreview: null,
        })}
      />,
    );

    expect(screen.getByLabelText('Serial / IMEI numbers')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Refresh checkout pricing' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Create sales invoice' })).toBeDisabled();
  });

  test('requires prescription capture for RX-required checkout lines', () => {
    render(
      <StoreBillingSection
        workspace={buildWorkspace({
          branchCatalogItems: [
            {
              id: 'catalog-item-rx-1',
              tenant_id: 'tenant-acme',
              branch_id: 'branch-1',
              product_id: 'product-rx-1',
              product_name: 'Prescription Tablet',
              sku_code: 'rx-tablet-10',
              barcode: '8901234567111',
              hsn_sac_code: '3004',
              gst_rate: 12,
              mrp: 340,
              base_selling_price: 320,
              selling_price_override: null,
              effective_selling_price: 320,
              tracking_mode: 'STANDARD',
              compliance_profile: 'RX_REQUIRED',
              compliance_config: {},
              availability_status: 'ACTIVE',
            },
          ],
          saleQuantity: '1',
          saleSerialNumbers: '',
          checkoutPricePreview: null,
          salePrescriptionNumber: '',
          salePatientName: '',
          salePrescriberName: '',
        })}
      />,
    );

    expect(screen.getByLabelText('Prescription number')).toBeInTheDocument();
    expect(screen.getByLabelText('Patient name')).toBeInTheDocument();
    expect(screen.getByLabelText('Prescriber name')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Refresh checkout pricing' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Create sales invoice' })).toBeDisabled();
  });

  test('requires age verification for age-restricted checkout lines', () => {
    render(
      <StoreBillingSection
        workspace={buildWorkspace({
          branchCatalogItems: [
            {
              id: 'catalog-item-age-1',
              tenant_id: 'tenant-acme',
              branch_id: 'branch-1',
              product_id: 'product-age-1',
              product_name: 'Reserve Beverage',
              sku_code: 'bev-reserve-750',
              barcode: '8901234567222',
              hsn_sac_code: '2203',
              gst_rate: 28,
              mrp: 900,
              base_selling_price: 850,
              selling_price_override: null,
              effective_selling_price: 850,
              tracking_mode: 'STANDARD',
              compliance_profile: 'AGE_RESTRICTED',
              compliance_config: { minimum_age: 21 },
              availability_status: 'ACTIVE',
            },
          ],
          saleQuantity: '1',
          saleSerialNumbers: '',
          checkoutPricePreview: null,
          saleAgeVerified: false,
          saleAgeVerificationId: '',
        })}
      />,
    );

    expect(screen.getByText(/Age verification required/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Mark age verified (21+)' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Refresh checkout pricing' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Create sales invoice' })).toBeDisabled();
  });
});
