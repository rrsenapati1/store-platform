/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { OwnerReturnApprovalsSection } from './OwnerReturnApprovalsSection';

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

describe('owner return approvals section', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    const responses = [
      jsonResponse({
        records: [
          {
            sale_return_id: 'sale-return-1',
            sale_id: 'sale-1',
            invoice_number: 'SINV-BLRFLAGSHIP-0001',
            customer_name: 'Acme Traders',
            status: 'REFUND_PENDING_APPROVAL',
            refund_amount: 97.12,
            refund_method: 'UPI',
            credit_note_number: 'SCN-BLRFLAGSHIP-0001',
            credit_note_total: 97.12,
            issued_on: '2026-04-13',
          },
        ],
      }),
      jsonResponse({
        id: 'sale-return-1',
        tenant_id: 'tenant-acme',
        branch_id: 'branch-1',
        sale_id: 'sale-1',
        status: 'REFUND_APPROVED',
        refund_amount: 97.12,
        refund_method: 'UPI',
        lines: [],
        credit_note: {
          id: 'credit-note-1',
          credit_note_number: 'SCN-BLRFLAGSHIP-0001',
          issued_on: '2026-04-13',
          subtotal: 92.5,
          cgst_total: 2.31,
          sgst_total: 2.31,
          igst_total: 0,
          grand_total: 97.12,
          tax_lines: [],
        },
      }),
      jsonResponse({
        records: [
          {
            sale_return_id: 'sale-return-1',
            sale_id: 'sale-1',
            invoice_number: 'SINV-BLRFLAGSHIP-0001',
            customer_name: 'Acme Traders',
            status: 'REFUND_APPROVED',
            refund_amount: 97.12,
            refund_method: 'UPI',
            credit_note_number: 'SCN-BLRFLAGSHIP-0001',
            credit_note_total: 97.12,
            issued_on: '2026-04-13',
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

  test('loads pending returns and approves a refund', async () => {
    render(
      <OwnerReturnApprovalsSection
        accessToken="session-owner"
        tenantId="tenant-acme"
        branchId="branch-1"
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Load refund approvals' }));

    expect(await screen.findByText(/SCN-BLRFLAGSHIP-0001/)).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Approval note'), { target: { value: 'Approved by owner' } });
    fireEvent.click(screen.getByRole('button', { name: 'Approve selected refund' }));

    await waitFor(() => {
      expect(screen.getByText('Latest approved refund')).toBeInTheDocument();
      expect(screen.getByText('REFUND_APPROVED')).toBeInTheDocument();
    });
  });
});
