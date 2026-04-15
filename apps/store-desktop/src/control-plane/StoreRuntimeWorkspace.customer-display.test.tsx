/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { App } from '../App';
import { clearCustomerDisplayPayload, loadCustomerDisplayPayload } from '../customer-display/customerDisplayModel';

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

describe('store runtime customer display flow', () => {
  const originalFetch = globalThis.fetch;
  const originalOpen = window.open;
  const originalWindowStorage = Object.getOwnPropertyDescriptor(window, 'localStorage');
  const originalGlobalStorage = Object.getOwnPropertyDescriptor(globalThis, 'localStorage');

  beforeEach(() => {
    const storage = createMemoryStorage();
    Object.defineProperty(window, 'localStorage', { configurable: true, value: storage });
    Object.defineProperty(globalThis, 'localStorage', { configurable: true, value: storage });
    clearCustomerDisplayPayload();
    window.open = vi.fn(() => ({ focus: vi.fn(), close: vi.fn(), closed: false } as unknown as WindowProxy));
    const responses = [
      jsonResponse({ access_token: 'session-cashier', token_type: 'Bearer' }),
      jsonResponse({
        user_id: 'user-cashier',
        email: 'cashier@acme.local',
        full_name: 'Counter Cashier',
        is_platform_admin: false,
        tenant_memberships: [],
        branch_memberships: [{ tenant_id: 'tenant-acme', branch_id: 'branch-1', role_name: 'cashier', status: 'ACTIVE' }],
      }),
      jsonResponse({
        id: 'tenant-acme',
        name: 'Acme Retail',
        slug: 'acme-retail',
        status: 'ACTIVE',
        onboarding_status: 'BRANCH_READY',
      }),
      jsonResponse({
        records: [{ branch_id: 'branch-1', tenant_id: 'tenant-acme', name: 'Bengaluru Flagship', code: 'blr-flagship', status: 'ACTIVE' }],
      }),
      jsonResponse({
        records: [
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
      }),
      jsonResponse({
        records: [
          {
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            stock_on_hand: 24,
            last_entry_type: 'PURCHASE_RECEIPT',
          },
        ],
      }),
      jsonResponse({ records: [] }),
      jsonResponse({
        records: [
          {
            id: 'device-1',
            tenant_id: 'tenant-acme',
            branch_id: 'branch-1',
            device_name: 'Counter Desktop 1',
            device_code: 'counter-1',
            session_surface: 'store_desktop',
            status: 'ACTIVE',
            assigned_staff_profile_id: null,
            assigned_staff_full_name: null,
          },
        ],
      }),
      jsonResponse({
        id: 'sale-1',
        tenant_id: 'tenant-acme',
        branch_id: 'branch-1',
        customer_name: 'Acme Traders',
        customer_gstin: '29AAEPM0111C1Z3',
        invoice_kind: 'B2B',
        irn_status: 'IRN_PENDING',
        invoice_number: 'SINV-BLRFLAGSHIP-0001',
        issued_on: '2026-04-15T12:04:00.000Z',
        subtotal: 185,
        cgst_total: 4.63,
        sgst_total: 4.62,
        igst_total: 0,
        grand_total: 194.25,
        payment: { payment_method: 'UPI', amount: 194.25 },
        lines: [
          {
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            hsn_sac_code: '0902',
            quantity: 2,
            unit_price: 92.5,
            gst_rate: 5,
            line_subtotal: 185,
            tax_total: 9.25,
            line_total: 194.25,
          },
        ],
        tax_lines: [
          { tax_type: 'CGST', tax_rate: 2.5, taxable_amount: 185, tax_amount: 4.63 },
          { tax_type: 'SGST', tax_rate: 2.5, taxable_amount: 185, tax_amount: 4.62 },
        ],
      }),
      jsonResponse({
        records: [
          {
            sale_id: 'sale-1',
            invoice_number: 'SINV-BLRFLAGSHIP-0001',
            customer_name: 'Acme Traders',
            invoice_kind: 'B2B',
            irn_status: 'IRN_PENDING',
            payment_method: 'UPI',
            grand_total: 194.25,
            issued_on: '2026-04-15',
          },
        ],
      }),
      jsonResponse({
        records: [
          {
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            stock_on_hand: 22,
            last_entry_type: 'SALE',
          },
        ],
      }),
    ];

    globalThis.fetch = vi.fn(async () => {
      const next = responses.shift();
      if (!next) {
        throw new Error('Unexpected fetch call');
      }
      return next as never;
    }) as typeof fetch;
  });

  afterEach(() => {
    clearCustomerDisplayPayload();
    window.open = originalOpen;
    globalThis.fetch = originalFetch;
    if (originalWindowStorage) {
      Object.defineProperty(window, 'localStorage', originalWindowStorage);
    }
    if (originalGlobalStorage) {
      Object.defineProperty(globalThis, 'localStorage', originalGlobalStorage);
    }
    vi.restoreAllMocks();
  });

  test('publishes cart preview and completed sale posture to the customer display', async () => {
    render(<App />);

    fireEvent.change(screen.getByLabelText('Korsenex token'), {
      target: { value: 'stub:sub=cashier-1;email=cashier@acme.local;name=Counter Cashier' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Start runtime session' }));

    expect(await screen.findByText('Counter Cashier')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Customer name'), { target: { value: 'Acme Traders' } });
    fireEvent.change(screen.getByLabelText('Sale quantity'), { target: { value: '2' } });
    fireEvent.change(screen.getByLabelText('Payment method'), { target: { value: 'UPI' } });
    fireEvent.click(screen.getByRole('button', { name: 'Open customer display' }));

    await waitFor(() => {
      const payload = loadCustomerDisplayPayload();
      expect(payload?.state).toBe('active_cart');
      expect(payload?.grand_total).toBe(194.25);
    });

    fireEvent.change(screen.getByLabelText('Customer GSTIN'), { target: { value: '29AAEPM0111C1Z3' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create sales invoice' }));

    await waitFor(() => {
      const payload = loadCustomerDisplayPayload();
      expect(payload?.state).toBe('sale_complete');
      expect(payload?.message).toContain('SINV-BLRFLAGSHIP-0001');
    });
  });
});
