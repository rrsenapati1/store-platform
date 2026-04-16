/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
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

describe('owner replenishment workflow', () => {
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
      jsonResponse({
        records: [
          {
            id: 'audit-1',
            action: 'branch.created',
            entity_type: 'branch',
            entity_id: 'branch-1',
            tenant_id: 'tenant-acme',
            branch_id: 'branch-1',
            created_at: '2026-04-13T08:00:00',
            payload: { name: 'Bengaluru Flagship' },
          },
        ],
      }),
      jsonResponse({ records: [] }),
      jsonResponse({ records: [] }),
      jsonResponse({ records: [] }),
      jsonResponse({ records: [] }),
      jsonResponse({ records: [] }),
      jsonResponse({
        id: 'product-1',
        tenant_id: 'tenant-acme',
        name: 'Classic Tea',
        sku_code: 'tea-classic-250g',
        barcode: '8901234567890',
        hsn_sac_code: '0902',
        gst_rate: 5,
        mrp: 120,
        category_code: 'TEA',
        selling_price: 92.5,
        status: 'ACTIVE',
      }),
      jsonResponse({
        records: [
          {
            product_id: 'product-1',
            tenant_id: 'tenant-acme',
            name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            barcode: '8901234567890',
            hsn_sac_code: '0902',
            gst_rate: 5,
            mrp: 120,
            category_code: 'TEA',
            selling_price: 92.5,
            status: 'ACTIVE',
          },
        ],
      }),
      jsonResponse({
        id: 'branch-catalog-1',
        tenant_id: 'tenant-acme',
        branch_id: 'branch-1',
        product_id: 'product-1',
        product_name: 'Classic Tea',
        sku_code: 'tea-classic-250g',
        barcode: '8901234567890',
        hsn_sac_code: '0902',
        gst_rate: 5,
        mrp: 120,
        category_code: 'TEA',
        base_selling_price: 92.5,
        selling_price_override: 89,
        effective_selling_price: 89,
        availability_status: 'ACTIVE',
        reorder_point: null,
        target_stock: null,
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
            barcode: '8901234567890',
            hsn_sac_code: '0902',
            gst_rate: 5,
            mrp: 120,
            category_code: 'TEA',
            base_selling_price: 92.5,
            selling_price_override: 89,
            effective_selling_price: 89,
            availability_status: 'ACTIVE',
            reorder_point: null,
            target_stock: null,
          },
        ],
      }),
      jsonResponse({
        id: 'branch-catalog-1',
        tenant_id: 'tenant-acme',
        branch_id: 'branch-1',
        product_id: 'product-1',
        product_name: 'Classic Tea',
        sku_code: 'tea-classic-250g',
        barcode: '8901234567890',
        hsn_sac_code: '0902',
        gst_rate: 5,
        mrp: 120,
        category_code: 'TEA',
        base_selling_price: 92.5,
        selling_price_override: 89,
        effective_selling_price: 89,
        availability_status: 'ACTIVE',
        reorder_point: 10,
        target_stock: 24,
      }),
      jsonResponse({
        branch_id: 'branch-1',
        low_stock_count: 1,
        adequate_count: 0,
        records: [
          {
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            availability_status: 'ACTIVE',
            stock_on_hand: 0,
            reorder_point: 10,
            target_stock: 24,
            suggested_reorder_quantity: 24,
            replenishment_status: 'LOW_STOCK',
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

  test('sets branch replenishment policy and renders the low-stock board', async () => {
    render(<App />);

    fireEvent.change(screen.getByLabelText('Korsenex token'), {
      target: { value: 'stub:sub=owner-1;email=owner@acme.local;name=Acme Owner' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Start owner session' }));

    expect(await screen.findByText('Acme Owner')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Product name'), { target: { value: 'Classic Tea' } });
    fireEvent.change(screen.getByLabelText('SKU code'), { target: { value: 'tea-classic-250g' } });
    fireEvent.change(screen.getByLabelText('Barcode'), { target: { value: '8901234567890' } });
    fireEvent.change(screen.getByLabelText('HSN or SAC code'), { target: { value: '0902' } });
    fireEvent.change(screen.getByLabelText('GST rate'), { target: { value: '5' } });
    fireEvent.change(screen.getByLabelText('MRP'), { target: { value: '120' } });
    fireEvent.change(screen.getByLabelText('Category code'), { target: { value: 'TEA' } });
    fireEvent.change(screen.getByLabelText('Selling price'), { target: { value: '92.5' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create catalog product' }));

    await waitFor(() => {
      expect(screen.getByText('Latest catalog product')).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText('Branch selling price override'), { target: { value: '89' } });
    fireEvent.click(screen.getByRole('button', { name: 'Assign first product to branch' }));

    await waitFor(() => {
      expect(screen.getByText('Latest branch catalog item')).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText('Reorder point'), { target: { value: '10' } });
    fireEvent.change(screen.getByLabelText('Target stock'), { target: { value: '24' } });
    fireEvent.click(screen.getByRole('button', { name: 'Set replenishment policy for first branch item' }));

    await waitFor(() => {
      expect(screen.getByText('Latest replenishment policy')).toBeInTheDocument();
    });

    const replenishmentSection = screen.getByRole('heading', { name: 'Replenishment board' }).closest('section');
    expect(replenishmentSection).not.toBeNull();
    expect(within(replenishmentSection as HTMLElement).getByRole('listitem')).toHaveTextContent(
      'Classic Tea :: LOW_STOCK :: suggest 24',
    );
  });
});
