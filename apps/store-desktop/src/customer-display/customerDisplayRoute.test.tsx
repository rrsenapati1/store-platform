/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, test } from 'vitest';
import { App } from '../App';
import {
  clearCustomerDisplayPayload,
  saveCustomerDisplayPayload,
  type CustomerDisplayPayload,
} from './customerDisplayModel';
import { CustomerDisplayRoute } from './customerDisplayRoute';

function createMemoryStorage(): Storage {
  const storage = new Map<string, string>();
  return {
    get length() {
      return storage.size;
    },
    clear() {
      storage.clear();
    },
    getItem(key: string) {
      return storage.has(key) ? storage.get(key)! : null;
    },
    key(index: number) {
      return Array.from(storage.keys())[index] ?? null;
    },
    removeItem(key: string) {
      storage.delete(key);
    },
    setItem(key: string, value: string) {
      storage.set(key, value);
    },
  };
}

function buildPayload(overrides: Partial<CustomerDisplayPayload> = {}): CustomerDisplayPayload {
  return {
    state: 'active_cart',
    title: 'Current order',
    message: 'Reviewing cart for UPI payment',
    currency_code: 'INR',
    line_items: [
      {
        label: 'Classic Tea',
        quantity: 2,
        amount: 194.25,
      },
    ],
    subtotal: 185,
    discount_total: 0,
    tax_total: 9.25,
    grand_total: 194.25,
    cash_received: null,
    change_due: null,
    payment_action: null,
    payment_qr: null,
    updated_at: '2026-04-15T12:00:00.000Z',
    ...overrides,
  };
}

describe('customer display route', () => {
  const originalWindowStorage = Object.getOwnPropertyDescriptor(window, 'localStorage');
  const originalGlobalStorage = Object.getOwnPropertyDescriptor(globalThis, 'localStorage');

  beforeEach(() => {
    const storage = createMemoryStorage();
    Object.defineProperty(window, 'localStorage', { configurable: true, value: storage });
    Object.defineProperty(globalThis, 'localStorage', { configurable: true, value: storage });
    clearCustomerDisplayPayload();
    window.history.pushState({}, '', '/');
  });

  afterEach(() => {
    clearCustomerDisplayPayload();
    window.history.pushState({}, '', '/');
    if (originalWindowStorage) {
      Object.defineProperty(window, 'localStorage', originalWindowStorage);
    }
    if (originalGlobalStorage) {
      Object.defineProperty(globalThis, 'localStorage', originalGlobalStorage);
    }
  });

  test('renders idle posture when no display payload is available', () => {
    render(<CustomerDisplayRoute />);

    expect(screen.getByText('Ready for next customer')).toBeInTheDocument();
    expect(screen.getAllByText('Waiting for the cashier terminal to start the next checkout.').length).toBeGreaterThan(0);
  });

  test('updates when the display payload changes in the same window', async () => {
    render(<CustomerDisplayRoute />);

    saveCustomerDisplayPayload(buildPayload());

    await waitFor(() => {
      expect(screen.getByText('Current order')).toBeInTheDocument();
      expect(screen.getByText('Classic Tea')).toBeInTheDocument();
      expect(screen.getAllByText('194.25').length).toBeGreaterThan(0);
    });
  });

  test('routes the app into customer-display mode from the query marker', async () => {
    saveCustomerDisplayPayload(buildPayload({
      state: 'sale_complete',
      title: 'Payment complete',
      message: 'Invoice SINV-BLRFLAGSHIP-0001',
      cash_received: 500,
      change_due: 111.5,
    }));
    window.history.pushState({}, '', '/?customer-display=1');

    render(<App />);

    expect(await screen.findByText('Payment complete')).toBeInTheDocument();
    expect(screen.queryByText('Store Runtime')).not.toBeInTheDocument();
  });

  test('renders a customer-facing QR graphic when a payment QR payload is active', async () => {
    saveCustomerDisplayPayload(buildPayload({
      state: 'payment_in_progress',
      title: 'Scan to pay',
      message: 'Scan to pay with any UPI app.',
      payment_qr: {
        format: 'upi_qr',
        value: 'upi://pay?tr=cf_order_checkout-1',
        expires_at: '2099-01-01T00:10:00.000Z',
      },
    }));

    render(<CustomerDisplayRoute />);

    expect(await screen.findByRole('img', { name: 'Customer payment QR code' })).toBeInTheDocument();
    expect(screen.getByText(/Expires in/i)).toBeInTheDocument();
  });

  test('renders hosted phone handoff posture with a scannable checkout link', async () => {
    saveCustomerDisplayPayload(buildPayload({
      state: 'payment_in_progress',
      title: 'Continue on phone',
      message: 'Scan this QR on the customer phone to open hosted checkout.',
      payment_action: {
        kind: 'hosted_url',
        value: 'https://payments.store.local/checkout/cf_order_checkout-1?surface=hosted_phone',
        label: 'Customer phone checkout',
        description: 'Scan this QR on the customer phone to open hosted checkout.',
        handoff_surface: 'HOSTED_PHONE',
      },
      payment_qr: {
        format: 'hosted_url',
        value: 'https://payments.store.local/checkout/cf_order_checkout-1?surface=hosted_phone',
        expires_at: '2099-01-01T00:10:00.000Z',
      },
    }));

    render(<CustomerDisplayRoute />);

    expect(await screen.findByRole('img', { name: 'Customer payment QR code' })).toBeInTheDocument();
    expect(screen.getByText('Continue on phone')).toBeInTheDocument();
    expect(screen.getAllByText(/hosted checkout/i).length).toBeGreaterThan(0);
  });

  test('renders hosted terminal instructions without a payment QR graphic', async () => {
    saveCustomerDisplayPayload(buildPayload({
      state: 'payment_in_progress',
      title: 'Complete payment on terminal',
      message: 'The cashier is continuing the hosted checkout on this terminal.',
      payment_action: {
        kind: 'hosted_url',
        value: 'https://payments.store.local/checkout/cf_order_checkout-1?surface=hosted_terminal',
        label: 'Terminal hosted checkout',
        description: 'The cashier is continuing the hosted checkout on this terminal.',
        handoff_surface: 'HOSTED_TERMINAL',
      },
      payment_qr: null,
    }));

    render(<CustomerDisplayRoute />);

    expect(await screen.findByText('Complete payment on terminal')).toBeInTheDocument();
    expect(screen.queryByRole('img', { name: 'Customer payment QR code' })).not.toBeInTheDocument();
  });
});
