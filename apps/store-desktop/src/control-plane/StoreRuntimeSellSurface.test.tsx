/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { render, screen } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';
import type { StoreRuntimeWorkspaceState } from './useStoreRuntimeWorkspace';
import { StoreRuntimeSellSurface } from './storeRuntimeSellSurface';

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
    activeCashierSession: {
      id: 'cashier-session-1',
      status: 'OPEN',
      session_number: 'CS-BLRFLAGSHIP-0001',
      staff_full_name: 'Counter Cashier',
      opening_float_amount: 500,
    },
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
    checkoutPricePreview: {
      mrp_total: 110,
      selling_price_subtotal: 92.5,
      automatic_discount_total: 5,
      promotion_code_discount_total: 0,
      loyalty_discount_total: 0,
      total_discount: 5,
      tax_total: 4.62,
      invoice_total: 97.12,
      final_payable_amount: 97.12,
      lines: [
        {
          product_id: 'product-1',
          product_name: 'Classic Tea',
          quantity: 1,
          mrp: 110,
          unit_selling_price: 92.5,
          taxable_amount: 88,
          tax_amount: 4.62,
          line_total: 92.62,
          promotion_discount_amount: 5,
          promotion_discount_source: 'AUTOMATIC_ITEM_CATEGORY',
        },
      ],
    },
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
          checkoutPaymentSession: {
            id: 'checkout-session-1',
            lifecycle_status: 'ACTION_READY',
            handoff_surface: 'BRANDED_UPI_QR',
            action_payload: {
              kind: 'upi_qr',
              label: 'Korsenex UPI QR',
              value: 'upi://pay?pa=korsenex',
            },
          },
        })}
      />,
    );

    expect(screen.getByRole('button', { name: 'Continue payment' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Finalize sale' })).toBeDisabled();
  });
});
