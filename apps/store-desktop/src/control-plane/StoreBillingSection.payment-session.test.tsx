/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';
import { StoreBillingSection } from './StoreBillingSection';
import type { StoreRuntimeWorkspaceState } from './useStoreRuntimeWorkspace';

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
    customerName: 'Acme Traders',
    customerGstin: '29AAEPM0111C1Z3',
    saleQuantity: '4',
    paymentMethod: 'CASHFREE_UPI_QR',
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
    latestSale: null,
    sales: [],
    inventorySnapshot: [],
    checkoutPaymentSession: {
      id: 'checkout-1',
      tenant_id: 'tenant-acme',
      branch_id: 'branch-1',
      provider_name: 'cashfree',
      provider_order_id: 'cf_order_checkout-1',
      provider_payment_session_id: 'cf_ps_checkout-1',
      provider_payment_id: null,
      payment_method: 'CASHFREE_UPI_QR',
      lifecycle_status: 'FAILED',
      provider_status: 'FAILED',
      order_amount: 388.5,
      currency_code: 'INR',
      qr_payload: { format: 'upi_qr', value: 'upi://pay?tr=cf_order_checkout-1' },
      qr_expires_at: '2026-04-15T12:10:00.000Z',
      sale: null,
    },
    cancelCheckoutPaymentSession: vi.fn(),
    retryCheckoutPaymentSession: vi.fn(),
    useManualCheckoutFallback: vi.fn(),
    ...overrides,
  } as unknown as StoreRuntimeWorkspaceState;
}

describe('store billing section payment session states', () => {
  test('renders retry and manual fallback actions for failed Cashfree QR sessions', () => {
    const workspace = createWorkspace();

    render(<StoreBillingSection workspace={workspace} />);

    expect(screen.getByText('Cashfree UPI QR payment')).toBeInTheDocument();
    expect(screen.getByText('FAILED')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Retry Cashfree UPI QR' }));
    expect(workspace.retryCheckoutPaymentSession).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole('button', { name: 'Switch to manual payment' }));
    expect(workspace.useManualCheckoutFallback).toHaveBeenCalledTimes(1);
  });

  test('renders a scannable QR preview and expiry for active Cashfree sessions', () => {
    const workspace = createWorkspace({
      checkoutPaymentSession: {
        id: 'checkout-1',
        tenant_id: 'tenant-acme',
        branch_id: 'branch-1',
        provider_name: 'cashfree',
        provider_order_id: 'cf_order_checkout-1',
        provider_payment_session_id: 'cf_ps_checkout-1',
        provider_payment_id: null,
        payment_method: 'CASHFREE_UPI_QR',
        lifecycle_status: 'QR_READY',
        provider_status: 'ACTIVE',
        order_amount: 388.5,
        currency_code: 'INR',
        qr_payload: { format: 'upi_qr', value: 'upi://pay?tr=cf_order_checkout-1' },
        qr_expires_at: '2026-04-15T12:10:00.000Z',
        sale: null,
      },
    });

    render(<StoreBillingSection workspace={workspace} />);

    expect(screen.getByRole('img', { name: 'Cashfree UPI QR code' })).toBeInTheDocument();
    expect(screen.getByText(/Expires in/i)).toBeInTheDocument();
  });
});
