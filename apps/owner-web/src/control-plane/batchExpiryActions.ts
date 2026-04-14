import { startTransition } from 'react';
import type {
  ControlPlaneBatchExpiryReport,
  ControlPlaneBatchExpiryWriteOff,
  ControlPlaneGoodsReceiptBatchLotIntake,
  ControlPlaneGoodsReceiptRecord,
  ControlPlaneInventoryLedgerRecord,
  ControlPlaneInventorySnapshotRecord,
} from '@store/types';
import { ownerControlPlaneClient } from './client';

type SetString = (value: string) => void;

export async function runRecordBatchLotsOnLatestGoodsReceipt(params: {
  accessToken: string;
  tenantId: string;
  branchId: string;
  lotA: { batchNumber: string; quantity: string; expiryDate: string };
  lotB: { batchNumber: string; quantity: string; expiryDate: string };
  productId: string;
  setIsBusy: (value: boolean) => void;
  setErrorMessage: SetString;
  setGoodsReceipts: (value: ControlPlaneGoodsReceiptRecord[]) => void;
  setLatestBatchLotIntake: (value: ControlPlaneGoodsReceiptBatchLotIntake | null) => void;
  setBatchExpiryReport: (value: ControlPlaneBatchExpiryReport | null) => void;
  resetForm: () => void;
}) {
  const {
    accessToken,
    tenantId,
    branchId,
    lotA,
    lotB,
    productId,
    setIsBusy,
    setErrorMessage,
    setGoodsReceipts,
    setLatestBatchLotIntake,
    setBatchExpiryReport,
    resetForm,
  } = params;

  setIsBusy(true);
  setErrorMessage('');
  try {
    const goodsReceiptList = await ownerControlPlaneClient.listGoodsReceipts(accessToken, tenantId, branchId);
    const latestGoodsReceipt = goodsReceiptList.records[goodsReceiptList.records.length - 1];
    if (!latestGoodsReceipt) {
      throw new Error('No goods receipt available for batch intake');
    }

    const intake = await ownerControlPlaneClient.createGoodsReceiptBatchLots(accessToken, tenantId, branchId, latestGoodsReceipt.goods_receipt_id, {
      lots: [
        {
          product_id: productId,
          batch_number: lotA.batchNumber,
          quantity: Number(lotA.quantity),
          expiry_date: lotA.expiryDate,
        },
        {
          product_id: productId,
          batch_number: lotB.batchNumber,
          quantity: Number(lotB.quantity),
          expiry_date: lotB.expiryDate,
        },
      ],
    });
    const report = await ownerControlPlaneClient.getBatchExpiryReport(accessToken, tenantId, branchId);
    startTransition(() => {
      setGoodsReceipts(goodsReceiptList.records);
      setLatestBatchLotIntake(intake);
      setBatchExpiryReport(report);
      resetForm();
    });
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to record batch lots');
  } finally {
    setIsBusy(false);
  }
}

export async function runWriteOffFirstExpiringLot(params: {
  accessToken: string;
  tenantId: string;
  branchId: string;
  quantity: string;
  reason: string;
  batchExpiryReport: ControlPlaneBatchExpiryReport | null;
  setIsBusy: (value: boolean) => void;
  setErrorMessage: SetString;
  setLatestBatchExpiryWriteOff: (value: ControlPlaneBatchExpiryWriteOff | null) => void;
  setBatchExpiryReport: (value: ControlPlaneBatchExpiryReport | null) => void;
  setInventoryLedger: (value: ControlPlaneInventoryLedgerRecord[]) => void;
  setInventorySnapshot: (value: ControlPlaneInventorySnapshotRecord[]) => void;
  resetForm: () => void;
}) {
  const {
    accessToken,
    tenantId,
    branchId,
    quantity,
    reason,
    batchExpiryReport,
    setIsBusy,
    setErrorMessage,
    setLatestBatchExpiryWriteOff,
    setBatchExpiryReport,
    setInventoryLedger,
    setInventorySnapshot,
    resetForm,
  } = params;

  setIsBusy(true);
  setErrorMessage('');
  try {
    const report = batchExpiryReport ?? (await ownerControlPlaneClient.getBatchExpiryReport(accessToken, tenantId, branchId));
    const firstExpiringLot = report.records[0];
    if (!firstExpiringLot) {
      throw new Error('No tracked batch lots available for expiry write-off');
    }

    const writeOff = await ownerControlPlaneClient.createBatchExpiryWriteOff(accessToken, tenantId, branchId, firstExpiringLot.batch_lot_id, {
      quantity: Number(quantity),
      reason,
    });
    const [nextReport, ledger, snapshot] = await Promise.all([
      ownerControlPlaneClient.getBatchExpiryReport(accessToken, tenantId, branchId),
      ownerControlPlaneClient.listInventoryLedger(accessToken, tenantId, branchId),
      ownerControlPlaneClient.listInventorySnapshot(accessToken, tenantId, branchId),
    ]);
    startTransition(() => {
      setLatestBatchExpiryWriteOff(writeOff);
      setBatchExpiryReport(nextReport);
      setInventoryLedger(ledger.records);
      setInventorySnapshot(snapshot.records);
      resetForm();
    });
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to write off expiring batch lot');
  } finally {
    setIsBusy(false);
  }
}

export async function runLoadBatchExpiryReport(params: {
  accessToken: string;
  tenantId: string;
  branchId: string;
  setIsBusy: (value: boolean) => void;
  setErrorMessage: SetString;
  setBatchExpiryReport: (value: ControlPlaneBatchExpiryReport | null) => void;
}) {
  const { accessToken, tenantId, branchId, setIsBusy, setErrorMessage, setBatchExpiryReport } = params;

  setIsBusy(true);
  setErrorMessage('');
  try {
    const report = await ownerControlPlaneClient.getBatchExpiryReport(accessToken, tenantId, branchId);
    startTransition(() => {
      setBatchExpiryReport(report);
    });
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to load batch expiry report');
  } finally {
    setIsBusy(false);
  }
}
