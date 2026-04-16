/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { App } from '../App';

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

describe('store runtime customer insights', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
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
      jsonResponse({ records: [] }),
      jsonResponse({ records: [] }),
      jsonResponse({ records: [] }),
      jsonResponse({ records: [] }),
      jsonResponse({ records: [] }),
      jsonResponse({
        records: [
          {
            customer_id: 'cust-1',
            name: 'Acme Traders',
            phone: null,
            email: null,
            gstin: '29AAEPM0111C1Z3',
            visit_count: 2,
            lifetime_value: 582.75,
            last_sale_id: 'sale-2',
            last_invoice_number: 'SINV-BLRFLAGSHIP-0002',
            last_branch_id: 'branch-1',
          },
        ],
      }),
      jsonResponse({
        branch_id: 'branch-1',
        customer_count: 1,
        repeat_customer_count: 1,
        anonymous_sales_count: 1,
        anonymous_sales_total: 97.12,
        top_customers: [
          {
            customer_id: 'cust-1',
            customer_name: 'Acme Traders',
            sales_count: 2,
            sales_total: 582.75,
            last_invoice_number: 'SINV-BLRFLAGSHIP-0002',
          },
        ],
        return_activity: [
          {
            customer_id: 'cust-1',
            customer_name: 'Acme Traders',
            return_count: 1,
            credit_note_total: 97.12,
            exchange_count: 1,
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
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  test('loads customer directory and branch summary', async () => {
    render(<App />);

    fireEvent.change(screen.getByLabelText('Korsenex token'), {
      target: { value: 'stub:sub=cashier-1;email=cashier@acme.local;name=Counter Cashier' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Start runtime session' }));

    expect(await screen.findByText('Counter Cashier')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Load customer insights' }));

    expect(await screen.findByText(/Acme Traders/)).toBeInTheDocument();
    expect(screen.getByText('Repeat customers')).toBeInTheDocument();
  });
});
