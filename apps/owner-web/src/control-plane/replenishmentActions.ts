import { startTransition } from 'react';
import type { ControlPlaneBranchCatalogItem, ControlPlaneReplenishmentBoard } from '@store/types';
import { ownerControlPlaneClient } from './client';

type SetString = (value: string) => void;

export async function runLoadReplenishmentBoard(params: {
  accessToken: string;
  tenantId: string;
  branchId: string;
  setIsBusy: (value: boolean) => void;
  setErrorMessage: SetString;
  setReplenishmentBoard: (value: ControlPlaneReplenishmentBoard | null) => void;
}) {
  const { accessToken, tenantId, branchId, setIsBusy, setErrorMessage, setReplenishmentBoard } = params;

  setIsBusy(true);
  setErrorMessage('');
  try {
    const board = await ownerControlPlaneClient.getReplenishmentBoard(accessToken, tenantId, branchId);
    startTransition(() => {
      setReplenishmentBoard(board);
    });
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to load replenishment board');
  } finally {
    setIsBusy(false);
  }
}

export async function runUpdateFirstBranchReplenishmentPolicy(params: {
  accessToken: string;
  tenantId: string;
  branchId: string;
  branchCatalogItem: ControlPlaneBranchCatalogItem;
  reorderPoint: string;
  targetStock: string;
  setIsBusy: (value: boolean) => void;
  setErrorMessage: SetString;
  setLatestBranchCatalogItem: (value: ControlPlaneBranchCatalogItem | null) => void;
  setReplenishmentBoard: (value: ControlPlaneReplenishmentBoard | null) => void;
}) {
  const {
    accessToken,
    tenantId,
    branchId,
    branchCatalogItem,
    reorderPoint,
    targetStock,
    setIsBusy,
    setErrorMessage,
    setLatestBranchCatalogItem,
    setReplenishmentBoard,
  } = params;

  setIsBusy(true);
  setErrorMessage('');
  try {
    const item = await ownerControlPlaneClient.upsertBranchCatalogItem(accessToken, tenantId, branchId, {
      product_id: branchCatalogItem.product_id,
      selling_price_override: branchCatalogItem.selling_price_override ?? null,
      availability_status: branchCatalogItem.availability_status,
      reorder_point: Number(reorderPoint),
      target_stock: Number(targetStock),
    });
    const board = await ownerControlPlaneClient.getReplenishmentBoard(accessToken, tenantId, branchId);
    startTransition(() => {
      setLatestBranchCatalogItem(item);
      setReplenishmentBoard(board);
    });
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to update replenishment policy');
  } finally {
    setIsBusy(false);
  }
}
