/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { render, screen } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';
import type {
  ControlPlaneCashierSession,
  ControlPlaneCheckoutPaymentSession,
  ControlPlaneCheckoutPricePreview,
} from '@store/types';
import type { StoreRuntimeWorkspaceState } from './useStoreRuntimeWorkspace';
import { StoreRuntimeSellSurface } from './storeRuntimeSellSurface';

function createCashierSession(
  overrides: Partial<ControlPlaneCashierSession> = {},
): ControlPlaneCashierSession {
  return {
    id: 'cashier-session-1',
    tenant_id: 'tenant-acme',
    branch_id: 'branch-1',
    attendance_session_id: 'attendance-session-1',
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
    opening_float_amount: 500,
    opening_note: null,
    closing_note: null,
    force_close_reason: null,
    opened_at: '2026-04-19T10:05:00.000Z',
    closed_at: null,
    last_activity_at: '2026-04-19T10:05:00.000Z',
    linked_sales_count: 0,
    linked_returns_count: 0,
    gross_billed_amount: 0,
    ...overrides,
  };
}

function createCheckoutPricePreview(
  overrides: Partial<ControlPlaneCheckoutPricePreview> = {},
): ControlPlaneCheckoutPricePreview {
  return {
    customer_profile_id: 'customer-1',
    customer_name: 'Asha Nair',
    customer_gstin: null,
    automatic_campaign: {
      id: 'campaign-auto-1',
      name: 'Tea Auto',
      trigger_mode: 'AUTOMATIC',
      scope: 'ITEM_CATEGORY',
      discount_type: 'PERCENTAGE',
      discount_value: 10,
    },
    promotion_code_campaign: null,
    customer_voucher: null,
    gift_card: null,
    summary: {
      mrp_total: 110,
      selling_price_subtotal: 92.5,
      automatic_discount_total: 5,
      promotion_code_discount_total: 0,
      customer_voucher_discount_total: 0,
      loyalty_discount_total: 0,
      total_discount: 5,
      tax_total: 4.62,
      invoice_total: 97.12,
      grand_total: 97.12,
      store_credit_amount: 0,
      gift_card_amount: 0,
      final_payable_amount: 97.12,
    },
    lines: [
      {
        product_id: 'product-1',
        product_name: 'Classic Tea',
        sku_code: 'tea-classic-250g',
        quantity: 1,
        serial_numbers: null,
        compliance_profile: null,
        compliance_capture: null,
        mrp: 110,
        unit_selling_price: 92.5,
        automatic_discount_amount: 5,
        promotion_code_discount_amount: 0,
        customer_voucher_discount_amount: 0,
        promotion_discount_source: 'AUTOMATIC_ITEM_CATEGORY',
        taxable_amount: 88,
        tax_amount: 4.62,
        line_total: 92.62,
      },
    ],
    tax_lines: [],
    ...overrides,
  };
}

function createCheckoutPaymentSession(
  overrides: Partial<ControlPlaneCheckoutPaymentSession> = {},
): ControlPlaneCheckoutPaymentSession {
  return {
    id: 'checkout-session-1',
    tenant_id: 'tenant-acme',
    branch_id: 'branch-1',
    cashier_session_id: 'cashier-session-1',
    customer_profile_id: 'customer-1',
    provider_name: 'cashfree',
    provider_order_id: 'cf_order_checkout-1',
    provider_payment_session_id: 'cf_ps_checkout-1',
    provider_payment_id: null,
    payment_method: 'CASHFREE_UPI_QR',
    handoff_surface: 'BRANDED_UPI_QR',
    provider_payment_mode: 'cashfree_upi',
    lifecycle_status: 'ACTION_READY',
    provider_status: 'ACTIVE',
    order_amount: 97.12,
    currency_code: 'INR',
    automatic_campaign_name: 'Tea Auto',
    automatic_discount_total: 5,
    promotion_code: null,
    customer_voucher_id: null,
    customer_voucher_name: null,
    promotion_discount_amount: 5,
    promotion_code_discount_total: 0,
    customer_voucher_discount_total: 0,
    store_credit_amount: 0,
    gift_card_id: null,
    gift_card_code: null,
    gift_card_amount: 0,
    action_payload: {
      kind: 'upi_qr',
      label: 'Korsenex UPI QR',
      value: 'upi://pay?pa=korsenex',
      description: 'Scan with any UPI app to complete the payment.',
    },
    action_expires_at: '2026-04-19T10:15:00.000Z',
    qr_payload: null,
    qr_expires_at: null,
    last_error_message: null,
    last_reconciled_at: '2026-04-19T10:05:00.000Z',
    recovery_state: 'ACTIVE',
    sale: null,
    ...overrides,
  };
}

function buildWorkspace(overrides: Partial<StoreRuntimeWorkspaceState> = {}): StoreRuntimeWorkspaceState {
  return {
    actor: {
      user_id: 'user-cashier',
      email: 'cashier@acme.local',
      full_name: 'Counter Cashier',
      is_platform_admin: false,
      tenant_memberships: [],
      branch_memberships: [{ tenant_id: 'tenant-acme', branch_id: 'branch-1', role_name: 'cashier', status: 'ACTIVE' }],
    },
    isSessionLive: true,
    isBusy: false,
    isCheckoutPaymentBusy: false,
    paymentMethod: 'Cash',
    activeCashierSession: createCashierSession(),
    branchCatalogItems: [
      {
        id: 'catalog-item-1',
        tenant_id: 'tenant-acme',
        branch_id: 'branch-1',
        product_id: 'product-1',
        product_name: 'Classic Tea',
        sku_code: 'tea-classic-250g',
        barcode: '8901234567890',
        tracking_mode: 'NONE',
        availability_status: 'ACTIVE',
        effective_selling_price: 92.5,
        base_selling_price: 92.5,
        gst_rate: 5,
      },
    ],
    inventorySnapshot: [
      {
        product_id: 'product-1',
        product_name: 'Classic Tea',
        sku_code: 'tea-classic-250g',
        stock_on_hand: 24,
        last_entry_type: 'PURCHASE_RECEIPT',
      },
    ],
    saleQuantity: '1',
    setSaleQuantity: vi.fn(),
    saleSerialNumbers: '',
    setSaleSerialNumbers: vi.fn(),
    selectedCustomerProfile: {
      id: 'customer-1',
      tenant_id: 'tenant-acme',
      full_name: 'Asha Nair',
      phone_number: '9999988888',
      default_price_tier_display_name: 'Wholesale',
    },
    selectedCustomerStoreCredit: { available_balance: 120 },
    selectedCustomerLoyalty: { available_points: 1800 },
    selectedCustomerVouchers: [],
    selectedCustomerVoucher: null,
    loyaltyProgram: {
      enabled: true,
      earn_rate_points_per_currency_unit: 1,
      minimum_redeem_points: 100,
      redeem_step_points: 100,
      redeem_step_value: 10,
    },
    checkoutPricePreview: createCheckoutPricePreview(),
    checkoutPaymentSession: null,
    ...overrides,
  } as unknown as StoreRuntimeWorkspaceState;
}

describe('StoreRuntimeSellSurface', () => {
  test('renders cart, customer and totals, and payment posture in distinct panels', () => {
    render(<StoreRuntimeSellSurface workspace={buildWorkspace()} />);

    expect(screen.getByRole('heading', { name: 'Current cart' })).toBeInTheDocument();
    expect(screen.getByText('Classic Tea')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Customer and totals' })).toBeInTheDocument();
    expect(screen.getByText('Asha Nair')).toBeInTheDocument();
    expect(screen.getByText('Invoice total')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Payment and session' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Finalize sale' })).toBeInTheDocument();
  });

  test('switches the primary action hierarchy when a provider-backed payment session is active', () => {
    render(
      <StoreRuntimeSellSurface
        workspace={buildWorkspace({
          paymentMethod: 'CASHFREE_UPI_QR',
          checkoutPaymentSession: createCheckoutPaymentSession(),
        })}
      />,
    );

    expect(screen.getByRole('button', { name: 'Continue payment' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Finalize sale' })).toBeDisabled();
  });
});
