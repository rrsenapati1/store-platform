import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import type { ControlPlaneCheckoutPaymentSession, ControlPlaneCheckoutPricePreview } from '@store/types';
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

describe('storeControlPlaneClient pricing preview payloads', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    globalThis.fetch = vi.fn() as typeof fetch;
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  test('sends checkout-price-preview payloads with voucher, promotion, loyalty, store credit, and gift card posture', async () => {
    const preview: ControlPlaneCheckoutPricePreview = {
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
          promotion_discount_source: 'Tea Auto + WELCOME20',
          taxable_amount: 48.25,
          tax_amount: 2.41,
          line_total: 50.66,
        },
      ],
      tax_lines: [],
    };
    vi.mocked(globalThis.fetch).mockResolvedValueOnce(jsonResponse(preview) as never);

    await storeControlPlaneClient.getCheckoutPricePreview('access-token', 'tenant-1', 'branch-1', {
      cashier_session_id: 'cashier-session-1',
      customer_profile_id: 'profile-1',
      customer_name: 'Acme Traders',
      customer_gstin: '29AAEPM0111C1Z3',
      promotion_code: 'WELCOME20',
      customer_voucher_id: 'voucher-1',
      loyalty_points_to_redeem: 200,
      store_credit_amount: 10,
      gift_card_code: 'GIFT-1000',
      gift_card_amount: 1.41,
      lines: [{ product_id: 'product-1', quantity: 1 }],
    });

    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/v1/tenants/tenant-1/branches/branch-1/checkout-price-preview'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          cashier_session_id: 'cashier-session-1',
          customer_profile_id: 'profile-1',
          customer_name: 'Acme Traders',
          customer_gstin: '29AAEPM0111C1Z3',
          promotion_code: 'WELCOME20',
          customer_voucher_id: 'voucher-1',
          loyalty_points_to_redeem: 200,
          store_credit_amount: 10,
          gift_card_code: 'GIFT-1000',
          gift_card_amount: 1.41,
          lines: [{ product_id: 'product-1', quantity: 1 }],
        }),
      }),
    );
  });

  test('sends store_credit_amount and gift card posture in checkout payment session payloads', async () => {
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
      order_amount: 16.41,
      currency_code: 'INR',
      automatic_campaign_name: 'Tea Auto',
      automatic_discount_total: 9.25,
      promotion_code: 'WELCOME20',
      customer_voucher_id: 'voucher-1',
      customer_voucher_name: 'Welcome voucher',
      promotion_discount_amount: 20,
      promotion_code_discount_total: 20,
      customer_voucher_discount_total: 15,
      store_credit_amount: 10,
      gift_card_id: 'gift-card-1',
      gift_card_code: 'GIFT-1000',
      gift_card_amount: 1.41,
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
      cashier_session_id: 'cashier-session-1',
      handoff_surface: 'BRANDED_UPI_QR',
      provider_payment_mode: 'cashfree_upi',
      customer_profile_id: 'profile-1',
      customer_name: 'Acme Traders',
      customer_gstin: '29AAEPM0111C1Z3',
      promotion_code: 'WELCOME20',
      customer_voucher_id: 'voucher-1',
      loyalty_points_to_redeem: 200,
      store_credit_amount: 10,
      gift_card_code: 'GIFT-1000',
      gift_card_amount: 1.41,
      lines: [{ product_id: 'product-1', quantity: 1 }],
    });

    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/v1/tenants/tenant-1/branches/branch-1/checkout-payment-sessions'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          provider_name: 'cashfree',
          payment_method: 'CASHFREE_UPI_QR',
          cashier_session_id: 'cashier-session-1',
          handoff_surface: 'BRANDED_UPI_QR',
          provider_payment_mode: 'cashfree_upi',
          customer_profile_id: 'profile-1',
          customer_name: 'Acme Traders',
          customer_gstin: '29AAEPM0111C1Z3',
          promotion_code: 'WELCOME20',
          customer_voucher_id: 'voucher-1',
          loyalty_points_to_redeem: 200,
          store_credit_amount: 10,
          gift_card_code: 'GIFT-1000',
          gift_card_amount: 1.41,
          lines: [{ product_id: 'product-1', quantity: 1 }],
        }),
      }),
    );
  });
});
