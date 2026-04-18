import { startTransition } from 'react';
import type {
  ControlPlaneBatchExpiryReport,
  ControlPlaneReceivingBoard,
  ControlPlaneReplenishmentBoard,
  ControlPlaneRestockBoard,
  ControlPlaneStockCountBoard,
} from '@store/types';
import { storeControlPlaneClient } from './client';

export type StoreBranchOperationsDashboardSnapshot = {
  replenishmentBoard: ControlPlaneReplenishmentBoard;
  restockBoard: ControlPlaneRestockBoard;
  receivingBoard: ControlPlaneReceivingBoard;
  stockCountBoard: ControlPlaneStockCountBoard;
  batchExpiryReport: ControlPlaneBatchExpiryReport;
};

export async function runLoadBranchOperationsDashboard(params: {
  accessToken: string;
  tenantId: string;
  branchId: string;
  setIsBusy: (value: boolean) => void;
  setErrorMessage: (value: string) => void;
  setSnapshot: (value: StoreBranchOperationsDashboardSnapshot | null) => void;
}) {
  const {
    accessToken,
    tenantId,
    branchId,
    setIsBusy,
    setErrorMessage,
    setSnapshot,
  } = params;

  setIsBusy(true);
  setErrorMessage('');
  try {
    const [
      replenishmentBoard,
      restockBoard,
      receivingBoard,
      stockCountBoard,
      batchExpiryReport,
    ] = await Promise.all([
      storeControlPlaneClient.getReplenishmentBoard(accessToken, tenantId, branchId),
      storeControlPlaneClient.getRestockBoard(accessToken, tenantId, branchId),
      storeControlPlaneClient.getReceivingBoard(accessToken, tenantId, branchId),
      storeControlPlaneClient.getStockCountBoard(accessToken, tenantId, branchId),
      storeControlPlaneClient.getBatchExpiryReport(accessToken, tenantId, branchId),
    ]);
    startTransition(() => {
      setSnapshot({
        replenishmentBoard,
        restockBoard,
        receivingBoard,
        stockCountBoard,
        batchExpiryReport,
      });
    });
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to load branch operations dashboard');
  } finally {
    setIsBusy(false);
  }
}
