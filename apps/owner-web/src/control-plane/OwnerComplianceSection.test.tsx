/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { OwnerComplianceSection } from './OwnerComplianceSection';

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

describe('owner compliance section', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    const responses = [
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
        branch_id: 'branch-1',
        pending_count: 0,
        attached_count: 0,
        records: [],
      }),
      jsonResponse({
        id: 'gst-export-1',
        sale_id: 'sale-1',
        invoice_id: 'invoice-1',
        invoice_number: 'SINV-BLRFLAGSHIP-0001',
        customer_name: 'Acme Traders',
        seller_gstin: '29ABCDE1234F1Z5',
        buyer_gstin: '29AAEPM0111C1Z3',
        hsn_sac_summary: '0902',
        grand_total: 388.5,
        status: 'QUEUED',
        irn: null,
        ack_no: null,
        signed_qr_payload: null,
        created_at: '2026-04-14T08:00:00',
      }),
      jsonResponse({
        branch_id: 'branch-1',
        pending_count: 1,
        attached_count: 0,
        records: [
          {
            id: 'gst-export-1',
            sale_id: 'sale-1',
            invoice_id: 'invoice-1',
            invoice_number: 'SINV-BLRFLAGSHIP-0001',
            customer_name: 'Acme Traders',
            seller_gstin: '29ABCDE1234F1Z5',
            buyer_gstin: '29AAEPM0111C1Z3',
            hsn_sac_summary: '0902',
            grand_total: 388.5,
            status: 'QUEUED',
            irn: null,
            ack_no: null,
            signed_qr_payload: null,
            created_at: '2026-04-14T08:00:00',
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

  test('shows queued gst export posture and blocks irn attachment until preparation completes', async () => {
    render(
      <OwnerComplianceSection
        accessToken="session-owner"
        tenantId="tenant-acme"
        branchId="branch-1"
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Load compliance queue' }));

    expect(await screen.findByText(/SINV-BLRFLAGSHIP-0001/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Create export for first pending invoice' }));
    await screen.findByText('Latest GST export job');
    expect(screen.getByText('QUEUED')).toBeInTheDocument();
    expect(screen.getByText('Queued for worker preparation')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('IRN'), { target: { value: 'IRN-001' } });
    fireEvent.change(screen.getByLabelText('Ack number'), { target: { value: 'ACK-001' } });
    fireEvent.change(screen.getByLabelText('Signed QR payload'), { target: { value: 'signed-qr-001' } });
    expect(screen.getByRole('button', { name: 'Attach IRN to selected export' })).toBeDisabled();
  });
});
