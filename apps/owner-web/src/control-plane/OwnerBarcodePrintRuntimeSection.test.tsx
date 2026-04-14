/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { OwnerBarcodePrintRuntimeSection } from './OwnerBarcodePrintRuntimeSection';

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

describe('owner barcode print runtime section', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    globalThis.fetch = vi.fn(async () =>
      jsonResponse({
        id: 'print-job-1',
        tenant_id: 'tenant-acme',
        branch_id: 'branch-1',
        device_id: 'device-1',
        reference_type: 'catalog_product',
        reference_id: 'product-1',
        job_type: 'BARCODE_LABEL',
        copies: 2,
        status: 'QUEUED',
        failure_reason: null,
        payload: {
          labels: [
            {
              sku_code: 'tea-classic-250g',
              product_name: 'Classic Tea',
              barcode: 'ACMETEACLASSIC',
              price_label: 'Rs. 89.00',
            },
          ],
        },
      }) as never,
    ) as unknown as typeof fetch;
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  test('queues barcode labels onto the selected runtime device', async () => {
    render(
      <OwnerBarcodePrintRuntimeSection
        accessToken="session-owner"
        tenantId="tenant-acme"
        branchId="branch-1"
        productId="product-1"
        devices={[
          {
            id: 'device-1',
            tenant_id: 'tenant-acme',
            branch_id: 'branch-1',
            device_name: 'Counter Desktop 1',
            device_code: 'counter-1',
            session_surface: 'store_desktop',
            runtime_profile: 'desktop_spoke',
            status: 'ACTIVE',
            assigned_staff_profile_id: null,
            assigned_staff_full_name: null,
          },
        ]}
      />,
    );

    fireEvent.change(screen.getByLabelText('Label copies'), { target: { value: '2' } });
    fireEvent.click(screen.getByRole('button', { name: 'Queue barcode labels' }));

    expect(await screen.findByText('Queued barcode label job')).toBeInTheDocument();
    expect(screen.getByText('BARCODE_LABEL')).toBeInTheDocument();
    expect(screen.getByText(/Classic Tea :: ACMETEACLASSIC :: Rs. 89.00/)).toBeInTheDocument();
  });
});
