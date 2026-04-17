/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { OwnerGiftCardSection } from './OwnerGiftCardSection';

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

describe('owner gift card section', () => {
  const originalFetch = globalThis.fetch;
  let selectedCardStatus: 'ACTIVE' | 'DISABLED';
  let selectedCardBalance: number;
  let selectedCardAdjustedTotal: number;
  let giftCards: Array<{
    id: string;
    tenant_id: string;
    gift_card_code: string;
    display_name: string;
    available_balance: number;
    issued_total: number;
    redeemed_total: number;
    adjusted_total: number;
    status: 'ACTIVE' | 'DISABLED';
    created_at: string;
    updated_at: string;
  }>;
  let ledgerEntries: Array<{
    id: string;
    entry_type: string;
    source_type: string;
    source_reference_id?: string | null;
    amount: number;
    balance_after: number;
    note?: string | null;
    branch_id?: string | null;
    created_at: string;
  }>;

  function buildSelectedCard() {
    return {
      id: 'gift-card-1',
      tenant_id: 'tenant-acme',
      gift_card_code: 'GIFT-1000',
      display_name: 'Diwali gift card',
      available_balance: selectedCardBalance,
      issued_total: 500,
      redeemed_total: 100,
      adjusted_total: selectedCardAdjustedTotal,
      status: selectedCardStatus,
      created_at: '2026-04-17T09:00:00Z',
      updated_at: '2026-04-17T09:15:00Z',
      ledger_entries: ledgerEntries,
    };
  }

  beforeEach(() => {
    selectedCardStatus = 'ACTIVE';
    selectedCardBalance = 400;
    selectedCardAdjustedTotal = 0;
    giftCards = [
      {
        id: 'gift-card-1',
        tenant_id: 'tenant-acme',
        gift_card_code: 'GIFT-1000',
        display_name: 'Diwali gift card',
        available_balance: 400,
        issued_total: 500,
        redeemed_total: 100,
        adjusted_total: 0,
        status: 'ACTIVE',
        created_at: '2026-04-17T09:00:00Z',
        updated_at: '2026-04-17T09:15:00Z',
      },
    ];
    ledgerEntries = [
      {
        id: 'gift-ledger-1',
        entry_type: 'ISSUED',
        source_type: 'MANUAL_ISSUE',
        source_reference_id: null,
        amount: 500,
        balance_after: 500,
        note: 'Launch issue',
        branch_id: null,
        created_at: '2026-04-17T09:00:00Z',
      },
      {
        id: 'gift-ledger-2',
        entry_type: 'REDEEMED',
        source_type: 'SALE_REDEMPTION',
        source_reference_id: 'sale-1',
        amount: -100,
        balance_after: 400,
        note: 'Sale SINV-BLRFLAGSHIP-0004',
        branch_id: 'branch-1',
        created_at: '2026-04-17T09:10:00Z',
      },
    ];

    globalThis.fetch = vi.fn(async (input, init) => {
      const url = String(input);
      const method = init?.method ?? 'GET';

      if (url.endsWith('/gift-cards') && method === 'GET') {
        return jsonResponse({ records: giftCards }) as never;
      }
      if (url.endsWith('/gift-cards') && method === 'POST') {
        const payload = JSON.parse(String(init?.body ?? '{}'));
        const created = {
          id: 'gift-card-2',
          tenant_id: 'tenant-acme',
          gift_card_code: String(payload.gift_card_code),
          display_name: String(payload.display_name),
          available_balance: Number(payload.initial_amount),
          issued_total: Number(payload.initial_amount),
          redeemed_total: 0,
          adjusted_total: 0,
          status: 'ACTIVE' as const,
          created_at: '2026-04-17T09:30:00Z',
          updated_at: '2026-04-17T09:30:00Z',
        };
        giftCards = [created, ...giftCards];
        return jsonResponse({
          ...created,
          ledger_entries: [
            {
              id: 'gift-ledger-3',
              entry_type: 'ISSUED',
              source_type: 'MANUAL_ISSUE',
              source_reference_id: null,
              amount: Number(payload.initial_amount),
              balance_after: Number(payload.initial_amount),
              note: payload.note ?? null,
              branch_id: null,
              created_at: '2026-04-17T09:30:00Z',
            },
          ],
        }) as never;
      }
      if (url.endsWith('/gift-cards/gift-card-1') && method === 'GET') {
        return jsonResponse(buildSelectedCard()) as never;
      }
      if (url.endsWith('/gift-cards/gift-card-1/adjust') && method === 'POST') {
        const payload = JSON.parse(String(init?.body ?? '{}'));
        const amountDelta = Number(payload.amount_delta ?? 0);
        selectedCardBalance += amountDelta;
        selectedCardAdjustedTotal += amountDelta;
        const createdAt = '2026-04-17T09:40:00Z';
        ledgerEntries = [
          {
            id: 'gift-ledger-adjust',
            entry_type: 'ADJUSTED',
            source_type: 'MANUAL_ADJUSTMENT',
            source_reference_id: null,
            amount: amountDelta,
            balance_after: selectedCardBalance,
            note: payload.note ?? null,
            branch_id: null,
            created_at: createdAt,
          },
          ...ledgerEntries,
        ];
        giftCards = giftCards.map((giftCard) => (
          giftCard.id === 'gift-card-1'
            ? {
                ...giftCard,
                available_balance: selectedCardBalance,
                adjusted_total: selectedCardAdjustedTotal,
                updated_at: createdAt,
              }
            : giftCard
        ));
        return jsonResponse(buildSelectedCard()) as never;
      }
      if (url.endsWith('/gift-cards/gift-card-1/disable') && method === 'POST') {
        selectedCardStatus = 'DISABLED';
        giftCards = giftCards.map((giftCard) => (
          giftCard.id === 'gift-card-1'
            ? { ...giftCard, status: 'DISABLED', updated_at: '2026-04-17T09:50:00Z' }
            : giftCard
        ));
        return jsonResponse(buildSelectedCard()) as never;
      }
      if (url.endsWith('/gift-cards/gift-card-1/reactivate') && method === 'POST') {
        selectedCardStatus = 'ACTIVE';
        giftCards = giftCards.map((giftCard) => (
          giftCard.id === 'gift-card-1'
            ? { ...giftCard, status: 'ACTIVE', updated_at: '2026-04-17T10:00:00Z' }
            : giftCard
        ));
        return jsonResponse(buildSelectedCard()) as never;
      }

      throw new Error(`Unexpected fetch call: ${method} ${url}`);
    }) as typeof fetch;
  });

  afterEach(() => {
    cleanup();
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  test('issues, adjusts, disables, and reactivates gift cards', async () => {
    render(
      <OwnerGiftCardSection
        accessToken="session-owner"
        tenantId="tenant-acme"
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Load gift cards' }));

    expect(await screen.findByRole('button', { name: /Diwali gift card \(GIFT-1000\) ACTIVE/ })).toBeInTheDocument();
    expect(await screen.findByText('Gift card details')).toBeInTheDocument();
    expect(await screen.findByText(/Launch issue/)).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Gift card display name'), { target: { value: 'New year gift card' } });
    fireEvent.change(screen.getByLabelText('Gift card code'), { target: { value: 'GIFT-2000' } });
    fireEvent.change(screen.getByLabelText('Initial amount'), { target: { value: '250' } });
    fireEvent.change(screen.getByLabelText('Issue note'), { target: { value: 'Front desk issue' } });
    fireEvent.click(screen.getByRole('button', { name: 'Issue gift card' }));

    await waitFor(() => {
      const issueCall = vi.mocked(globalThis.fetch).mock.calls.find(
        ([url, init]) =>
          String(url).includes('/v1/tenants/tenant-acme/gift-cards') &&
          !String(url).includes('/adjust') &&
          init?.method === 'POST',
      );
      expect(issueCall).toBeDefined();
      expect(JSON.parse(String(issueCall?.[1]?.body ?? '{}'))).toEqual({
        display_name: 'New year gift card',
        gift_card_code: 'GIFT-2000',
        initial_amount: 250,
        note: 'Front desk issue',
      });
    });

    expect(await screen.findByRole('button', { name: /New year gift card \(GIFT-2000\) ACTIVE/ })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /Diwali gift card \(GIFT-1000\) ACTIVE/ }));
    expect(await screen.findByText(/Launch issue/)).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Adjust balance delta'), { target: { value: '-50' } });
    fireEvent.change(screen.getByLabelText('Adjust note'), { target: { value: 'Counter correction' } });
    fireEvent.click(screen.getByRole('button', { name: 'Adjust selected gift card' }));

    await waitFor(() => {
      const adjustCall = vi.mocked(globalThis.fetch).mock.calls.find(
        ([url, init]) =>
          String(url).includes('/v1/tenants/tenant-acme/gift-cards/gift-card-1/adjust') &&
          init?.method === 'POST',
      );
      expect(adjustCall).toBeDefined();
      expect(JSON.parse(String(adjustCall?.[1]?.body ?? '{}'))).toEqual({
        amount_delta: -50,
        note: 'Counter correction',
      });
    });

    expect(await screen.findByText('350')).toBeInTheDocument();
    expect(screen.getByText(/Counter correction/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Disable selected gift card' }));
    expect(await screen.findByText('DISABLED')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Reactivate selected gift card' }));
    expect(await screen.findByText('ACTIVE')).toBeInTheDocument();
  });
});
