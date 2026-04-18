import { startTransition } from 'react';
import type {
  ControlPlaneGoodsReceipt,
  ControlPlaneGoodsReceiptRecord,
  ControlPlaneInventoryLedgerRecord,
  ControlPlaneInventorySnapshotRecord,
  ControlPlaneStockCountBoard,
  ControlPlaneReceivingBoard,
  ControlPlaneStockAdjustment,
  ControlPlaneStockCount,
  ControlPlaneStockCountReviewSession,
  ControlPlaneTransfer,
  ControlPlaneTransferBoard,
} from '@store/types';
import { ownerControlPlaneClient } from './client';

type SetString = (value: string) => void;

export async function runCreateGoodsReceipt(params: {
  accessToken: string;
  tenantId: string;
  branchId: string;
  purchaseOrderId: string;
  note: string;
  lines: Array<{
    product_id: string;
    received_quantity: number;
    discrepancy_note: string;
    serial_numbers: string[];
  }>;
  setIsBusy: (value: boolean) => void;
  setErrorMessage: SetString;
  setLatestGoodsReceipt: (value: ControlPlaneGoodsReceipt | null) => void;
  setGoodsReceipts: (value: ControlPlaneGoodsReceiptRecord[]) => void;
  setReceivingBoard: (value: ControlPlaneReceivingBoard | null) => void;
  setInventoryLedger: (value: ControlPlaneInventoryLedgerRecord[]) => void;
  setInventorySnapshot: (value: ControlPlaneInventorySnapshotRecord[]) => void;
  resetForm: () => void;
}) {
  const {
    accessToken,
    tenantId,
    branchId,
    purchaseOrderId,
    note,
    lines,
    setIsBusy,
    setErrorMessage,
    setLatestGoodsReceipt,
    setGoodsReceipts,
    setReceivingBoard,
    setInventoryLedger,
    setInventorySnapshot,
    resetForm,
  } = params;

  setIsBusy(true);
  setErrorMessage('');
  try {
    const goodsReceipt = await ownerControlPlaneClient.createGoodsReceipt(accessToken, tenantId, branchId, {
      purchase_order_id: purchaseOrderId,
      note: note || null,
      lines: lines.map((line) => ({
        product_id: line.product_id,
        received_quantity: line.received_quantity,
        discrepancy_note: line.discrepancy_note || null,
        serial_numbers: line.serial_numbers.length ? line.serial_numbers : null,
      })),
    });
    const [goodsReceiptList, board, ledger, snapshot] = await Promise.all([
      ownerControlPlaneClient.listGoodsReceipts(accessToken, tenantId, branchId),
      ownerControlPlaneClient.getReceivingBoard(accessToken, tenantId, branchId),
      ownerControlPlaneClient.listInventoryLedger(accessToken, tenantId, branchId),
      ownerControlPlaneClient.listInventorySnapshot(accessToken, tenantId, branchId),
    ]);
    startTransition(() => {
      setLatestGoodsReceipt(goodsReceipt);
      setGoodsReceipts(goodsReceiptList.records);
      setReceivingBoard(board);
      setInventoryLedger(ledger.records);
      setInventorySnapshot(snapshot.records);
      resetForm();
    });
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to create goods receipt');
  } finally {
    setIsBusy(false);
  }
}

export async function runCreateStockAdjustment(params: {
  accessToken: string;
  tenantId: string;
  branchId: string;
  productId: string;
  quantityDelta: number;
  reason: string;
  setIsBusy: (value: boolean) => void;
  setErrorMessage: SetString;
  setLatestStockAdjustment: (value: ControlPlaneStockAdjustment | null) => void;
  setInventoryLedger: (value: ControlPlaneInventoryLedgerRecord[]) => void;
  setInventorySnapshot: (value: ControlPlaneInventorySnapshotRecord[]) => void;
  resetForm: () => void;
}) {
  const {
    accessToken,
    tenantId,
    branchId,
    productId,
    quantityDelta,
    reason,
    setIsBusy,
    setErrorMessage,
    setLatestStockAdjustment,
    setInventoryLedger,
    setInventorySnapshot,
    resetForm,
  } = params;

  setIsBusy(true);
  setErrorMessage('');
  try {
    const adjustment = await ownerControlPlaneClient.createStockAdjustment(accessToken, tenantId, branchId, {
      product_id: productId,
      quantity_delta: quantityDelta,
      reason,
      note: reason || null,
    });
    const [ledger, snapshot] = await Promise.all([
      ownerControlPlaneClient.listInventoryLedger(accessToken, tenantId, branchId),
      ownerControlPlaneClient.listInventorySnapshot(accessToken, tenantId, branchId),
    ]);
    startTransition(() => {
      setLatestStockAdjustment(adjustment);
      setInventoryLedger(ledger.records);
      setInventorySnapshot(snapshot.records);
      resetForm();
    });
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to post stock adjustment');
  } finally {
    setIsBusy(false);
  }
}

export async function runCreateStockCount(params: {
  accessToken: string;
  tenantId: string;
  branchId: string;
  productId: string;
  countedQuantity: number;
  note: string;
  setIsBusy: (value: boolean) => void;
  setErrorMessage: SetString;
  setLatestStockCount: (value: ControlPlaneStockCount | null) => void;
  setInventoryLedger: (value: ControlPlaneInventoryLedgerRecord[]) => void;
  setInventorySnapshot: (value: ControlPlaneInventorySnapshotRecord[]) => void;
  resetForm: () => void;
}) {
  const {
    accessToken,
    tenantId,
    branchId,
    productId,
    countedQuantity,
    note,
    setIsBusy,
    setErrorMessage,
    setLatestStockCount,
    setInventoryLedger,
    setInventorySnapshot,
    resetForm,
  } = params;

  setIsBusy(true);
  setErrorMessage('');
  try {
    const stockCount = await ownerControlPlaneClient.createStockCount(accessToken, tenantId, branchId, {
      product_id: productId,
      counted_quantity: countedQuantity,
      note: note || null,
    });
    const [ledger, snapshot] = await Promise.all([
      ownerControlPlaneClient.listInventoryLedger(accessToken, tenantId, branchId),
      ownerControlPlaneClient.listInventorySnapshot(accessToken, tenantId, branchId),
    ]);
    startTransition(() => {
      setLatestStockCount(stockCount);
      setInventoryLedger(ledger.records);
      setInventorySnapshot(snapshot.records);
      resetForm();
    });
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to record stock count');
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
  setLatestStockCountSession: (value: ControlPlaneStockCountReviewSession | null) => void;
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
    setLatestStockCountSession,
    setStockCountBoard,
  } = params;

  setIsBusy(true);
  setErrorMessage('');
  try {
    const sessionRecord = await ownerControlPlaneClient.createStockCountSession(accessToken, tenantId, branchId, {
      product_id: productId,
      note: note || null,
    });
    const board = await ownerControlPlaneClient.getStockCountBoard(accessToken, tenantId, branchId);
    startTransition(() => {
      setLatestStockCountSession(sessionRecord);
      setStockCountBoard(board);
    });
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to open stock count session');
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
  setLatestStockCountSession: (value: ControlPlaneStockCountReviewSession | null) => void;
  setStockCountBoard: (value: ControlPlaneStockCountBoard | null) => void;
  resetForm: () => void;
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
    setLatestStockCountSession,
    setStockCountBoard,
    resetForm,
  } = params;

  setIsBusy(true);
  setErrorMessage('');
  try {
    const sessionRecord = await ownerControlPlaneClient.recordStockCountSession(accessToken, tenantId, branchId, stockCountSessionId, {
      counted_quantity: countedQuantity,
      note: note || null,
    });
    const board = await ownerControlPlaneClient.getStockCountBoard(accessToken, tenantId, branchId);
    startTransition(() => {
      setLatestStockCountSession(sessionRecord);
      setStockCountBoard(board);
      resetForm();
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
  setLatestStockCountSession: (value: ControlPlaneStockCountReviewSession | null) => void;
  setLatestStockCount: (value: ControlPlaneStockCount | null) => void;
  setStockCountBoard: (value: ControlPlaneStockCountBoard | null) => void;
  setInventoryLedger: (value: ControlPlaneInventoryLedgerRecord[]) => void;
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
    setLatestStockCountSession,
    setLatestStockCount,
    setStockCountBoard,
    setInventoryLedger,
    setInventorySnapshot,
  } = params;

  setIsBusy(true);
  setErrorMessage('');
  try {
    const approval = await ownerControlPlaneClient.approveStockCountSession(accessToken, tenantId, branchId, stockCountSessionId, {
      review_note: reviewNote || null,
    });
    const [board, ledger, snapshot] = await Promise.all([
      ownerControlPlaneClient.getStockCountBoard(accessToken, tenantId, branchId),
      ownerControlPlaneClient.listInventoryLedger(accessToken, tenantId, branchId),
      ownerControlPlaneClient.listInventorySnapshot(accessToken, tenantId, branchId),
    ]);
    startTransition(() => {
      setLatestStockCountSession(approval.session);
      setLatestStockCount(approval.stock_count);
      setStockCountBoard(board);
      setInventoryLedger(ledger.records);
      setInventorySnapshot(snapshot.records);
    });
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to approve stock count session');
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
  setLatestStockCountSession: (value: ControlPlaneStockCountReviewSession | null) => void;
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
    setLatestStockCountSession,
    setStockCountBoard,
  } = params;

  setIsBusy(true);
  setErrorMessage('');
  try {
    const sessionRecord = await ownerControlPlaneClient.cancelStockCountSession(accessToken, tenantId, branchId, stockCountSessionId, {
      review_note: reviewNote || null,
    });
    const board = await ownerControlPlaneClient.getStockCountBoard(accessToken, tenantId, branchId);
    startTransition(() => {
      setLatestStockCountSession(sessionRecord);
      setStockCountBoard(board);
    });
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to cancel stock count session');
  } finally {
    setIsBusy(false);
  }
}

export async function runCreateBranchTransfer(params: {
  accessToken: string;
  tenantId: string;
  branchId: string;
  destinationBranchId: string;
  productId: string;
  quantity: number;
  setIsBusy: (value: boolean) => void;
  setErrorMessage: SetString;
  setLatestTransfer: (value: ControlPlaneTransfer | null) => void;
  setTransferBoard: (value: ControlPlaneTransferBoard | null) => void;
  setInventoryLedger: (value: ControlPlaneInventoryLedgerRecord[]) => void;
  setInventorySnapshot: (value: ControlPlaneInventorySnapshotRecord[]) => void;
  resetForm: () => void;
}) {
  const {
    accessToken,
    tenantId,
    branchId,
    destinationBranchId,
    productId,
    quantity,
    setIsBusy,
    setErrorMessage,
    setLatestTransfer,
    setTransferBoard,
    setInventoryLedger,
    setInventorySnapshot,
    resetForm,
  } = params;

  setIsBusy(true);
  setErrorMessage('');
  try {
    const transfer = await ownerControlPlaneClient.createTransfer(accessToken, tenantId, branchId, {
      destination_branch_id: destinationBranchId,
      product_id: productId,
      quantity,
      note: 'Branch rebalance',
    });
    const [board, ledger, snapshot] = await Promise.all([
      ownerControlPlaneClient.getTransferBoard(accessToken, tenantId, branchId),
      ownerControlPlaneClient.listInventoryLedger(accessToken, tenantId, branchId),
      ownerControlPlaneClient.listInventorySnapshot(accessToken, tenantId, branchId),
    ]);
    startTransition(() => {
      setLatestTransfer(transfer);
      setTransferBoard(board);
      setInventoryLedger(ledger.records);
      setInventorySnapshot(snapshot.records);
      resetForm();
    });
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to create branch transfer');
  } finally {
    setIsBusy(false);
  }
}
