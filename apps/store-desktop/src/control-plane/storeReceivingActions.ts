import { startTransition } from 'react';
import type {
  ControlPlaneGoodsReceipt,
  ControlPlaneGoodsReceiptRecord,
  ControlPlaneInventorySnapshotRecord,
  ControlPlanePurchaseOrder,
  ControlPlaneReceivingBoard,
} from '@store/types';
import { storeControlPlaneClient } from './client';

type SetString = (value: string) => void;

export interface StoreReceivingLineDraft {
  product_id: string;
  product_name: string;
  sku_code: string;
  ordered_quantity: number;
  received_quantity: string;
  discrepancy_note: string;
}

function buildReceivingLineDrafts(purchaseOrder: ControlPlanePurchaseOrder): StoreReceivingLineDraft[] {
  return purchaseOrder.lines.map((line) => ({
    product_id: line.product_id,
    product_name: line.product_name,
    sku_code: line.sku_code,
    ordered_quantity: line.quantity,
    received_quantity: '',
    discrepancy_note: '',
  }));
}

function latestGoodsReceiptFromList(records: ControlPlaneGoodsReceiptRecord[]): ControlPlaneGoodsReceipt | null {
  const latest = records[records.length - 1];
  if (!latest) {
    return null;
  }
  return {
    id: latest.goods_receipt_id,
    tenant_id: '',
    branch_id: '',
    purchase_order_id: latest.purchase_order_id,
    supplier_id: latest.supplier_id,
    goods_receipt_number: latest.goods_receipt_number,
    received_on: latest.received_on,
    note: latest.note ?? null,
    ordered_quantity_total: latest.ordered_quantity ?? 0,
    received_quantity_total: latest.received_quantity,
    variance_quantity_total: latest.variance_quantity ?? 0,
    has_discrepancy: latest.has_discrepancy,
    lines: [],
  };
}

export async function runLoadReceivingBoard(params: {
  accessToken: string;
  tenantId: string;
  branchId: string;
  setIsBusy: (value: boolean) => void;
  setErrorMessage: SetString;
  setReceivingBoard: (value: ControlPlaneReceivingBoard | null) => void;
  setGoodsReceipts: (value: ControlPlaneGoodsReceiptRecord[]) => void;
  setLatestGoodsReceipt: (value: ControlPlaneGoodsReceipt | null) => void;
}) {
  const {
    accessToken,
    tenantId,
    branchId,
    setIsBusy,
    setErrorMessage,
    setReceivingBoard,
    setGoodsReceipts,
    setLatestGoodsReceipt,
  } = params;

  setIsBusy(true);
  setErrorMessage('');
  try {
    const [board, goodsReceipts] = await Promise.all([
      storeControlPlaneClient.getReceivingBoard(accessToken, tenantId, branchId),
      storeControlPlaneClient.listGoodsReceipts(accessToken, tenantId, branchId),
    ]);
    startTransition(() => {
      setReceivingBoard(board);
      setGoodsReceipts(goodsReceipts.records);
      setLatestGoodsReceipt(latestGoodsReceiptFromList(goodsReceipts.records));
    });
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to load receiving board');
  } finally {
    setIsBusy(false);
  }
}

export async function runSelectReceivingPurchaseOrder(params: {
  accessToken: string;
  tenantId: string;
  branchId: string;
  purchaseOrderId: string;
  setIsBusy: (value: boolean) => void;
  setErrorMessage: SetString;
  setSelectedReceivingPurchaseOrderId: (value: string) => void;
  setSelectedReceivingPurchaseOrder: (value: ControlPlanePurchaseOrder | null) => void;
  setReceivingLineDrafts: (value: StoreReceivingLineDraft[]) => void;
  setGoodsReceiptNote: (value: string) => void;
}) {
  const {
    accessToken,
    tenantId,
    branchId,
    purchaseOrderId,
    setIsBusy,
    setErrorMessage,
    setSelectedReceivingPurchaseOrderId,
    setSelectedReceivingPurchaseOrder,
    setReceivingLineDrafts,
    setGoodsReceiptNote,
  } = params;

  setIsBusy(true);
  setErrorMessage('');
  try {
    const purchaseOrder = await storeControlPlaneClient.getPurchaseOrder(accessToken, tenantId, branchId, purchaseOrderId);
    startTransition(() => {
      setSelectedReceivingPurchaseOrderId(purchaseOrderId);
      setSelectedReceivingPurchaseOrder(purchaseOrder);
      setReceivingLineDrafts(buildReceivingLineDrafts(purchaseOrder));
      setGoodsReceiptNote('');
    });
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to load purchase order detail');
  } finally {
    setIsBusy(false);
  }
}

export async function runCreateGoodsReceipt(params: {
  accessToken: string;
  tenantId: string;
  branchId: string;
  purchaseOrderId: string;
  goodsReceiptNote: string;
  receivingLineDrafts: StoreReceivingLineDraft[];
  setIsBusy: (value: boolean) => void;
  setErrorMessage: SetString;
  setLatestGoodsReceipt: (value: ControlPlaneGoodsReceipt | null) => void;
  setReceivingBoard: (value: ControlPlaneReceivingBoard | null) => void;
  setGoodsReceipts: (value: ControlPlaneGoodsReceiptRecord[]) => void;
  setInventorySnapshot: (value: ControlPlaneInventorySnapshotRecord[]) => void;
  resetReceivingDraft: () => void;
}) {
  const {
    accessToken,
    tenantId,
    branchId,
    purchaseOrderId,
    goodsReceiptNote,
    receivingLineDrafts,
    setIsBusy,
    setErrorMessage,
    setLatestGoodsReceipt,
    setReceivingBoard,
    setGoodsReceipts,
    setInventorySnapshot,
    resetReceivingDraft,
  } = params;

  const parsedLines = receivingLineDrafts.map((line) => {
    const receivedQuantity = Number(line.received_quantity);
    return {
      product_id: line.product_id,
      ordered_quantity: line.ordered_quantity,
      received_quantity: receivedQuantity,
      discrepancy_note: line.discrepancy_note || null,
    };
  });

  if (parsedLines.length === 0) {
    setErrorMessage('Select a purchase order before creating a goods receipt.');
    return;
  }
  if (parsedLines.some((line) => !Number.isFinite(line.received_quantity))) {
    setErrorMessage('All receiving quantities must be numeric.');
    return;
  }
  if (parsedLines.some((line) => line.received_quantity < 0 || line.received_quantity > line.ordered_quantity)) {
    setErrorMessage('Receiving quantities must stay within ordered bounds.');
    return;
  }
  if (!parsedLines.some((line) => line.received_quantity > 0)) {
    setErrorMessage('At least one reviewed receiving line must have a positive quantity.');
    return;
  }

  setIsBusy(true);
  setErrorMessage('');
  try {
    const goodsReceipt = await storeControlPlaneClient.createGoodsReceipt(accessToken, tenantId, branchId, {
      purchase_order_id: purchaseOrderId,
      note: goodsReceiptNote || null,
      lines: parsedLines.map((line) => ({
        product_id: line.product_id,
        received_quantity: line.received_quantity,
        discrepancy_note: line.discrepancy_note,
      })),
    });
    const [board, goodsReceipts, snapshot] = await Promise.all([
      storeControlPlaneClient.getReceivingBoard(accessToken, tenantId, branchId),
      storeControlPlaneClient.listGoodsReceipts(accessToken, tenantId, branchId),
      storeControlPlaneClient.listInventorySnapshot(accessToken, tenantId, branchId),
    ]);
    startTransition(() => {
      setLatestGoodsReceipt(goodsReceipt);
      setReceivingBoard(board);
      setGoodsReceipts(goodsReceipts.records);
      setInventorySnapshot(snapshot.records);
      resetReceivingDraft();
    });
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to create goods receipt');
  } finally {
    setIsBusy(false);
  }
}
