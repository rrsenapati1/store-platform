/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import type { ControlPlaneCheckoutPaymentSession } from '@store/types';
import { StoreBillingSection } from './StoreBillingSection';
import type { StoreRuntimeWorkspaceState } from './useStoreRuntimeWorkspace';

function createCheckoutPaymentSession(
  overrides: Partial<ControlPlaneCheckoutPaymentSession> = {},
): ControlPlaneCheckoutPaymentSession {
  return {
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
    lifecycle_status: 'FAILED',
    provider_status: 'FAILED',
    order_amount: 388.5,
    currency_code: 'INR',
    promotion_code: null,
    promotion_discount_amount: 0,
    action_payload: {
      kind: 'upi_qr',
      value: 'upi://pay?tr=cf_order_checkout-1',
      label: 'Korsenex customer UPI QR',
      description: 'Scan with any UPI app to complete this checkout.',
    },
    action_expires_at: '2026-04-15T12:10:00.000Z',
    qr_payload: { format: 'upi_qr', value: 'upi://pay?tr=cf_order_checkout-1' },
    qr_expires_at: '2026-04-15T12:10:00.000Z',
    last_error_message: 'Cashfree reported FAILED',
    last_reconciled_at: '2026-04-15T12:01:00.000Z',
    recovery_state: 'RETRYABLE',
    sale: null,
    ...overrides,
  };
}

function createWorkspace(overrides: Partial<StoreRuntimeWorkspaceState> = {}): StoreRuntimeWorkspaceState {
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
    selectedCustomerProfile: null,
    customerName: 'Acme Traders',
    customerGstin: '29AAEPM0111C1Z3',
    promotionCode: '',
    clearSelectedCustomerProfile: vi.fn(),
    clearPromotionCode: vi.fn(),
    createCustomerProfileFromCheckout: vi.fn(),
    saleQuantity: '4',
    paymentMethod: 'CASHFREE_UPI_QR',
    loadCustomerProfiles: vi.fn(),
    selectCustomerProfile: vi.fn(),
    setCustomerProfileSearchQuery: vi.fn(),
    setCustomerName: vi.fn(),
    setCustomerGstin: vi.fn(),
    setPromotionCode: vi.fn(),
    setSaleQuantity: vi.fn(),
    setPaymentMethod: vi.fn(),
    createSalesInvoice: vi.fn(),
    isBusy: false,
    isCheckoutPaymentBusy: false,
    isSessionLive: true,
    offlineContinuityReady: false,
    checkoutPaymentHistory: [],
    actor: {
      user_id: 'user-cashier',
      email: 'cashier@acme.local',
      full_name: 'Counter Cashier',
      is_platform_admin: false,
      tenant_memberships: [],
      branch_memberships: [{ tenant_id: 'tenant-acme', branch_id: 'branch-1', role_name: 'cashier', status: 'ACTIVE' }],
    },
    latestSale: null,
    sales: [],
    inventorySnapshot: [],
    checkoutPaymentSession: createCheckoutPaymentSession(),
    cancelCheckoutPaymentSession: vi.fn(),
    finalizeCheckoutPaymentSession: vi.fn(),
    refreshCheckoutPaymentSession: vi.fn(),
    retryCheckoutPaymentSession: vi.fn(),
    listCheckoutPaymentHistory: vi.fn(),
    useManualCheckoutFallback: vi.fn(),
    ...overrides,
  } as unknown as StoreRuntimeWorkspaceState;
}

describe('store billing section payment session states', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-04-15T12:00:00.000Z'));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  test('renders retry and manual fallback actions for failed Cashfree QR sessions', () => {
    const workspace = createWorkspace();

    render(<StoreBillingSection workspace={workspace} />);

    expect(screen.getByText('Korsenex UPI QR')).toBeInTheDocument();
    expect(screen.getByText('FAILED')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Retry payment session' }));
    expect(workspace.retryCheckoutPaymentSession).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole('button', { name: 'Switch to manual payment' }));
    expect(workspace.useManualCheckoutFallback).toHaveBeenCalledTimes(1);
  });

  test('renders a scannable QR preview and expiry for active branded QR sessions', () => {
    const workspace = createWorkspace({
      checkoutPaymentSession: createCheckoutPaymentSession({
        lifecycle_status: 'ACTION_READY',
        provider_status: 'ACTIVE',
        last_error_message: null,
        recovery_state: 'ACTIVE',
      }),
    });

    render(<StoreBillingSection workspace={workspace} />);

    expect(screen.getByRole('img', { name: 'Cashfree UPI QR code' })).toBeInTheDocument();
    expect(screen.getByText(/Expires in/i)).toBeInTheDocument();
  });

  test('renders hosted checkout actions and recovery history for terminal and phone handoff sessions', () => {
    const workspace = createWorkspace({
      paymentMethod: 'CASHFREE_HOSTED_PHONE',
      checkoutPaymentSession: createCheckoutPaymentSession({
        payment_method: 'CASHFREE_HOSTED_PHONE',
        handoff_surface: 'HOSTED_PHONE',
        provider_payment_mode: 'cashfree_checkout',
        lifecycle_status: 'ACTION_READY',
        provider_status: 'ACTIVE',
        action_payload: {
          kind: 'hosted_url',
          value: 'https://payments.store.local/checkout/cf_order_checkout-1?surface=hosted_phone',
          label: 'Customer phone checkout',
          description: 'Scan or open this link on the customer phone.',
        },
        action_expires_at: '2026-04-15T12:10:00.000Z',
        qr_payload: {
          format: 'hosted_url',
          value: 'https://payments.store.local/checkout/cf_order_checkout-1?surface=hosted_phone',
        },
        qr_expires_at: '2026-04-15T12:10:00.000Z',
        last_error_message: null,
        recovery_state: 'ACTIVE',
      }),
      checkoutPaymentHistory: [
        createCheckoutPaymentSession({
          id: 'checkout-history-1',
          provider_order_id: 'cf_order_history_1',
          payment_method: 'CASHFREE_HOSTED_TERMINAL',
          handoff_surface: 'HOSTED_TERMINAL',
          provider_payment_mode: 'cashfree_checkout',
          lifecycle_status: 'CONFIRMED',
          provider_status: 'SUCCESS',
          action_payload: {
            kind: 'hosted_url',
            value: 'https://payments.store.local/checkout/cf_order_history_1?surface=hosted_terminal',
            label: 'Terminal hosted checkout',
            description: 'Continue payment on this terminal.',
          },
          action_expires_at: '2026-04-15T12:10:00.000Z',
          qr_payload: null,
          qr_expires_at: null,
          last_error_message: 'Awaiting finalization',
          recovery_state: 'FINALIZE_REQUIRED',
        }),
      ],
    });

    render(<StoreBillingSection workspace={workspace} />);

    expect(screen.getByText('Cashfree hosted checkout')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Customer phone checkout' })).toHaveAttribute(
      'href',
      'https://payments.store.local/checkout/cf_order_checkout-1?surface=hosted_phone',
    );
    expect(screen.getAllByRole('button', { name: 'Refresh payment status' }).length).toBeGreaterThan(0);
    expect(screen.getByRole('button', { name: 'Finalize confirmed payment' })).toBeInTheDocument();
    expect(screen.getByText('Recent payment sessions')).toBeInTheDocument();
    expect(screen.getByText('cf_order_history_1')).toBeInTheDocument();
  });
});
