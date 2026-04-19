/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
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

describe('owner barcode foundation flow', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    const responses = [
      jsonResponse({ access_token: 'session-owner', token_type: 'Bearer' }),
      jsonResponse({
        user_id: 'user-owner',
        email: 'owner@acme.local',
        full_name: 'Acme Owner',
        is_platform_admin: false,
        tenant_memberships: [{ tenant_id: 'tenant-acme', role_name: 'tenant_owner', status: 'ACTIVE' }],
        branch_memberships: [],
      }),
      jsonResponse({
        id: 'tenant-acme',
        name: 'Acme Retail',
        slug: 'acme-retail',
        status: 'ACTIVE',
        onboarding_status: 'BRANCH_READY',
      }),
      jsonResponse({
        records: [
          {
            branch_id: 'branch-1',
            tenant_id: 'tenant-acme',
            name: 'Bengaluru Flagship',
            code: 'blr-flagship',
            status: 'ACTIVE',
          },
        ],
      }),
      jsonResponse({ records: [] }),
      jsonResponse({ records: [] }),
      jsonResponse({
        records: [
          {
            product_id: 'product-1',
            tenant_id: 'tenant-acme',
            name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            barcode: '',
            hsn_sac_code: '0902',
            gst_rate: 5,
            selling_price: 92.5,
            status: 'ACTIVE',
          },
        ],
      }),
      jsonResponse({
        records: [
          {
            id: 'branch-catalog-1',
            tenant_id: 'tenant-acme',
            branch_id: 'branch-1',
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            barcode: '',
            hsn_sac_code: '0902',
            gst_rate: 5,
            base_selling_price: 92.5,
            selling_price_override: 89,
            effective_selling_price: 89,
            availability_status: 'ACTIVE',
          },
        ],
      }),
      jsonResponse({ records: [] }),
      jsonResponse({ records: [] }),
      jsonResponse({
        product_id: 'product-1',
        barcode: 'ACMETEACLASSIC',
        source: 'ALLOCATED',
      }),
      jsonResponse({
        records: [
          {
            product_id: 'product-1',
            tenant_id: 'tenant-acme',
            name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            barcode: 'ACMETEACLASSIC',
            hsn_sac_code: '0902',
            gst_rate: 5,
            selling_price: 92.5,
            status: 'ACTIVE',
          },
        ],
      }),
      jsonResponse({
        records: [
          {
            id: 'branch-catalog-1',
            tenant_id: 'tenant-acme',
            branch_id: 'branch-1',
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            barcode: 'ACMETEACLASSIC',
            hsn_sac_code: '0902',
            gst_rate: 5,
            base_selling_price: 92.5,
            selling_price_override: 89,
            effective_selling_price: 89,
            availability_status: 'ACTIVE',
          },
        ],
      }),
      jsonResponse({
        product_id: 'product-1',
        sku_code: 'tea-classic-250g',
        product_name: 'Classic Tea',
        barcode: 'ACMETEACLASSIC',
        price_label: 'Rs. 89.00',
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

  test('allocates a barcode for the first catalog product and previews the branch label', async () => {
    render(<App />);

    fireEvent.change(screen.getByLabelText('Korsenex token'), {
      target: { value: 'stub:sub=owner-1;email=owner@acme.local;name=Acme Owner' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Start owner session' }));

    expect(await screen.findByText('Acme Owner', {}, { timeout: 10_000 })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Catalog' }));

    fireEvent.click(screen.getByRole('button', { name: 'Allocate first product barcode' }));

    await waitFor(() => {
      expect(screen.getByText('Latest barcode allocation')).toBeInTheDocument();
      expect(screen.getByText('ACMETEACLASSIC')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: 'Preview first product label' }));

    await waitFor(() => {
      expect(screen.getByText('Latest barcode label preview')).toBeInTheDocument();
      expect(screen.getByText('Rs. 89.00')).toBeInTheDocument();
    });
  });
});
