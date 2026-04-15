import { describe, expect, test } from 'vitest';
import { buildCustomerDisplayPayload } from './customerDisplayModel';

describe('customer display payload model', () => {
  test('returns idle posture when no checkout preview exists', () => {
    const payload = buildCustomerDisplayPayload({
      branchName: 'Bengaluru Flagship',
      selectedItem: null,
      saleQuantity: '1',
      paymentMethod: 'Cash',
      latestSale: null,
      checkoutPaymentSession: null,
      isBusy: false,
    });

    expect(payload.state).toBe('idle');
    expect(payload.title).toBe('Ready for next customer');
    expect(payload.line_items).toEqual([]);
    expect(payload.grand_total).toBeNull();
  });

  test('returns active cart posture from the cashier preview state', () => {
    const payload = buildCustomerDisplayPayload({
      branchName: 'Bengaluru Flagship',
      selectedItem: {
        product_name: 'Classic Tea',
        effective_selling_price: 92.5,
        gst_rate: 5,
      },
      saleQuantity: '2',
      paymentMethod: 'UPI',
      latestSale: null,
      checkoutPaymentSession: null,
      isBusy: false,
    });

    expect(payload.state).toBe('active_cart');
    expect(payload.line_items).toEqual([
      {
        label: 'Classic Tea',
        quantity: 2,
        amount: 194.25,
      },
    ]);
    expect(payload.subtotal).toBe(185);
    expect(payload.tax_total).toBe(9.25);
    expect(payload.grand_total).toBe(194.25);
    expect(payload.message).toBe('Reviewing cart for UPI payment');
  });

  test('returns sale complete posture from the latest completed sale', () => {
    const payload = buildCustomerDisplayPayload({
      branchName: 'Bengaluru Flagship',
      selectedItem: {
        product_name: 'Classic Tea',
        effective_selling_price: 92.5,
        gst_rate: 5,
      },
      saleQuantity: '2',
      paymentMethod: 'Cash',
      latestSale: {
        customer_name: 'Acme Traders',
        payment: {
          payment_method: 'Cash',
          amount: 500,
        },
        lines: [
          {
            product_name: 'Classic Tea',
            quantity: 4,
            line_total: 388.5,
          },
        ],
        subtotal: 370,
        cgst_total: 9.25,
        sgst_total: 9.25,
        igst_total: 0,
        grand_total: 388.5,
        invoice_number: 'SINV-BLRFLAGSHIP-0001',
      },
      checkoutPaymentSession: null,
      isBusy: false,
    });

    expect(payload.state).toBe('sale_complete');
    expect(payload.title).toBe('Payment complete');
    expect(payload.grand_total).toBe(388.5);
    expect(payload.cash_received).toBe(500);
    expect(payload.change_due).toBe(111.5);
    expect(payload.message).toContain('SINV-BLRFLAGSHIP-0001');
  });
});
