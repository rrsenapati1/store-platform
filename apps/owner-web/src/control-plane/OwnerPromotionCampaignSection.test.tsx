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
    discount_type: string;
    discount_value: number;
    minimum_order_amount: number | null;
    maximum_discount_amount: number | null;
    redemption_limit_total: number | null;
    redemption_count: number;
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
        discount_type: 'PERCENTAGE',
        discount_value: 10,
        minimum_order_amount: 200,
        maximum_discount_amount: 40,
        redemption_limit_total: 500,
        redemption_count: 2,
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
          discount_type: payload.discount_type,
          discount_value: Number(payload.discount_value),
          minimum_order_amount: payload.minimum_order_amount,
          maximum_discount_amount: payload.maximum_discount_amount,
          redemption_limit_total: payload.redemption_limit_total,
          redemption_count: 0,
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
    fireEvent.click(screen.getByRole('button', { name: 'Create promotion campaign' }));

    expect(await screen.findByText('Welcome Flat')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Disable selected campaign' }));
    expect(await screen.findByText('DISABLED')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Reactivate selected campaign' }));
    await waitFor(() => {
      expect(screen.getByText('ACTIVE')).toBeInTheDocument();
    });
  });
});
