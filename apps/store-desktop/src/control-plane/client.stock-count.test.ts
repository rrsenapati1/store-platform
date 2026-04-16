import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import type {
  ControlPlaneStockCountApproval,
  ControlPlaneStockCountBoard,
  ControlPlaneStockCountReviewSession,
} from '@store/types';
import { storeControlPlaneClient } from './client';

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

describe('storeControlPlaneClient stock count reviewed-session routes', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    globalThis.fetch = vi.fn() as typeof fetch;
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  test('loads the stock-count board', async () => {
    const board: ControlPlaneStockCountBoard = {
      branch_id: 'branch-1',
      open_count: 1,
      counted_count: 0,
      approved_count: 0,
      canceled_count: 0,
      records: [
        {
          stock_count_session_id: 'scs-1',
          session_number: 'SCS-BLRFLAGSHIP-0001',
          product_id: 'product-1',
          product_name: 'Classic Tea',
          sku_code: 'tea-classic-250g',
          status: 'OPEN',
          expected_quantity: null,
          counted_quantity: null,
          variance_quantity: null,
          note: 'Aisle recount',
          review_note: null,
        },
      ],
    };
    vi.mocked(globalThis.fetch).mockResolvedValueOnce(jsonResponse(board) as never);

    const result = await storeControlPlaneClient.getStockCountBoard('access-token', 'tenant-1', 'branch-1');

    expect(result).toEqual(board);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/v1/tenants/tenant-1/branches/branch-1/stock-count-board'),
      expect.objectContaining({
        headers: expect.objectContaining({
          authorization: 'Bearer access-token',
          'content-type': 'application/json',
        }),
      }),
    );
  });

  test('creates, records, approves, and cancels a reviewed stock-count session', async () => {
    const openSession: ControlPlaneStockCountReviewSession = {
      id: 'scs-1',
      tenant_id: 'tenant-1',
      branch_id: 'branch-1',
      product_id: 'product-1',
      session_number: 'SCS-BLRFLAGSHIP-0001',
      status: 'OPEN',
      expected_quantity: null,
      counted_quantity: null,
      variance_quantity: null,
      note: 'Aisle recount',
      review_note: null,
    };
    const countedSession: ControlPlaneStockCountReviewSession = {
      ...openSession,
      status: 'COUNTED',
      expected_quantity: 12,
      counted_quantity: 10,
      variance_quantity: -2,
    };
    const approval: ControlPlaneStockCountApproval = {
      session: { ...countedSession, status: 'APPROVED', review_note: 'Approved after review' },
      stock_count: {
        id: 'count-1',
        tenant_id: 'tenant-1',
        branch_id: 'branch-1',
        product_id: 'product-1',
        counted_quantity: 10,
        expected_quantity: 12,
        variance_quantity: -2,
        note: 'Aisle recount',
        closing_stock: 10,
      },
    };

    vi.mocked(globalThis.fetch)
      .mockResolvedValueOnce(jsonResponse(openSession) as never)
      .mockResolvedValueOnce(jsonResponse(countedSession) as never)
      .mockResolvedValueOnce(jsonResponse(approval) as never)
      .mockResolvedValueOnce(
        jsonResponse({ ...countedSession, status: 'CANCELED', review_note: 'Canceled after recount' }) as never,
      );

    await storeControlPlaneClient.createStockCountSession('access-token', 'tenant-1', 'branch-1', {
      product_id: 'product-1',
      note: 'Aisle recount',
    });
    await storeControlPlaneClient.recordStockCountSession('access-token', 'tenant-1', 'branch-1', 'scs-1', {
      counted_quantity: 10,
      note: 'Blind count complete',
    });
    await storeControlPlaneClient.approveStockCountSession('access-token', 'tenant-1', 'branch-1', 'scs-1', {
      review_note: 'Approved after review',
    });
    await storeControlPlaneClient.cancelStockCountSession('access-token', 'tenant-1', 'branch-1', 'scs-1', {
      review_note: 'Canceled after recount',
    });
  });
});
