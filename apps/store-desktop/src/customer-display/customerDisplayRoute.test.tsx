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
});
