/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { OwnerPromotionCampaignSection } from './OwnerPromotionCampaignSection';

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

describe('owner promotion campaign section', () => {
  const originalFetch = globalThis.fetch;
  let campaigns: Array<{
    id: string;
    tenant_id: string;
    name: string;
    status: string;
    trigger_mode: string;
    scope: string;
    discount_type: string;
    discount_value: number;
    minimum_order_amount: number | null;
    maximum_discount_amount: number | null;
    redemption_limit_total: number | null;
    redemption_count: number;
    priority: number;
    stacking_rule: string;
    target_product_ids: string[];
    target_category_codes: string[];
    created_at: string;
    updated_at: string;
    codes: Array<{
      id: string;
      tenant_id: string;
      campaign_id: string;
      code: string;
      status: string;
      redemption_limit_per_code: number | null;
      redemption_count: number;
      created_at: string;
      updated_at: string;
    }>;
  }>;

  beforeEach(() => {
    campaigns = [
      {
        id: 'campaign-1',
        tenant_id: 'tenant-acme',
        name: 'Weekend Savings',
        status: 'ACTIVE',
        trigger_mode: 'CODE',
        scope: 'CART',
        discount_type: 'PERCENTAGE',
        discount_value: 10,
        minimum_order_amount: 200,
        maximum_discount_amount: 40,
        redemption_limit_total: 500,
        redemption_count: 2,
        priority: 100,
        stacking_rule: 'STACKABLE',
        target_product_ids: [],
        target_category_codes: [],
        created_at: '2026-04-17T09:00:00Z',
        updated_at: '2026-04-17T09:00:00Z',
        codes: [],
      },
    ];

    globalThis.fetch = vi.fn(async (input, init) => {
      const url = String(input);
      const method = init?.method ?? 'GET';

      if (url.endsWith('/promotion-campaigns') && method === 'GET') {
        return jsonResponse({ records: campaigns }) as never;
      }
      if (url.endsWith('/promotion-campaigns') && method === 'POST') {
        const payload = JSON.parse(String(init?.body ?? '{}'));
        const created = {
          id: 'campaign-2',
          tenant_id: 'tenant-acme',
          name: payload.name,
          status: payload.status,
          trigger_mode: payload.trigger_mode,
          scope: payload.scope,
          discount_type: payload.discount_type,
          discount_value: Number(payload.discount_value),
          minimum_order_amount: payload.minimum_order_amount,
          maximum_discount_amount: payload.maximum_discount_amount,
          redemption_limit_total: payload.redemption_limit_total,
          redemption_count: 0,
          priority: Number(payload.priority ?? 100),
          stacking_rule: payload.stacking_rule ?? 'STACKABLE',
          target_product_ids: payload.target_product_ids ?? [],
          target_category_codes: payload.target_category_codes ?? [],
          created_at: '2026-04-17T09:30:00Z',
          updated_at: '2026-04-17T09:30:00Z',
          codes: [],
        };
        campaigns = [...campaigns, created];
        return jsonResponse(created) as never;
      }
      if (url.includes('/promotion-campaigns/campaign-1/codes') && method === 'POST') {
        const payload = JSON.parse(String(init?.body ?? '{}'));
        const code = {
          id: 'code-1',
          tenant_id: 'tenant-acme',
          campaign_id: 'campaign-1',
          code: payload.code,
          status: payload.status,
          redemption_limit_per_code: payload.redemption_limit_per_code,
          redemption_count: 0,
          created_at: '2026-04-17T09:35:00Z',
          updated_at: '2026-04-17T09:35:00Z',
        };
        campaigns = campaigns.map((campaign) => (
          campaign.id === 'campaign-1' ? { ...campaign, codes: [...campaign.codes, code] } : campaign
        ));
        return jsonResponse(code) as never;
      }
      if (url.includes('/promotion-campaigns/campaign-2/disable') && method === 'POST') {
        campaigns = campaigns.map((campaign) => (
          campaign.id === 'campaign-2' ? { ...campaign, status: 'DISABLED' } : campaign
        ));
        return jsonResponse(campaigns.find((campaign) => campaign.id === 'campaign-2')) as never;
      }
      if (url.includes('/promotion-campaigns/campaign-2/reactivate') && method === 'POST') {
        campaigns = campaigns.map((campaign) => (
          campaign.id === 'campaign-2' ? { ...campaign, status: 'ACTIVE' } : campaign
        ));
        return jsonResponse(campaigns.find((campaign) => campaign.id === 'campaign-2')) as never;
      }

      throw new Error(`Unexpected fetch call: ${method} ${url}`);
    }) as typeof fetch;
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
    cleanup();
    vi.restoreAllMocks();
  });

  test('loads campaigns and creates a shared code under the selected campaign', async () => {
    render(<OwnerPromotionCampaignSection accessToken="access-token" tenantId="tenant-acme" />);

    fireEvent.click(screen.getByRole('button', { name: 'Refresh promotion campaigns' }));
    expect(await screen.findByText('Weekend Savings')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Shared promotion code'), { target: { value: 'WEEKEND10' } });
    fireEvent.change(screen.getByLabelText('Per-code redemption limit'), { target: { value: '100' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create shared code' }));

    expect(await screen.findByText('WEEKEND10 - ACTIVE - redeemed 0')).toBeInTheDocument();

    await waitFor(() => {
      const createCodeCall = vi.mocked(globalThis.fetch).mock.calls.find(
        ([url, init]) =>
          String(url).includes('/promotion-campaigns/campaign-1/codes')
          && init?.method === 'POST',
      );
      expect(createCodeCall).toBeDefined();
      expect(JSON.parse(String(createCodeCall?.[1]?.body ?? '{}'))).toMatchObject({
        code: 'WEEKEND10',
        status: 'ACTIVE',
        redemption_limit_per_code: 100,
      });
    });
  });

  test('creates and toggles a promotion campaign', async () => {
    render(<OwnerPromotionCampaignSection accessToken="access-token" tenantId="tenant-acme" />);

    fireEvent.click(screen.getByRole('button', { name: 'Refresh promotion campaigns' }));
    await screen.findByText('Weekend Savings');

    fireEvent.change(screen.getByLabelText('Campaign name'), { target: { value: 'Welcome Flat' } });
    fireEvent.change(screen.getByLabelText('Discount type'), { target: { value: 'FLAT_AMOUNT' } });
    fireEvent.change(screen.getByLabelText('Discount value'), { target: { value: '20' } });
    fireEvent.change(screen.getByLabelText('Priority'), { target: { value: '250' } });
    fireEvent.change(screen.getByLabelText('Stacking rule'), { target: { value: 'EXCLUSIVE' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create promotion campaign' }));

    expect(await screen.findByText('Welcome Flat')).toBeInTheDocument();
    expect(screen.getByText('250')).toBeInTheDocument();
    expect(screen.getByText('EXCLUSIVE')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Disable selected campaign' }));
    expect(await screen.findByText('DISABLED')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Reactivate selected campaign' }));
    await waitFor(() => {
      expect(screen.getByText('ACTIVE')).toBeInTheDocument();
    });
  });

  test('creates an automatic item/category campaign with explicit targets', async () => {
    render(<OwnerPromotionCampaignSection accessToken="access-token" tenantId="tenant-acme" />);

    fireEvent.click(screen.getByRole('button', { name: 'Refresh promotion campaigns' }));
    await screen.findByText('Weekend Savings');

    fireEvent.change(screen.getByLabelText('Campaign name'), { target: { value: 'Tea Auto' } });
    fireEvent.change(screen.getByLabelText('Trigger mode'), { target: { value: 'AUTOMATIC' } });
    fireEvent.change(screen.getByLabelText('Scope'), { target: { value: 'ITEM_CATEGORY' } });
    fireEvent.change(screen.getByLabelText('Discount type'), { target: { value: 'PERCENTAGE' } });
    fireEvent.change(screen.getByLabelText('Discount value'), { target: { value: '15' } });
    fireEvent.change(screen.getByLabelText('Target product ids'), { target: { value: 'product-1, product-2' } });
    fireEvent.change(screen.getByLabelText('Target category codes'), { target: { value: 'TEA, SNACKS' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create promotion campaign' }));

    expect(await screen.findByText('Tea Auto')).toBeInTheDocument();
    expect(screen.getByText('AUTOMATIC')).toBeInTheDocument();
    expect(screen.getByText('ITEM_CATEGORY')).toBeInTheDocument();
    expect(screen.getByText('product-1, product-2')).toBeInTheDocument();
    expect(screen.getByText('TEA, SNACKS')).toBeInTheDocument();
    expect(screen.getByText('Automatic campaigns apply without cashier-entered shared codes.')).toBeInTheDocument();

    await waitFor(() => {
      const createCampaignCall = vi.mocked(globalThis.fetch).mock.calls.find(
        ([url, init]) =>
          String(url).endsWith('/promotion-campaigns')
          && init?.method === 'POST'
          && JSON.parse(String(init?.body ?? '{}')).name === 'Tea Auto',
      );
      expect(createCampaignCall).toBeDefined();
      expect(JSON.parse(String(createCampaignCall?.[1]?.body ?? '{}'))).toMatchObject({
        trigger_mode: 'AUTOMATIC',
        scope: 'ITEM_CATEGORY',
        priority: 100,
        stacking_rule: 'STACKABLE',
        target_product_ids: ['product-1', 'product-2'],
        target_category_codes: ['TEA', 'SNACKS'],
      });
    });
  });

  test('creates an assigned voucher campaign without shared code controls', async () => {
    render(<OwnerPromotionCampaignSection accessToken="access-token" tenantId="tenant-acme" />);

    fireEvent.click(screen.getByRole('button', { name: 'Refresh promotion campaigns' }));
    await screen.findByText('Weekend Savings');

    fireEvent.change(screen.getByLabelText('Campaign name'), { target: { value: 'Customer welcome voucher' } });
    fireEvent.change(screen.getByLabelText('Trigger mode'), { target: { value: 'ASSIGNED_VOUCHER' } });
    fireEvent.change(screen.getByLabelText('Scope'), { target: { value: 'CART' } });
    fireEvent.change(screen.getByLabelText('Discount type'), { target: { value: 'FLAT_AMOUNT' } });
    fireEvent.change(screen.getByLabelText('Discount value'), { target: { value: '50' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create promotion campaign' }));

    expect(await screen.findByText('Customer welcome voucher')).toBeInTheDocument();
    expect(screen.getByText('ASSIGNED_VOUCHER')).toBeInTheDocument();
    expect(screen.getByText('Assigned voucher campaigns are issued to one customer profile at a time and do not use shared codes.')).toBeInTheDocument();
    expect(screen.queryByLabelText('Shared promotion code')).not.toBeInTheDocument();

    await waitFor(() => {
      const createCampaignCall = vi.mocked(globalThis.fetch).mock.calls.find(
        ([url, init]) =>
          String(url).endsWith('/promotion-campaigns')
          && init?.method === 'POST'
          && JSON.parse(String(init?.body ?? '{}')).name === 'Customer welcome voucher',
      );
      expect(createCampaignCall).toBeDefined();
      expect(JSON.parse(String(createCampaignCall?.[1]?.body ?? '{}'))).toMatchObject({
        trigger_mode: 'ASSIGNED_VOUCHER',
        scope: 'CART',
        discount_type: 'FLAT_AMOUNT',
        discount_value: 50,
        priority: 100,
        stacking_rule: 'STACKABLE',
      });
    });
  });
});
