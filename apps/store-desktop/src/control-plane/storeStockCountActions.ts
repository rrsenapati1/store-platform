import { startTransition } from 'react';
import type {
  ControlPlaneInventorySnapshotRecord,
  ControlPlaneStockCount,
  ControlPlaneStockCountBoard,
  ControlPlaneStockCountReviewSession,
} from '@store/types';
import { storeControlPlaneClient } from './client';

type SetString = (value: string) => void;

export async function runLoadStockCountBoard(params: {
  accessToken: string;
  tenantId: string;
  branchId: string;
  setIsBusy: (value: boolean) => void;
  setErrorMessage: SetString;
  setStockCountBoard: (value: ControlPlaneStockCountBoard | null) => void;
  setSelectedStockCountProductId: (value: string) => void;
}) {
  const {
    accessToken,
    tenantId,
    branchId,
    setIsBusy,
    setErrorMessage,
    setStockCountBoard,
    setSelectedStockCountProductId,
  } = params;

  setIsBusy(true);
  setErrorMessage('');
  try {
    const board = await storeControlPlaneClient.getStockCountBoard(accessToken, tenantId, branchId);
    startTransition(() => {
      setStockCountBoard(board);
      if (board.records[0]?.product_id) {
        setSelectedStockCountProductId(board.records[0].product_id);
      }
    });
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to load stock-count board');
  } finally {
    setIsBusy(false);
  }
}

export async function runCreateStockCountSession(params: {
  accessToken: string;
  tenantId: string;
  branchId: string;
  productId: string;
  note: string;
  setIsBusy: (value: boolean) => void;
  setErrorMessage: SetString;
  setActiveStockCountSession: (value: ControlPlaneStockCountReviewSession | null) => void;
  setStockCountBoard: (value: ControlPlaneStockCountBoard | null) => void;
}) {
  const {
    accessToken,
    tenantId,
    branchId,
    productId,
    note,
    setIsBusy,
    setErrorMessage,
    setActiveStockCountSession,
    setStockCountBoard,
  } = params;

  setIsBusy(true);
  setErrorMessage('');
  try {
    const session = await storeControlPlaneClient.createStockCountSession(accessToken, tenantId, branchId, {
      product_id: productId,
      note: note || null,
    });
    const board = await storeControlPlaneClient.getStockCountBoard(accessToken, tenantId, branchId);
    startTransition(() => {
      setActiveStockCountSession(session);
      setStockCountBoard(board);
    });
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to open stock-count session');
  } finally {
    setIsBusy(false);
  }
}

export async function runRecordStockCountSession(params: {
  accessToken: string;
  tenantId: string;
  branchId: string;
  stockCountSessionId: string;
  countedQuantity: number;
  note: string;
  setIsBusy: (value: boolean) => void;
  setErrorMessage: SetString;
  setActiveStockCountSession: (value: ControlPlaneStockCountReviewSession | null) => void;
  setStockCountBoard: (value: ControlPlaneStockCountBoard | null) => void;
}) {
  const {
    accessToken,
    tenantId,
    branchId,
    stockCountSessionId,
    countedQuantity,
    note,
    setIsBusy,
    setErrorMessage,
    setActiveStockCountSession,
    setStockCountBoard,
  } = params;

  setIsBusy(true);
  setErrorMessage('');
  try {
    const session = await storeControlPlaneClient.recordStockCountSession(
      accessToken,
      tenantId,
      branchId,
      stockCountSessionId,
      {
        counted_quantity: countedQuantity,
        note: note || null,
      },
    );
    const board = await storeControlPlaneClient.getStockCountBoard(accessToken, tenantId, branchId);
    startTransition(() => {
      setActiveStockCountSession(session);
      setStockCountBoard(board);
    });
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to record blind count');
  } finally {
    setIsBusy(false);
  }
}

export async function runApproveStockCountSession(params: {
  accessToken: string;
  tenantId: string;
  branchId: string;
  stockCountSessionId: string;
  reviewNote: string;
  setIsBusy: (value: boolean) => void;
  setErrorMessage: SetString;
  setActiveStockCountSession: (value: ControlPlaneStockCountReviewSession | null) => void;
  setLatestApprovedStockCount: (value: ControlPlaneStockCount | null) => void;
  setStockCountBoard: (value: ControlPlaneStockCountBoard | null) => void;
  setInventorySnapshot: (value: ControlPlaneInventorySnapshotRecord[]) => void;
}) {
  const {
    accessToken,
    tenantId,
    branchId,
    stockCountSessionId,
    reviewNote,
    setIsBusy,
    setErrorMessage,
    setActiveStockCountSession,
    setLatestApprovedStockCount,
    setStockCountBoard,
    setInventorySnapshot,
  } = params;

  setIsBusy(true);
  setErrorMessage('');
  try {
    const approval = await storeControlPlaneClient.approveStockCountSession(
      accessToken,
      tenantId,
      branchId,
      stockCountSessionId,
      {
        review_note: reviewNote || null,
      },
    );
    const [board, snapshot] = await Promise.all([
      storeControlPlaneClient.getStockCountBoard(accessToken, tenantId, branchId),
      storeControlPlaneClient.listInventorySnapshot(accessToken, tenantId, branchId),
    ]);
    startTransition(() => {
      setActiveStockCountSession(approval.session);
      setLatestApprovedStockCount(approval.stock_count);
      setStockCountBoard(board);
      setInventorySnapshot(snapshot.records);
    });
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to approve stock-count session');
  } finally {
    setIsBusy(false);
  }
}

export async function runCancelStockCountSession(params: {
  accessToken: string;
  tenantId: string;
  branchId: string;
  stockCountSessionId: string;
  reviewNote: string;
  setIsBusy: (value: boolean) => void;
  setErrorMessage: SetString;
  setActiveStockCountSession: (value: ControlPlaneStockCountReviewSession | null) => void;
  setStockCountBoard: (value: ControlPlaneStockCountBoard | null) => void;
}) {
  const {
    accessToken,
    tenantId,
    branchId,
    stockCountSessionId,
    reviewNote,
    setIsBusy,
    setErrorMessage,
    setActiveStockCountSession,
    setStockCountBoard,
  } = params;

  setIsBusy(true);
  setErrorMessage('');
  try {
    const session = await storeControlPlaneClient.cancelStockCountSession(
      accessToken,
      tenantId,
      branchId,
      stockCountSessionId,
      {
        review_note: reviewNote || null,
      },
    );
    const board = await storeControlPlaneClient.getStockCountBoard(accessToken, tenantId, branchId);
    startTransition(() => {
      setActiveStockCountSession(session);
      setStockCountBoard(board);
    });
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to cancel stock-count session');
  } finally {
    setIsBusy(false);
  }
}
