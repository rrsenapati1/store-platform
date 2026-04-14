/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { OwnerCustomerInsightsSection } from './OwnerCustomerInsightsSection';

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

describe('owner customer insights section', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    const responses = [
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
      jsonResponse({
        customer: {
          customer_id: 'cust-1',
          name: 'Acme Traders',
          phone: null,
          email: null,
          gstin: '29AAEPM0111C1Z3',
          visit_count: 2,
          lifetime_value: 582.75,
          last_sale_id: 'sale-2',
        },
        sales_summary: {
          sales_count: 2,
          sales_total: 582.75,
          return_count: 1,
          credit_note_total: 97.12,
          exchange_count: 1,
        },
        sales: [
          {
            sale_id: 'sale-1',
            branch_id: 'branch-1',
            invoice_id: 'invoice-1',
            invoice_number: 'SINV-BLRFLAGSHIP-0001',
            grand_total: 291.38,
            payment_method: 'Cash',
          },
          {
            sale_id: 'sale-2',
            branch_id: 'branch-1',
            invoice_id: 'invoice-2',
            invoice_number: 'SINV-BLRFLAGSHIP-0002',
            grand_total: 291.37,
            payment_method: 'MIXED',
          },
        ],
        returns: [
          {
            sale_return_id: 'return-1',
            sale_id: 'sale-1',
            branch_id: 'branch-1',
            credit_note_id: 'credit-1',
            credit_note_number: 'SCN-BLRFLAGSHIP-0001',
            grand_total: 97.12,
            refund_amount: 97.12,
            status: 'REFUND_APPROVED',
          },
        ],
        exchanges: [
          {
            exchange_order_id: 'exchange-1',
            sale_id: 'sale-1',
            branch_id: 'branch-1',
            return_total: 97.12,
            replacement_total: 291.37,
            balance_direction: 'COLLECT_FROM_CUSTOMER',
            balance_amount: 97.12,
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

  test('loads customer directory, history, and branch report', async () => {
    render(
      <OwnerCustomerInsightsSection
        accessToken="session-owner"
        tenantId="tenant-acme"
        branchId="branch-1"
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Load customer insights' }));

    expect(await screen.findByText(/Acme Traders/)).toBeInTheDocument();
    expect(screen.getByText('Repeat customers')).toBeInTheDocument();
    expect(screen.getByText('Sales history')).toBeInTheDocument();
  });
});
