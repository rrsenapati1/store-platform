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

describe('owner batch expiry flow', () => {
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
        records: [{ branch_id: 'branch-1', tenant_id: 'tenant-acme', name: 'Bengaluru Flagship', code: 'blr-flagship', status: 'ACTIVE' }],
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
            barcode: 'ACMETEACLASSIC',
            hsn_sac_code: '0902',
            gst_rate: 5,
            selling_price: 92.5,
            status: 'ACTIVE',
          },
        ],
      }),
      jsonResponse({ records: [] }),
      jsonResponse({ records: [] }),
      jsonResponse({ records: [] }),
      jsonResponse({
        records: [
          {
            goods_receipt_id: 'goods-receipt-1',
            goods_receipt_number: 'GRN-BLRFLAGSHIP-0001',
            purchase_order_id: 'purchase-order-1',
            purchase_order_number: 'PO-BLRFLAGSHIP-0001',
            supplier_id: 'supplier-1',
            supplier_name: 'Acme Tea Traders',
            received_on: '2026-04-14',
            line_count: 1,
            received_quantity: 10,
          },
        ],
      }),
      jsonResponse({
        goods_receipt_id: 'goods-receipt-1',
        records: [
          {
            id: 'lot-1',
            product_id: 'product-1',
            batch_number: 'BATCH-A',
            quantity: 6,
            expiry_date: '2026-04-21',
          },
          {
            id: 'lot-2',
            product_id: 'product-1',
            batch_number: 'BATCH-B',
            quantity: 4,
            expiry_date: '2026-07-13',
          },
        ],
      }),
      jsonResponse({
        branch_id: 'branch-1',
        tracked_lot_count: 2,
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
          {
            batch_lot_id: 'lot-2',
            product_id: 'product-1',
            product_name: 'Classic Tea',
            batch_number: 'BATCH-B',
            expiry_date: '2026-07-13',
            days_to_expiry: 90,
            received_quantity: 4,
            written_off_quantity: 0,
            remaining_quantity: 4,
            status: 'FRESH',
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
        tracked_lot_count: 2,
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
          {
            batch_lot_id: 'lot-2',
            product_id: 'product-1',
            product_name: 'Classic Tea',
            batch_number: 'BATCH-B',
            expiry_date: '2026-07-13',
            days_to_expiry: 90,
            received_quantity: 4,
            written_off_quantity: 0,
            remaining_quantity: 4,
            status: 'FRESH',
          },
        ],
      }),
      jsonResponse({
        records: [
          {
            inventory_ledger_entry_id: 'ledger-1',
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            entry_type: 'EXPIRY_WRITE_OFF',
            quantity: -1,
            reference_type: 'batch_expiry_write_off',
            reference_id: 'write-off-1',
          },
        ],
      }),
      jsonResponse({
        records: [
          {
            product_id: 'product-1',
            product_name: 'Classic Tea',
            sku_code: 'tea-classic-250g',
            stock_on_hand: 9,
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

  test('records batch lots for the latest goods receipt and writes off the first expiring lot', async () => {
    render(<App />);

    fireEvent.change(screen.getByLabelText('Korsenex token'), {
      target: { value: 'stub:sub=owner-1;email=owner@acme.local;name=Acme Owner' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Start owner session' }));

    expect(await screen.findByText('Acme Owner')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Lot A batch number'), { target: { value: 'BATCH-A' } });
    fireEvent.change(screen.getByLabelText('Lot A quantity'), { target: { value: '6' } });
    fireEvent.change(screen.getByLabelText('Lot A expiry date'), { target: { value: '2026-04-21' } });
    fireEvent.change(screen.getByLabelText('Lot B batch number'), { target: { value: 'BATCH-B' } });
    fireEvent.change(screen.getByLabelText('Lot B quantity'), { target: { value: '4' } });
    fireEvent.change(screen.getByLabelText('Lot B expiry date'), { target: { value: '2026-07-13' } });
    fireEvent.click(screen.getByRole('button', { name: 'Record batch lots on latest goods receipt' }));

    await waitFor(() => {
      expect(screen.getByText('Latest batch lot intake')).toBeInTheDocument();
      expect(screen.getByText('BATCH-A, BATCH-B')).toBeInTheDocument();
      expect(screen.getAllByText('2').length).toBeGreaterThan(0);
    });

    fireEvent.change(screen.getByLabelText('Expiry write-off quantity'), { target: { value: '1' } });
    fireEvent.change(screen.getByLabelText('Expiry write-off reason'), { target: { value: 'Expired on shelf' } });
    fireEvent.click(screen.getByRole('button', { name: 'Write off first expiring lot' }));

    await waitFor(() => {
      expect(screen.getByText('Latest expiry write-off')).toBeInTheDocument();
      expect(screen.getByText('5')).toBeInTheDocument();
      expect(screen.getAllByText('EXPIRING_SOON').length).toBeGreaterThan(0);
    });
  });
});
