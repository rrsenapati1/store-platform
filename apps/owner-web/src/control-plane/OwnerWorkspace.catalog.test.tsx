/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
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

describe('owner catalog foundation flow', () => {
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
        tracking_mode: 'SERIALIZED',
        compliance_profile: 'NONE',
        compliance_config: {},
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
            tracking_mode: 'SERIALIZED',
            compliance_profile: 'NONE',
            compliance_config: {},
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
        tracking_mode: 'SERIALIZED',
        compliance_profile: 'NONE',
        compliance_config: {},
        base_selling_price: 92.5,
        selling_price_override: 89,
        effective_selling_price: 89,
        availability_status: 'ACTIVE',
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
            tracking_mode: 'SERIALIZED',
            compliance_profile: 'NONE',
            compliance_config: {},
            base_selling_price: 92.5,
            selling_price_override: 89,
            effective_selling_price: 89,
            availability_status: 'ACTIVE',
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
    cleanup();
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  test('creates a central catalog product and assigns it to the first branch', async () => {
    render(<App />);

    fireEvent.change(screen.getByLabelText('Korsenex token'), {
      target: { value: 'stub:sub=owner-1;email=owner@acme.local;name=Acme Owner' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Start owner session' }));

    expect(await screen.findByText('Acme Owner', {}, { timeout: 10_000 })).toBeInTheDocument();
    expect(await screen.findByText('Bengaluru Flagship')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Product name'), { target: { value: 'Classic Tea' } });
    fireEvent.change(screen.getByLabelText('SKU code'), { target: { value: 'tea-classic-250g' } });
    fireEvent.change(screen.getByLabelText('Barcode'), { target: { value: '8901234567890' } });
    fireEvent.change(screen.getByLabelText('HSN or SAC code'), { target: { value: '0902' } });
    fireEvent.change(screen.getByLabelText('GST rate'), { target: { value: '5' } });
    fireEvent.change(screen.getByLabelText('MRP'), { target: { value: '120' } });
    fireEvent.change(screen.getByLabelText('Category code'), { target: { value: 'TEA' } });
    fireEvent.change(screen.getByLabelText('Tracking mode'), { target: { value: 'SERIALIZED' } });
    fireEvent.change(screen.getByLabelText('Selling price'), { target: { value: '92.5' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create catalog product' }));

    const createProductCall = vi.mocked(globalThis.fetch).mock.calls.find(
      ([input, init]) => String(input).endsWith('/v1/tenants/tenant-acme/catalog/products') && (init?.method ?? 'GET') === 'POST',
    );
    expect(createProductCall).toBeDefined();
    expect(JSON.parse(String(createProductCall?.[1]?.body))).toMatchObject({
      tracking_mode: 'SERIALIZED',
    });

    await waitFor(() => {
      expect(screen.getByText('Latest catalog product')).toBeInTheDocument();
      expect(screen.getAllByText('Classic Tea').length).toBeGreaterThan(0);
      expect(screen.getByText('120')).toBeInTheDocument();
      expect(screen.getAllByText('SERIALIZED').length).toBeGreaterThan(0);
    });

    fireEvent.change(screen.getByLabelText('Branch selling price override'), { target: { value: '89' } });
    fireEvent.click(screen.getByRole('button', { name: 'Assign first product to branch' }));

    await waitFor(() => {
      expect(screen.getByText('Latest branch catalog item')).toBeInTheDocument();
      expect(screen.getByText('Classic Tea -> 89 :: MRP 120')).toBeInTheDocument();
    });
  });

  test('sends compliance profile configuration when creating a regulated catalog product', async () => {
    render(<App />);

    fireEvent.change(screen.getByLabelText('Korsenex token'), {
      target: { value: 'stub:sub=owner-1;email=owner@acme.local;name=Acme Owner' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Start owner session' }));

    expect(await screen.findByText('Acme Owner', {}, { timeout: 10_000 })).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Product name'), { target: { value: 'Reserve Beverage' } });
    fireEvent.change(screen.getByLabelText('SKU code'), { target: { value: 'bev-reserve-750' } });
    fireEvent.change(screen.getByLabelText('Barcode'), { target: { value: '8901234567005' } });
    fireEvent.change(screen.getByLabelText('HSN or SAC code'), { target: { value: '2203' } });
    fireEvent.change(screen.getByLabelText('GST rate'), { target: { value: '28' } });
    fireEvent.change(screen.getByLabelText('MRP'), { target: { value: '900' } });
    fireEvent.change(screen.getByLabelText('Category code'), { target: { value: 'ALCOHOL' } });
    fireEvent.change(screen.getByLabelText('Tracking mode'), { target: { value: 'STANDARD' } });
    fireEvent.change(screen.getByLabelText('Compliance profile'), { target: { value: 'AGE_RESTRICTED' } });
    fireEvent.change(screen.getByLabelText('Minimum age'), { target: { value: '21' } });
    fireEvent.change(screen.getByLabelText('Selling price'), { target: { value: '850' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create catalog product' }));

    const createProductCall = vi.mocked(globalThis.fetch).mock.calls.find(
      ([input, init]) => String(input).endsWith('/v1/tenants/tenant-acme/catalog/products') && (init?.method ?? 'GET') === 'POST',
    );
    expect(createProductCall).toBeDefined();
    expect(JSON.parse(String(createProductCall?.[1]?.body))).toMatchObject({
      compliance_profile: 'AGE_RESTRICTED',
      compliance_config: {
        minimum_age: 21,
      },
    });
  });
});
