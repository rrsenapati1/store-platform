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

describe('owner price tier foundation flow', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    const priceTiers: Array<{
      id: string;
      tenant_id: string;
      code: string;
      display_name: string;
      status: string;
      created_at: string;
      updated_at: string;
    }> = [];

    const branchPriceTierPrices: Array<{
      id: string;
      tenant_id: string;
      branch_id: string;
      product_id: string;
      product_name: string;
      sku_code: string;
      price_tier_id: string;
      price_tier_code: string;
      price_tier_display_name: string;
      base_selling_price: number;
      effective_base_selling_price: number;
      selling_price: number;
      created_at: string;
      updated_at: string;
    }> = [];

    globalThis.fetch = vi.fn(async (input, init) => {
      const url = typeof input === 'string' ? input : input.toString();
      const method = init?.method ?? 'GET';

      if (url === '/v1/auth/oidc/exchange' && method === 'POST') {
        return jsonResponse({ access_token: 'session-owner', token_type: 'Bearer' }) as never;
      }
      if (url === '/v1/auth/me') {
        return jsonResponse({
          user_id: 'user-owner',
          email: 'owner@acme.local',
          full_name: 'Acme Owner',
          is_platform_admin: false,
          tenant_memberships: [{ tenant_id: 'tenant-acme', role_name: 'tenant_owner', status: 'ACTIVE' }],
          branch_memberships: [],
        }) as never;
      }
      if (url === '/v1/tenants/tenant-acme') {
        return jsonResponse({
          id: 'tenant-acme',
          name: 'Acme Retail',
          slug: 'acme-retail',
          status: 'ACTIVE',
          onboarding_status: 'BRANCH_READY',
        }) as never;
      }
      if (url === '/v1/tenants/tenant-acme/branches') {
        return jsonResponse({
          records: [
            {
              branch_id: 'branch-1',
              tenant_id: 'tenant-acme',
              name: 'Bengaluru Flagship',
              code: 'blr-flagship',
              status: 'ACTIVE',
            },
          ],
        }) as never;
      }
      if (url === '/v1/tenants/tenant-acme/audit-events') {
        return jsonResponse({ records: [] }) as never;
      }
      if (url === '/v1/tenants/tenant-acme/staff-profiles') {
        return jsonResponse({ records: [] }) as never;
      }
      if (url === '/v1/tenants/tenant-acme/catalog/products') {
        return jsonResponse({
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
        }) as never;
      }
      if (url === '/v1/tenants/tenant-acme/branches/branch-1/catalog-items') {
        return jsonResponse({
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
            },
          ],
        }) as never;
      }
      if (url === '/v1/tenants/tenant-acme/branches/branch-1/devices') {
        return jsonResponse({ records: [] }) as never;
      }
      if (url === '/v1/tenants/tenant-acme/suppliers') {
        return jsonResponse({ records: [] }) as never;
      }
      if (url === '/v1/tenants/tenant-acme/price-tiers' && method === 'POST') {
        const payload = JSON.parse(String(init?.body ?? '{}'));
        const record = {
          id: 'tier-1',
          tenant_id: 'tenant-acme',
          code: payload.code,
          display_name: payload.display_name,
          status: payload.status,
          created_at: '2026-04-17T12:00:00',
          updated_at: '2026-04-17T12:00:00',
        };
        priceTiers.splice(0, priceTiers.length, record);
        return jsonResponse(record) as never;
      }
      if (url === '/v1/tenants/tenant-acme/price-tiers' && method === 'GET') {
        return jsonResponse({ records: priceTiers }) as never;
      }
      if (url === '/v1/tenants/tenant-acme/branches/branch-1/price-tier-prices' && method === 'POST') {
        const payload = JSON.parse(String(init?.body ?? '{}'));
        const tier = priceTiers.find((record) => record.id === payload.price_tier_id);
        const record = {
          id: 'branch-tier-1',
          tenant_id: 'tenant-acme',
          branch_id: 'branch-1',
          product_id: 'product-1',
          product_name: 'Classic Tea',
          sku_code: 'tea-classic-250g',
          price_tier_id: payload.price_tier_id,
          price_tier_code: tier?.code ?? 'VIP',
          price_tier_display_name: tier?.display_name ?? 'VIP Price',
          base_selling_price: 92.5,
          effective_base_selling_price: 89,
          selling_price: payload.selling_price,
          created_at: '2026-04-17T12:05:00',
          updated_at: '2026-04-17T12:05:00',
        };
        branchPriceTierPrices.splice(0, branchPriceTierPrices.length, record);
        return jsonResponse(record) as never;
      }
      if (url === '/v1/tenants/tenant-acme/branches/branch-1/price-tier-prices' && method === 'GET') {
        return jsonResponse({ records: branchPriceTierPrices }) as never;
      }

      throw new Error(`Unexpected fetch call: ${method} ${url}`);
    }) as typeof fetch;
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  test('creates a price tier and assigns a branch price-tier price', async () => {
    render(<App />);

    fireEvent.change(screen.getByLabelText('Korsenex token'), {
      target: { value: 'stub:sub=owner-1;email=owner@acme.local;name=Acme Owner' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Start owner session' }));

    expect(await screen.findByText('Acme Owner', {}, { timeout: 10_000 })).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Price tier code'), { target: { value: 'VIP' } });
    fireEvent.change(screen.getByLabelText('Price tier display name'), { target: { value: 'VIP Price' } });
    fireEvent.change(screen.getByLabelText('Price tier status'), { target: { value: 'ACTIVE' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create price tier' }));

    await waitFor(() => {
      expect(screen.getByText('Latest price tier')).toBeInTheDocument();
      expect(screen.getByText('VIP :: VIP Price :: ACTIVE')).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText('Tier selling price'), { target: { value: '84' } });
    fireEvent.click(screen.getByRole('button', { name: 'Set first tier price for first product' }));

    await waitFor(() => {
      expect(screen.getByText('Latest branch tier price')).toBeInTheDocument();
      expect(screen.getByText('Classic Tea :: VIP :: 84')).toBeInTheDocument();
    });
  });
});
