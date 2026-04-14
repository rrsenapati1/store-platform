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

describe('store runtime batch expiry flow', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    const responses = [
      jsonResponse({ access_token: 'session-stock-clerk', token_type: 'Bearer' }),
      jsonResponse({
        user_id: 'user-stock-clerk',
        email: 'stock@acme.local',
        full_name: 'Stock Clerk',
        is_platform_admin: false,
        tenant_memberships: [],
        branch_memberships: [{ tenant_id: 'tenant-acme', branch_id: 'branch-1', role_name: 'stock_clerk', status: 'ACTIVE' }],
      }),
      jsonResponse({
        id: 'tenant-acme',
        name: 'Acme Retail',
        slug: 'acme-retail',
        status: 'ACTIVE',
        onboarding_status: 'BRANCH_READY',
      }),
      jsonResponse({
        records: [{ branch_id: 'branch-1', tenant_id: 'tenant-acme', name: 'Bengaluru Flagship', code: 'blr-flagship', status: 'ACTIVE' }],
      }),
      jsonResponse({ records: [] }),
      jsonResponse({ records: [] }),
      jsonResponse({ records: [] }),
      jsonResponse({
        records: [
          {
            id: 'device-1',
            tenant_id: 'tenant-acme',
            branch_id: 'branch-1',
            device_name: 'Backroom Tablet',
            device_code: 'backroom-1',
            session_surface: 'store_desktop',
            status: 'ACTIVE',
            assigned_staff_profile_id: null,
            assigned_staff_full_name: null,
          },
        ],
      }),
      jsonResponse({
        branch_id: 'branch-1',
        tracked_lot_count: 1,
        expiring_soon_count: 1,
        expired_count: 0,
        untracked_stock_quantity: 0,
        records: [
          {
            batch_lot_id: 'lot-1',
            product_id: 'product-1',
            product_name: 'Classic Tea',
            batch_number: 'BATCH-A',
            expiry_date: '2026-04-21',
            days_to_expiry: 7,
            received_quantity: 6,
            written_off_quantity: 0,
            remaining_quantity: 6,
            status: 'EXPIRING_SOON',
          },
        ],
      }),
      jsonResponse({
        batch_lot_id: 'lot-1',
        product_id: 'product-1',
        product_name: 'Classic Tea',
        batch_number: 'BATCH-A',
        expiry_date: '2026-04-21',
        received_quantity: 6,
        written_off_quantity: 1,
        remaining_quantity: 5,
        status: 'EXPIRING_SOON',
        reason: 'Expired on shelf',
      }),
      jsonResponse({
        branch_id: 'branch-1',
        tracked_lot_count: 1,
        expiring_soon_count: 1,
        expired_count: 0,
        untracked_stock_quantity: 0,
        records: [
          {
            batch_lot_id: 'lot-1',
            product_id: 'product-1',
            product_name: 'Classic Tea',
            batch_number: 'BATCH-A',
            expiry_date: '2026-04-21',
            days_to_expiry: 7,
            received_quantity: 6,
            written_off_quantity: 1,
            remaining_quantity: 5,
            status: 'EXPIRING_SOON',
          },
        ],
      }),
      jsonResponse({
        records: [
          {
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            stock_on_hand: 5,
            last_entry_type: 'EXPIRY_WRITE_OFF',
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

  test('loads the branch expiry report and writes off the first expiring lot', async () => {
    render(<App />);

    fireEvent.change(screen.getByLabelText('Korsenex token'), {
      target: { value: 'stub:sub=stock-clerk-1;email=stock@acme.local;name=Stock Clerk' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Start runtime session' }));

    expect(await screen.findByText('Stock Clerk')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Load branch expiry report' }));

    await waitFor(() => {
      expect(screen.getByText('Latest branch expiry report')).toBeInTheDocument();
      expect(screen.getByText(/BATCH-A/)).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText('Expiry write-off quantity'), { target: { value: '1' } });
    fireEvent.change(screen.getByLabelText('Expiry write-off reason'), { target: { value: 'Expired on shelf' } });
    fireEvent.click(screen.getByRole('button', { name: 'Write off first expiring lot' }));

    await waitFor(() => {
      expect(screen.getByText('Latest batch write-off')).toBeInTheDocument();
      expect(screen.getByText('5')).toBeInTheDocument();
    });
  });
});
