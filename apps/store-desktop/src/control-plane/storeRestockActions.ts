import { startTransition } from 'react';
import type { ControlPlaneReplenishmentBoard, ControlPlaneRestockBoard, ControlPlaneRestockTask } from '@store/types';
import { storeControlPlaneClient } from './client';

type SetString = (value: string) => void;

export async function runLoadRestockBoard(params: {
  accessToken: string;
  tenantId: string;
  branchId: string;
  setIsBusy: (value: boolean) => void;
  setErrorMessage: SetString;
  setRestockBoard: (value: ControlPlaneRestockBoard | null) => void;
  setReplenishmentBoard: (value: ControlPlaneReplenishmentBoard | null) => void;
}) {
  const {
    accessToken,
    tenantId,
    branchId,
    setIsBusy,
    setErrorMessage,
    setRestockBoard,
    setReplenishmentBoard,
  } = params;

  setIsBusy(true);
  setErrorMessage('');
  try {
    const [board, replenishmentBoard] = await Promise.all([
      storeControlPlaneClient.getRestockBoard(accessToken, tenantId, branchId),
      storeControlPlaneClient.getReplenishmentBoard(accessToken, tenantId, branchId),
    ]);
    startTransition(() => {
      setRestockBoard(board);
      setReplenishmentBoard(replenishmentBoard);
    });
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to load restock board');
  } finally {
    setIsBusy(false);
  }
}

export async function runCreateRestockTask(params: {
  accessToken: string;
  tenantId: string;
  branchId: string;
  productId: string;
  requestedQuantity: number;
  sourcePosture: string;
  note: string;
  setIsBusy: (value: boolean) => void;
  setErrorMessage: SetString;
  setLatestRestockTask: (value: ControlPlaneRestockTask | null) => void;
  setRestockBoard: (value: ControlPlaneRestockBoard | null) => void;
  resetForm: () => void;
}) {
  const {
    accessToken,
    tenantId,
    branchId,
    productId,
    requestedQuantity,
    sourcePosture,
    note,
    setIsBusy,
    setErrorMessage,
    setLatestRestockTask,
    setRestockBoard,
    resetForm,
  } = params;

  setIsBusy(true);
  setErrorMessage('');
  try {
    const task = await storeControlPlaneClient.createRestockTask(accessToken, tenantId, branchId, {
      product_id: productId,
      requested_quantity: requestedQuantity,
      source_posture: sourcePosture,
      note: note || null,
    });
    const board = await storeControlPlaneClient.getRestockBoard(accessToken, tenantId, branchId);
    startTransition(() => {
      setLatestRestockTask(task);
      setRestockBoard(board);
      resetForm();
    });
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to create restock task');
  } finally {
    setIsBusy(false);
  }
}

export async function runPickRestockTask(params: {
  accessToken: string;
  tenantId: string;
  branchId: string;
  restockTaskId: string;
  pickedQuantity: number;
  note: string;
  setIsBusy: (value: boolean) => void;
  setErrorMessage: SetString;
  setLatestRestockTask: (value: ControlPlaneRestockTask | null) => void;
  setRestockBoard: (value: ControlPlaneRestockBoard | null) => void;
  resetForm: () => void;
}) {
  const {
    accessToken,
    tenantId,
    branchId,
    restockTaskId,
    pickedQuantity,
    note,
    setIsBusy,
    setErrorMessage,
    setLatestRestockTask,
    setRestockBoard,
    resetForm,
  } = params;

  setIsBusy(true);
  setErrorMessage('');
  try {
    const task = await storeControlPlaneClient.pickRestockTask(accessToken, tenantId, branchId, restockTaskId, {
      picked_quantity: pickedQuantity,
      note: note || null,
    });
    const board = await storeControlPlaneClient.getRestockBoard(accessToken, tenantId, branchId);
    startTransition(() => {
      setLatestRestockTask(task);
      setRestockBoard(board);
      resetForm();
    });
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to mark restock task picked');
  } finally {
    setIsBusy(false);
  }
}

export async function runCompleteRestockTask(params: {
  accessToken: string;
  tenantId: string;
  branchId: string;
  restockTaskId: string;
  completionNote: string;
  setIsBusy: (value: boolean) => void;
  setErrorMessage: SetString;
  setLatestRestockTask: (value: ControlPlaneRestockTask | null) => void;
  setRestockBoard: (value: ControlPlaneRestockBoard | null) => void;
  resetForm: () => void;
}) {
  const {
    accessToken,
    tenantId,
    branchId,
    restockTaskId,
    completionNote,
    setIsBusy,
    setErrorMessage,
    setLatestRestockTask,
    setRestockBoard,
    resetForm,
  } = params;

  setIsBusy(true);
  setErrorMessage('');
  try {
    const task = await storeControlPlaneClient.completeRestockTask(accessToken, tenantId, branchId, restockTaskId, {
      completion_note: completionNote || null,
    });
    const board = await storeControlPlaneClient.getRestockBoard(accessToken, tenantId, branchId);
    startTransition(() => {
      setLatestRestockTask(task);
      setRestockBoard(board);
      resetForm();
    });
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to complete restock task');
  } finally {
    setIsBusy(false);
  }
}

export async function runCancelRestockTask(params: {
  accessToken: string;
  tenantId: string;
  branchId: string;
  restockTaskId: string;
  cancelNote: string;
  setIsBusy: (value: boolean) => void;
  setErrorMessage: SetString;
  setLatestRestockTask: (value: ControlPlaneRestockTask | null) => void;
  setRestockBoard: (value: ControlPlaneRestockBoard | null) => void;
  resetForm: () => void;
}) {
  const {
    accessToken,
    tenantId,
    branchId,
    restockTaskId,
    cancelNote,
    setIsBusy,
    setErrorMessage,
    setLatestRestockTask,
    setRestockBoard,
    resetForm,
  } = params;

  setIsBusy(true);
  setErrorMessage('');
  try {
    const task = await storeControlPlaneClient.cancelRestockTask(accessToken, tenantId, branchId, restockTaskId, {
      cancel_note: cancelNote || null,
    });
    const board = await storeControlPlaneClient.getRestockBoard(accessToken, tenantId, branchId);
    startTransition(() => {
      setLatestRestockTask(task);
      setRestockBoard(board);
      resetForm();
    });
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to cancel restock task');
  } finally {
    setIsBusy(false);
  }
}
