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
            status: 'ACTION_REQUIRED',
            provider_name: 'iris_direct',
            provider_status: 'MISSING_PROFILE',
            last_error_code: 'MISSING_PROFILE',
            last_error_message: 'Branch IRP provider profile is not configured',
            irn: null,
            ack_no: null,
            signed_qr_payload: null,
            created_at: '2026-04-14T08:00:00',
          },
        ],
      }),
      jsonResponse({
        provider_name: null,
        api_username: null,
        has_password: false,
        status: 'NOT_CONFIGURED',
        last_error_message: null,
      }),
      jsonResponse({
        provider_name: 'iris_direct',
        api_username: 'acme-irp-user',
        has_password: true,
        status: 'CONFIGURED',
        last_error_message: null,
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
        status: 'RETRY_QUEUED',
        provider_name: 'iris_direct',
        provider_status: 'RETRY_QUEUED',
        last_error_code: null,
        last_error_message: null,
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
            status: 'RETRY_QUEUED',
            provider_name: 'iris_direct',
            provider_status: 'RETRY_QUEUED',
            last_error_code: null,
            last_error_message: null,
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

  test('loads provider posture and retries action-required exports without manual IRN entry', async () => {
    render(
      <OwnerComplianceSection
        accessToken="session-owner"
        tenantId="tenant-acme"
        branchId="branch-1"
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Load compliance queue' }));

    expect(await screen.findByText('Provider profile')).toBeInTheDocument();
    expect(screen.getByText('NOT_CONFIGURED')).toBeInTheDocument();
    expect(screen.getByText(/Branch IRP provider profile is not configured/)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Attach IRN to selected export' })).not.toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Provider'), { target: { value: 'iris_direct' } });
    fireEvent.change(screen.getByLabelText('API username'), { target: { value: 'acme-irp-user' } });
    fireEvent.change(screen.getByLabelText('API password'), { target: { value: 'super-secret' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save provider profile' }));

    expect(await screen.findByText('CONFIGURED')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Retry selected export' }));

    expect(await screen.findByText('Latest GST export job')).toBeInTheDocument();
    expect(screen.getAllByText('RETRY_QUEUED').length).toBeGreaterThan(0);
  });
});
