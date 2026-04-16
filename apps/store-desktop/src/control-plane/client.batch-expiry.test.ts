import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import type {
  ControlPlaneBatchExpiryBoard,
  ControlPlaneBatchExpiryReviewApproval,
  ControlPlaneBatchExpiryReviewSession,
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

describe('storeControlPlaneClient batch expiry reviewed-session routes', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    globalThis.fetch = vi.fn() as typeof fetch;
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  test('loads the batch expiry board', async () => {
    const board: ControlPlaneBatchExpiryBoard = {
      branch_id: 'branch-1',
      open_count: 1,
      reviewed_count: 0,
      approved_count: 0,
      canceled_count: 0,
      records: [
        {
          batch_expiry_session_id: 'bes-1',
          session_number: 'BES-0001',
          batch_lot_id: 'lot-1',
          product_id: 'product-1',
          product_name: 'Classic Tea',
          sku_code: 'tea-classic-250g',
          batch_number: 'BATCH-A',
          status: 'OPEN',
          remaining_quantity_snapshot: 6,
          proposed_quantity: null,
          reason: null,
          note: 'Shelf check',
          review_note: null,
        },
      ],
    };
    vi.mocked(globalThis.fetch).mockResolvedValueOnce(jsonResponse(board) as never);

    const result = await storeControlPlaneClient.getBatchExpiryBoard('access-token', 'tenant-1', 'branch-1');

    expect(result).toEqual(board);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/v1/tenants/tenant-1/branches/branch-1/batch-expiry-board'),
      expect.objectContaining({
        headers: expect.objectContaining({
          authorization: 'Bearer access-token',
          'content-type': 'application/json',
        }),
      }),
    );
  });

  test('creates a batch expiry review session', async () => {
    const session: ControlPlaneBatchExpiryReviewSession = {
      id: 'bes-1',
      tenant_id: 'tenant-1',
      branch_id: 'branch-1',
      batch_lot_id: 'lot-1',
      product_id: 'product-1',
      session_number: 'BES-0001',
      status: 'OPEN',
      remaining_quantity_snapshot: 6,
      proposed_quantity: null,
      reason: null,
      note: 'Shelf check',
      review_note: null,
    };
    vi.mocked(globalThis.fetch).mockResolvedValueOnce(jsonResponse(session) as never);

    const result = await storeControlPlaneClient.createBatchExpirySession('access-token', 'tenant-1', 'branch-1', {
      batch_lot_id: 'lot-1',
      note: 'Shelf check',
    });

    expect(result).toEqual(session);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/v1/tenants/tenant-1/branches/branch-1/batch-expiry-sessions'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          batch_lot_id: 'lot-1',
          note: 'Shelf check',
        }),
      }),
    );
  });

  test('records a reviewed batch expiry quantity and reason', async () => {
    const session: ControlPlaneBatchExpiryReviewSession = {
      id: 'bes-1',
      tenant_id: 'tenant-1',
      branch_id: 'branch-1',
      batch_lot_id: 'lot-1',
      product_id: 'product-1',
      session_number: 'BES-0001',
      status: 'REVIEWED',
      remaining_quantity_snapshot: 6,
      proposed_quantity: 1,
      reason: 'Expired on shelf',
      note: 'Shelf check',
      review_note: null,
    };
    vi.mocked(globalThis.fetch).mockResolvedValueOnce(jsonResponse(session) as never);

    const result = await storeControlPlaneClient.recordBatchExpirySession(
      'access-token',
      'tenant-1',
      'branch-1',
      'bes-1',
      {
        quantity: 1,
        reason: 'Expired on shelf',
      },
    );

    expect(result).toEqual(session);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/v1/tenants/tenant-1/branches/branch-1/batch-expiry-sessions/bes-1/review'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          quantity: 1,
          reason: 'Expired on shelf',
        }),
      }),
    );
  });

  test('approves a reviewed batch expiry session', async () => {
    const approval: ControlPlaneBatchExpiryReviewApproval = {
      session: {
        id: 'bes-1',
        tenant_id: 'tenant-1',
        branch_id: 'branch-1',
        batch_lot_id: 'lot-1',
        product_id: 'product-1',
        session_number: 'BES-0001',
        status: 'APPROVED',
        remaining_quantity_snapshot: 6,
        proposed_quantity: 1,
        reason: 'Expired on shelf',
        note: 'Shelf check',
        review_note: 'Approved after review',
      },
      write_off: {
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
      },
    };
    vi.mocked(globalThis.fetch).mockResolvedValueOnce(jsonResponse(approval) as never);

    const result = await storeControlPlaneClient.approveBatchExpirySession(
      'access-token',
      'tenant-1',
      'branch-1',
      'bes-1',
      {
        review_note: 'Approved after review',
      },
    );

    expect(result).toEqual(approval);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/v1/tenants/tenant-1/branches/branch-1/batch-expiry-sessions/bes-1/approve'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          review_note: 'Approved after review',
        }),
      }),
    );
  });

  test('cancels a batch expiry review session', async () => {
    const session: ControlPlaneBatchExpiryReviewSession = {
      id: 'bes-1',
      tenant_id: 'tenant-1',
      branch_id: 'branch-1',
      batch_lot_id: 'lot-1',
      product_id: 'product-1',
      session_number: 'BES-0001',
      status: 'CANCELED',
      remaining_quantity_snapshot: 6,
      proposed_quantity: 1,
      reason: 'Expired on shelf',
      note: 'Shelf check',
      review_note: 'Canceled after recount',
    };
    vi.mocked(globalThis.fetch).mockResolvedValueOnce(jsonResponse(session) as never);

    const result = await storeControlPlaneClient.cancelBatchExpirySession(
      'access-token',
      'tenant-1',
      'branch-1',
      'bes-1',
      {
        review_note: 'Canceled after recount',
      },
    );

    expect(result).toEqual(session);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/v1/tenants/tenant-1/branches/branch-1/batch-expiry-sessions/bes-1/cancel'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          review_note: 'Canceled after recount',
        }),
      }),
    );
  });
});
