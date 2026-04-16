import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import type { ControlPlaneCheckoutPaymentSession, ControlPlaneSale } from '@store/types';
import { storeControlPlaneClient } from './client';

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

describe('storeControlPlaneClient promotion payloads', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    globalThis.fetch = vi.fn() as typeof fetch;
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  test('sends promotion_code in direct sale payloads', async () => {
    const sale: ControlPlaneSale = {
      id: 'sale-1',
      tenant_id: 'tenant-1',
      branch_id: 'branch-1',
      customer_profile_id: 'profile-1',
      customer_name: 'Acme Traders',
      customer_gstin: '29AAEPM0111C1Z3',
      invoice_kind: 'B2B',
      irn_status: 'IRN_PENDING',
      invoice_number: 'SINV-BLRFLAGSHIP-0004',
      issued_on: '2026-04-17',
      subtotal: 92.5,
      cgst_total: 2.31,
      sgst_total: 2.31,
      igst_total: 0,
      grand_total: 57.12,
      promotion_campaign_id: 'campaign-1',
      promotion_code_id: 'code-1',
      promotion_code: 'WELCOME20',
      promotion_discount_amount: 20,
      store_credit_amount: 10,
      loyalty_points_redeemed: 200,
      loyalty_discount_amount: 20,
      loyalty_points_earned: 57,
      payment: { payment_method: 'UPI', amount: 47.12 },
      lines: [],
      tax_lines: [],
    };
    vi.mocked(globalThis.fetch).mockResolvedValueOnce(jsonResponse(sale) as never);

    await storeControlPlaneClient.createSale('access-token', 'tenant-1', 'branch-1', {
      customer_profile_id: 'profile-1',
      customer_name: 'Acme Traders',
      customer_gstin: '29AAEPM0111C1Z3',
      payment_method: 'UPI',
      promotion_code: 'WELCOME20',
      store_credit_amount: 10,
      loyalty_points_to_redeem: 200,
      lines: [{ product_id: 'product-1', quantity: 1 }],
    });

    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/v1/tenants/tenant-1/branches/branch-1/sales'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          customer_profile_id: 'profile-1',
          customer_name: 'Acme Traders',
          customer_gstin: '29AAEPM0111C1Z3',
          payment_method: 'UPI',
          promotion_code: 'WELCOME20',
          store_credit_amount: 10,
          loyalty_points_to_redeem: 200,
          lines: [{ product_id: 'product-1', quantity: 1 }],
        }),
      }),
    );
  });

  test('sends promotion_code in checkout payment session payloads', async () => {
    const session: ControlPlaneCheckoutPaymentSession = {
      id: 'checkout-1',
      tenant_id: 'tenant-1',
      branch_id: 'branch-1',
      customer_profile_id: 'profile-1',
      provider_name: 'cashfree',
      provider_order_id: 'cf-order-1',
      provider_payment_session_id: 'cf-ps-1',
      provider_payment_id: null,
      payment_method: 'CASHFREE_UPI_QR',
      handoff_surface: 'BRANDED_UPI_QR',
      provider_payment_mode: 'cashfree_upi',
      lifecycle_status: 'ACTION_READY',
      provider_status: 'ACTIVE',
      order_amount: 57.12,
      currency_code: 'INR',
      promotion_code: 'WELCOME20',
      promotion_discount_amount: 20,
      action_payload: { kind: 'upi_qr', value: 'upi://pay', label: 'Korsenex QR', description: null },
      action_expires_at: null,
      qr_payload: { format: 'upi_qr', value: 'upi://pay' },
      qr_expires_at: null,
      last_error_message: null,
      last_reconciled_at: null,
      recovery_state: 'ACTIVE',
      sale: null,
    };
    vi.mocked(globalThis.fetch).mockResolvedValueOnce(jsonResponse(session) as never);

    await storeControlPlaneClient.createCheckoutPaymentSession('access-token', 'tenant-1', 'branch-1', {
      provider_name: 'cashfree',
      payment_method: 'CASHFREE_UPI_QR',
      handoff_surface: 'BRANDED_UPI_QR',
      provider_payment_mode: 'cashfree_upi',
      customer_profile_id: 'profile-1',
      customer_name: 'Acme Traders',
      customer_gstin: '29AAEPM0111C1Z3',
      promotion_code: 'WELCOME20',
      loyalty_points_to_redeem: 200,
      lines: [{ product_id: 'product-1', quantity: 1 }],
    });

    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/v1/tenants/tenant-1/branches/branch-1/checkout-payment-sessions'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          provider_name: 'cashfree',
          payment_method: 'CASHFREE_UPI_QR',
          handoff_surface: 'BRANDED_UPI_QR',
          provider_payment_mode: 'cashfree_upi',
          customer_profile_id: 'profile-1',
          customer_name: 'Acme Traders',
          customer_gstin: '29AAEPM0111C1Z3',
          promotion_code: 'WELCOME20',
          loyalty_points_to_redeem: 200,
          lines: [{ product_id: 'product-1', quantity: 1 }],
        }),
      }),
    );
  });
});
