import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import type { ControlPlaneReplenishmentBoard } from '@store/types';
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

describe('storeControlPlaneClient replenishment routes', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    globalThis.fetch = vi.fn() as typeof fetch;
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  test('loads the replenishment board', async () => {
    const board: ControlPlaneReplenishmentBoard = {
      branch_id: 'branch-1',
      low_stock_count: 1,
      adequate_count: 1,
      records: [
        {
          product_id: 'product-1',
          product_name: 'Classic Tea',
          sku_code: 'tea-classic-250g',
          availability_status: 'ACTIVE',
          stock_on_hand: 4,
          reorder_point: 10,
          target_stock: 24,
          suggested_reorder_quantity: 20,
          replenishment_status: 'LOW_STOCK',
        },
      ],
    };
    vi.mocked(globalThis.fetch).mockResolvedValueOnce(jsonResponse(board) as never);

    const result = await storeControlPlaneClient.getReplenishmentBoard('access-token', 'tenant-1', 'branch-1');

    expect(result).toEqual(board);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/v1/tenants/tenant-1/branches/branch-1/replenishment-board'),
      expect.objectContaining({
        headers: expect.objectContaining({
          authorization: 'Bearer access-token',
          'content-type': 'application/json',
        }),
      }),
    );
  });
});
