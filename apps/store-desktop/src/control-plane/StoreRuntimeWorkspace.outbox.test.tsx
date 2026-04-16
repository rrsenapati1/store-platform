/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { App } from '../App';
import { STORE_RUNTIME_CACHE_KEY } from '../runtime-cache/storeRuntimeCache';

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

class MemoryStorage implements Storage {
  private readonly data = new Map<string, string>();

  get length() {
    return this.data.size;
  }

  clear(): void {
    this.data.clear();
  }

  getItem(key: string): string | null {
    return this.data.get(key) ?? null;
  }

  key(index: number): string | null {
    return Array.from(this.data.keys())[index] ?? null;
  }

  removeItem(key: string): void {
    this.data.delete(key);
  }

  setItem(key: string, value: string): void {
    this.data.set(key, value);
  }
}

function queueBootstrapResponses(fetchMock: ReturnType<typeof vi.fn>) {
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
    jsonResponse({ records: [] }),
  ];

  for (const response of responses) {
    fetchMock.mockResolvedValueOnce(response as never);
  }
}

function queueSaleCreationResponses(fetchMock: ReturnType<typeof vi.fn>) {
  const responses = [
    jsonResponse({
      id: 'sale-1',
      tenant_id: 'tenant-acme',
      branch_id: 'branch-1',
      customer_name: 'Acme Traders',
      customer_gstin: '29AAEPM0111C1Z3',
      invoice_kind: 'B2B',
      irn_status: 'IRN_PENDING',
      invoice_number: 'SINV-BLRFLAGSHIP-0001',
      issued_on: '2026-04-14',
      subtotal: 370,
      cgst_total: 9.25,
      sgst_total: 9.25,
      igst_total: 0,
      grand_total: 388.5,
      payment: { payment_method: 'UPI', amount: 388.5 },
      lines: [
        {
          product_id: 'product-1',
          product_name: 'Classic Tea',
          sku_code: 'tea-classic-250g',
          hsn_sac_code: '0902',
          quantity: 4,
          unit_price: 92.5,
          gst_rate: 5,
          line_subtotal: 370,
          tax_total: 18.5,
          line_total: 388.5,
        },
      ],
      tax_lines: [
        { tax_type: 'CGST', tax_rate: 2.5, taxable_amount: 370, tax_amount: 9.25 },
        { tax_type: 'SGST', tax_rate: 2.5, taxable_amount: 370, tax_amount: 9.25 },
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
          grand_total: 388.5,
          issued_on: '2026-04-14',
        },
      ],
    }),
    jsonResponse({
      records: [
        {
          product_id: 'product-1',
          product_name: 'Classic Tea',
          sku_code: 'tea-classic-250g',
          stock_on_hand: 20,
          last_entry_type: 'SALE',
        },
      ],
    }),
  ];

  for (const response of responses) {
    fetchMock.mockResolvedValueOnce(response as never);
  }
}

describe('store runtime outbox continuity', () => {
  const originalFetch = globalThis.fetch;
  const originalLocalStorage = globalThis.localStorage;
  const originalTauriInternals = (window as Window & { __TAURI_INTERNALS__?: object }).__TAURI_INTERNALS__;

  beforeEach(() => {
    delete (window as Window & { __TAURI_INTERNALS__?: object }).__TAURI_INTERNALS__;
    Object.defineProperty(globalThis, 'localStorage', {
      configurable: true,
      value: new MemoryStorage(),
    });
  });

  afterEach(() => {
    cleanup();
    globalThis.fetch = originalFetch;
    Object.defineProperty(globalThis, 'localStorage', {
      configurable: true,
      value: originalLocalStorage,
    });
    (window as Window & { __TAURI_INTERNALS__?: object }).__TAURI_INTERNALS__ = originalTauriInternals;
    vi.restoreAllMocks();
  });

  test('queues a heartbeat locally and replays it when the control plane is reachable again', async () => {
    const fetchMock = vi.fn();
    queueBootstrapResponses(fetchMock);
    globalThis.fetch = fetchMock as typeof fetch;

    render(<App />);

    fireEvent.change(screen.getByLabelText('Korsenex token'), {
      target: { value: 'stub:sub=cashier-1;email=cashier@acme.local;name=Counter Cashier' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Start runtime session' }));

    expect(await screen.findByText('Counter Cashier')).toBeInTheDocument();
    expect(await screen.findByDisplayValue('device-1')).toBeInTheDocument();

    fetchMock.mockRejectedValueOnce(new TypeError('Failed to fetch'));
    fireEvent.click(screen.getByRole('button', { name: 'Send device heartbeat' }));

    await waitFor(() => {
      expect(screen.getByText('Queued runtime actions: 1')).toBeInTheDocument();
    });

    await waitFor(() => {
      const queuedSnapshot = JSON.parse(localStorage.getItem(STORE_RUNTIME_CACHE_KEY) ?? '{}') as {
        pending_mutations?: Array<Record<string, unknown>>;
      };
      expect(queuedSnapshot.pending_mutations).toHaveLength(1);
    });

    fetchMock.mockResolvedValueOnce(
      jsonResponse({
        device_id: 'device-1',
        status: 'ACTIVE',
        last_seen_at: '2026-04-14T11:02:00',
        queued_job_count: 0,
      }) as never,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Replay pending runtime actions' }));

    await waitFor(() => {
      expect(screen.getByText('Queued runtime actions: 0')).toBeInTheDocument();
      expect(screen.getByText('2026-04-14T11:02:00')).toBeInTheDocument();
    });
  });

  test('queues an invoice print request locally and replays it once the control plane recovers', async () => {
    const fetchMock = vi.fn();
    queueBootstrapResponses(fetchMock);
    queueSaleCreationResponses(fetchMock);
    globalThis.fetch = fetchMock as typeof fetch;

    render(<App />);

    fireEvent.change(screen.getByLabelText('Korsenex token'), {
      target: { value: 'stub:sub=cashier-1;email=cashier@acme.local;name=Counter Cashier' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Start runtime session' }));

    expect(await screen.findByText('Counter Cashier')).toBeInTheDocument();
    expect(await screen.findByDisplayValue('device-1')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Customer name'), { target: { value: 'Acme Traders' } });
    fireEvent.change(screen.getByLabelText('Customer GSTIN'), { target: { value: '29AAEPM0111C1Z3' } });
    fireEvent.change(screen.getByLabelText('Sale quantity'), { target: { value: '4' } });
    fireEvent.change(screen.getByLabelText('Payment method'), { target: { value: 'UPI' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create sales invoice' }));

    expect((await screen.findAllByText('SINV-BLRFLAGSHIP-0001')).length).toBeGreaterThan(0);

    fetchMock.mockRejectedValueOnce(new TypeError('Failed to fetch'));
    fireEvent.click(screen.getByRole('button', { name: 'Queue latest invoice print' }));

    await waitFor(() => {
      expect(screen.getByText('Queued runtime actions: 1')).toBeInTheDocument();
      expect(screen.getByText(/Invoice print :: SINV-BLRFLAGSHIP-0001/)).toBeInTheDocument();
    });

    await waitFor(() => {
      const queuedSnapshot = JSON.parse(localStorage.getItem(STORE_RUNTIME_CACHE_KEY) ?? '{}') as {
        pending_mutations?: Array<Record<string, unknown>>;
      };
      expect(queuedSnapshot.pending_mutations).toHaveLength(1);
    });

    fetchMock.mockResolvedValueOnce(
      jsonResponse({
        id: 'print-job-1',
        tenant_id: 'tenant-acme',
        branch_id: 'branch-1',
        device_id: 'device-1',
        reference_type: 'sale',
        reference_id: 'sale-1',
        job_type: 'SALES_INVOICE',
        copies: 1,
        status: 'QUEUED',
        failure_reason: null,
        payload: {
          document_number: 'SINV-BLRFLAGSHIP-0001',
          receipt_lines: ['STORE TAX INVOICE', 'Invoice: SINV-BLRFLAGSHIP-0001'],
        },
      }) as never,
    );
    fetchMock.mockResolvedValueOnce(
      jsonResponse({
        records: [
          {
            id: 'print-job-1',
            tenant_id: 'tenant-acme',
            branch_id: 'branch-1',
            device_id: 'device-1',
            reference_type: 'sale',
            reference_id: 'sale-1',
            job_type: 'SALES_INVOICE',
            copies: 1,
            status: 'QUEUED',
            failure_reason: null,
            payload: {
              document_number: 'SINV-BLRFLAGSHIP-0001',
              receipt_lines: ['STORE TAX INVOICE', 'Invoice: SINV-BLRFLAGSHIP-0001'],
            },
          },
        ],
      }) as never,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Replay pending runtime actions' }));

    await waitFor(() => {
      expect(screen.getByText('Queued runtime actions: 0')).toBeInTheDocument();
      expect(screen.getByText('print-job-1')).toBeInTheDocument();
    });
  });
});
