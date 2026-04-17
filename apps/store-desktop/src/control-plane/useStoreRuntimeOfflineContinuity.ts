import { useEffect, useRef, useState } from 'react';
import type {
  ControlPlaneActor,
  ControlPlaneBranchCatalogItem,
  ControlPlaneBranchRecord,
  ControlPlaneDeviceRecord,
  ControlPlaneInventorySnapshotRecord,
  ControlPlaneOfflineSaleReplayRequest,
  ControlPlaneSaleRecord,
} from '@store/types';
import { storeControlPlaneClient } from './client';
import { shouldQueueRuntimeOutboxMutation } from './runtimeOutbox';
import type { StoreRuntimeHubIdentityRecord } from './storeRuntimeHubIdentityStore';
import {
  createResolvedStoreRuntimeContinuityStore,
  type StoreRuntimeContinuityAdapter,
  type StoreRuntimeContinuityPersistence,
  type StoreRuntimeContinuitySnapshot,
  type StoreRuntimeOfflineConflictRecord,
  type StoreRuntimeOfflineSaleRecord,
} from './storeRuntimeContinuityStore';
import { isOfflineSaleContinuityReady, prepareOfflineSaleContinuityDraft } from './storeRuntimeContinuityPolicy';

type UseStoreRuntimeOfflineContinuityArgs = {
  accessToken: string;
  tenantId: string;
  branchId: string;
  actor: ControlPlaneActor | null;
  branches: ControlPlaneBranchRecord[];
  branchCatalogItems: ControlPlaneBranchCatalogItem[];
  inventorySnapshot: ControlPlaneInventorySnapshotRecord[];
  runtimeDevices: ControlPlaneDeviceRecord[];
  selectedRuntimeDeviceId: string;
  hubIdentityRecord: StoreRuntimeHubIdentityRecord | null;
  onInventorySnapshotChange(nextInventorySnapshot: ControlPlaneInventorySnapshotRecord[]): void;
  onSalesChange(nextSales: ControlPlaneSaleRecord[]): void;
};

type CreateOfflineSaleArgs = {
  cashierSessionId: string;
  customerName: string;
  customerGstin?: string | null;
  paymentMethod: string;
  lineInputs: Array<{ product_id: string; quantity: number }>;
};

type ReplayOfflineSalesResult = {
  acceptedCount: number;
  conflictCount: number;
};

function buildDefaultPersistence(): StoreRuntimeContinuityPersistence {
  return {
    authority: 'BRANCH_HUB_CONTINUITY',
    backend_kind: 'browser_storage',
    backend_label: 'Branch continuity storage',
    cached_at: null,
    detail: null,
    location: null,
    snapshot_present: false,
  };
}

function resolveRuntimeProfile(device: ControlPlaneDeviceRecord | null): string | null {
  if (!device) {
    return null;
  }
  if (device.runtime_profile) {
    return device.runtime_profile;
  }
  return device.is_branch_hub ? 'branch_hub' : 'desktop_spoke';
}

function hasOpenOfflineSales(snapshot: StoreRuntimeContinuitySnapshot | null) {
  return Boolean(
    snapshot?.offline_sales.some((sale) => sale.reconciliation_state !== 'RECONCILED' && sale.reconciliation_state !== 'REJECTED'),
  );
}

function buildSeedSnapshot(args: {
  tenantId: string;
  branchId: string;
  branchCode: string;
  hubDeviceId: string;
  inventorySnapshot: ControlPlaneInventorySnapshotRecord[];
}): StoreRuntimeContinuitySnapshot {
  return {
    schema_version: 1,
    authority: 'BRANCH_HUB_CONTINUITY',
    cached_at: new Date().toISOString(),
    tenant_id: args.tenantId,
    branch_id: args.branchId,
    branch_code: args.branchCode,
    hub_device_id: args.hubDeviceId,
    next_continuity_invoice_sequence: 1,
    inventory_snapshot: args.inventorySnapshot,
    offline_sales: [],
    conflicts: [],
    last_reconciled_at: null,
  };
}

function isSameScope(
  snapshot: StoreRuntimeContinuitySnapshot | null,
  scope: {
    tenantId: string;
    branchId: string;
    branchCode: string;
    hubDeviceId: string;
  },
) {
  return snapshot !== null
    && snapshot.tenant_id === scope.tenantId
    && snapshot.branch_id === scope.branchId
    && snapshot.branch_code === scope.branchCode
    && snapshot.hub_device_id === scope.hubDeviceId;
}

function inventoryMatches(
  currentSnapshot: StoreRuntimeContinuitySnapshot | null,
  nextInventorySnapshot: ControlPlaneInventorySnapshotRecord[],
) {
  if (currentSnapshot === null) {
    return false;
  }
  return JSON.stringify(currentSnapshot.inventory_snapshot) === JSON.stringify(nextInventorySnapshot);
}

function serializeReplayPayload(sale: StoreRuntimeOfflineSaleRecord): ControlPlaneOfflineSaleReplayRequest {
  return {
    continuity_sale_id: sale.continuity_sale_id,
    continuity_invoice_number: sale.continuity_invoice_number,
    idempotency_key: sale.idempotency_key,
    issued_offline_at: sale.issued_offline_at,
    cashier_session_id: sale.cashier_session_id ?? null,
    staff_actor_id: sale.staff_actor_id,
    customer_name: sale.customer_name,
    customer_gstin: sale.customer_gstin ?? null,
    payment_method: sale.payment_method,
    subtotal: sale.subtotal,
    cgst_total: sale.cgst_total,
    sgst_total: sale.sgst_total,
    igst_total: sale.igst_total,
    grand_total: sale.grand_total,
    lines: sale.lines.map((line) => ({
      product_id: line.product_id,
      quantity: line.quantity,
    })),
  };
}

function describeReplayFailure(error: unknown) {
  if (error instanceof Error) {
    return error.message;
  }
  return 'Unable to replay offline sales right now.';
}

export function useStoreRuntimeOfflineContinuity({
  accessToken,
  tenantId,
  branchId,
  actor,
  branches,
  branchCatalogItems,
  inventorySnapshot,
  runtimeDevices,
  selectedRuntimeDeviceId,
  hubIdentityRecord,
  onInventorySnapshotChange,
  onSalesChange,
}: UseStoreRuntimeOfflineContinuityArgs) {
  const continuityStoreRef = useRef<StoreRuntimeContinuityAdapter | null>(null);
  if (continuityStoreRef.current === null) {
    continuityStoreRef.current = createResolvedStoreRuntimeContinuityStore();
  }

  const [continuitySnapshot, setContinuitySnapshot] = useState<StoreRuntimeContinuitySnapshot | null>(null);
  const [continuityPersistence, setContinuityPersistence] = useState<StoreRuntimeContinuityPersistence>(buildDefaultPersistence());
  const [hasLoadedContinuity, setHasLoadedContinuity] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');

  const selectedBranch = branches.find((branch) => branch.branch_id === branchId) ?? branches[0] ?? null;
  const selectedRuntimeDevice = runtimeDevices.find((device) => device.id === selectedRuntimeDeviceId) ?? runtimeDevices[0] ?? null;
  const runtimeProfile = resolveRuntimeProfile(selectedRuntimeDevice);
  const staffActorId = actor?.user_id ?? '';
  const continuityReady = isOfflineSaleContinuityReady({
    runtimeProfile,
    branchCode: selectedBranch?.code ?? null,
    branchGstin: selectedBranch?.gstin ?? null,
    hubDeviceId: hubIdentityRecord?.device_id ?? selectedRuntimeDevice?.id ?? null,
    staffActorId,
    branchCatalogItems,
    inventorySnapshot,
  });

  async function persistSnapshot(nextSnapshot: StoreRuntimeContinuitySnapshot) {
    const persistence = await continuityStoreRef.current!.save(nextSnapshot);
    setContinuitySnapshot(nextSnapshot);
    setContinuityPersistence(persistence);
    return nextSnapshot;
  }

  useEffect(() => {
    let isCancelled = false;

    void (async () => {
      try {
        const [loadedSnapshot, persistence] = await Promise.all([
          continuityStoreRef.current!.load(),
          continuityStoreRef.current!.getPersistence(),
        ]);
        if (isCancelled) {
          return;
        }
        setContinuitySnapshot(loadedSnapshot);
        setContinuityPersistence(persistence);
      } catch {
        if (isCancelled) {
          return;
        }
        setContinuitySnapshot(null);
        setContinuityPersistence(buildDefaultPersistence());
      } finally {
        if (!isCancelled) {
          setHasLoadedContinuity(true);
        }
      }
    })();

    return () => {
      isCancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!hasLoadedContinuity || !continuityReady || !selectedBranch || !selectedRuntimeDevice) {
      return;
    }
    const scope = {
      tenantId,
      branchId,
      branchCode: selectedBranch.code,
      hubDeviceId: hubIdentityRecord?.device_id ?? selectedRuntimeDevice.id,
    };
    const scopeMatches = isSameScope(continuitySnapshot, scope);
    const shouldReseedInventory = scopeMatches
      && !hasOpenOfflineSales(continuitySnapshot)
      && inventorySnapshot.length > 0
      && !inventoryMatches(continuitySnapshot, inventorySnapshot);
    if (scopeMatches && !shouldReseedInventory) {
      return;
    }

    const nextSnapshot = scopeMatches && continuitySnapshot
      ? {
          ...continuitySnapshot,
          cached_at: new Date().toISOString(),
          inventory_snapshot: inventorySnapshot,
          branch_code: selectedBranch.code,
          hub_device_id: scope.hubDeviceId,
        }
      : buildSeedSnapshot({
          tenantId,
          branchId,
          branchCode: selectedBranch.code,
          hubDeviceId: scope.hubDeviceId,
          inventorySnapshot,
        });

    void persistSnapshot(nextSnapshot);
  }, [
    branchId,
    continuityReady,
    continuitySnapshot,
    hasLoadedContinuity,
    hubIdentityRecord?.device_id,
    inventorySnapshot,
    selectedBranch,
    selectedRuntimeDevice,
    tenantId,
  ]);

  useEffect(() => {
    if (!hasLoadedContinuity || !continuityReady || !hasOpenOfflineSales(continuitySnapshot)) {
      return;
    }
    const activeContinuitySnapshot = continuitySnapshot;
    if (!activeContinuitySnapshot || inventoryMatches(activeContinuitySnapshot, inventorySnapshot)) {
      return;
    }
    onInventorySnapshotChange(activeContinuitySnapshot.inventory_snapshot);
  }, [
    continuityReady,
    continuitySnapshot,
    hasLoadedContinuity,
    inventorySnapshot,
    onInventorySnapshotChange,
  ]);

  async function createOfflineSale(args: CreateOfflineSaleArgs) {
    if (!continuityReady || !selectedBranch) {
      throw new Error('Offline continuity is not ready on this runtime.');
    }
    const baseSnapshot = continuitySnapshot ?? buildSeedSnapshot({
      tenantId,
      branchId,
      branchCode: selectedBranch.code,
      hubDeviceId: hubIdentityRecord?.device_id ?? selectedRuntimeDevice?.id ?? '',
      inventorySnapshot,
    });
    const nextDraft = prepareOfflineSaleContinuityDraft({
      tenantId,
      branchId,
      branchCode: selectedBranch.code,
      cashierSessionId: args.cashierSessionId,
      hubDeviceId: hubIdentityRecord?.device_id ?? selectedRuntimeDevice?.id ?? '',
      staffActorId,
      branchGstin: selectedBranch.gstin ?? null,
      customerName: args.customerName,
      customerGstin: args.customerGstin ?? null,
      paymentMethod: args.paymentMethod,
      lineInputs: args.lineInputs,
      branchCatalogItems,
      inventorySnapshot: baseSnapshot.inventory_snapshot,
      nextContinuityInvoiceSequence: baseSnapshot.next_continuity_invoice_sequence,
      issuedAt: new Date().toISOString(),
    });
    const nextSnapshot: StoreRuntimeContinuitySnapshot = {
      ...baseSnapshot,
      cached_at: new Date().toISOString(),
      inventory_snapshot: nextDraft.updatedInventory,
      next_continuity_invoice_sequence: nextDraft.nextContinuityInvoiceSequence,
      offline_sales: [...baseSnapshot.offline_sales, nextDraft.sale],
    };
    await persistSnapshot(nextSnapshot);
    onInventorySnapshotChange(nextDraft.updatedInventory);
    setStatusMessage('Cloud unavailable. Branch continuity mode is active.');
    return nextDraft.sale;
  }

  async function replayOfflineSales(): Promise<ReplayOfflineSalesResult> {
    if (!continuitySnapshot || !hubIdentityRecord) {
      throw new Error('Branch hub identity is required before offline sales can be replayed.');
    }

    const replayableSales = continuitySnapshot.offline_sales.filter((sale) => sale.reconciliation_state === 'PENDING_REPLAY');
    if (replayableSales.length === 0) {
      return { acceptedCount: 0, conflictCount: 0 };
    }

    let acceptedCount = 0;
    let conflictCount = 0;
    const conflictRecords = [...continuitySnapshot.conflicts];
    const replayingSnapshot: StoreRuntimeContinuitySnapshot = {
      ...continuitySnapshot,
      cached_at: new Date().toISOString(),
      offline_sales: continuitySnapshot.offline_sales.map((sale) => (
        sale.reconciliation_state === 'PENDING_REPLAY'
          ? { ...sale, reconciliation_state: 'REPLAYING', replay_error: null }
          : sale
      )),
    };
    await persistSnapshot(replayingSnapshot);

    let workingSnapshot = replayingSnapshot;
    for (const sale of replayableSales) {
      try {
        const response = await storeControlPlaneClient.replayOfflineSale(
          hubIdentityRecord.device_id,
          hubIdentityRecord.sync_access_secret,
          serializeReplayPayload(sale),
        );
        if (response.result === 'accepted') {
          acceptedCount += 1;
          workingSnapshot = {
            ...workingSnapshot,
            cached_at: new Date().toISOString(),
            last_reconciled_at: new Date().toISOString(),
            offline_sales: workingSnapshot.offline_sales.map((currentSale) => (
              currentSale.continuity_sale_id === sale.continuity_sale_id
                ? {
                    ...currentSale,
                    reconciliation_state: 'RECONCILED',
                    replayed_sale_id: response.sale_id ?? null,
                    replayed_invoice_number: response.invoice_number ?? null,
                    replay_error: null,
                  }
                : currentSale
            )),
          };
          continue;
        }

        conflictCount += 1;
        const conflictRecord: StoreRuntimeOfflineConflictRecord = {
          continuity_sale_id: sale.continuity_sale_id,
          reason: 'REPLAY_CONFLICT',
          message: response.message ?? 'Offline sale replay needs operator review.',
          recorded_at: new Date().toISOString(),
        };
        const existingConflictIndex = conflictRecords.findIndex(
          (record) => record.continuity_sale_id === sale.continuity_sale_id,
        );
        if (existingConflictIndex >= 0) {
          conflictRecords.splice(existingConflictIndex, 1, conflictRecord);
        } else {
          conflictRecords.push(conflictRecord);
        }
        workingSnapshot = {
          ...workingSnapshot,
          cached_at: new Date().toISOString(),
          conflicts: [...conflictRecords],
          offline_sales: workingSnapshot.offline_sales.map((currentSale) => (
            currentSale.continuity_sale_id === sale.continuity_sale_id
              ? {
                  ...currentSale,
                  reconciliation_state: 'CONFLICT',
                  replay_error: response.message ?? 'Offline sale replay needs operator review.',
                }
              : currentSale
          )),
        };
      } catch (error) {
        workingSnapshot = {
          ...workingSnapshot,
          cached_at: new Date().toISOString(),
          offline_sales: workingSnapshot.offline_sales.map((currentSale) => (
            currentSale.continuity_sale_id === sale.continuity_sale_id
              ? {
                  ...currentSale,
                  reconciliation_state: 'PENDING_REPLAY',
                  replay_error: describeReplayFailure(error),
                }
              : currentSale
          )),
        };
        if (shouldQueueRuntimeOutboxMutation(error)) {
          setStatusMessage('Cloud unavailable. Branch continuity mode is active.');
          await persistSnapshot(workingSnapshot);
          return { acceptedCount, conflictCount };
        }
        throw error;
      }
    }

    await persistSnapshot(workingSnapshot);

    if (acceptedCount > 0 && accessToken && tenantId && branchId) {
      try {
        const [salesResponse, inventoryResponse] = await Promise.all([
          storeControlPlaneClient.listSales(accessToken, tenantId, branchId),
          storeControlPlaneClient.listInventorySnapshot(accessToken, tenantId, branchId),
        ]);
        onSalesChange(salesResponse.records);
        onInventorySnapshotChange(inventoryResponse.records);
      } catch {
        // Keep the reconciled local state even if the read-after-write refresh fails.
      }
    }

    if (conflictCount > 0) {
      setStatusMessage('Some offline sales require operator review before they can be reconciled.');
    } else if (workingSnapshot.offline_sales.some((sale) => sale.reconciliation_state === 'PENDING_REPLAY')) {
      setStatusMessage('Offline sales are still pending reconciliation.');
    } else if (acceptedCount > 0) {
      setStatusMessage('Offline sales reconciled with the control plane.');
    } else {
      setStatusMessage('');
    }

    return { acceptedCount, conflictCount };
  }

  return {
    continuityPersistence,
    continuitySnapshot,
    createOfflineSale,
    hasLoadedContinuity,
    hasPendingOfflineSales: continuitySnapshot?.offline_sales.some((sale) => sale.reconciliation_state === 'PENDING_REPLAY') ?? false,
    isContinuityModeActive: continuitySnapshot?.offline_sales.some((sale) => sale.reconciliation_state === 'PENDING_REPLAY') ?? false,
    isReady: continuityReady,
    latestOfflineSale: continuitySnapshot?.offline_sales.at(-1) ?? null,
    offlineConflictCount: continuitySnapshot?.conflicts.length ?? 0,
    offlineConflicts: continuitySnapshot?.conflicts ?? [],
    offlineSales: continuitySnapshot?.offline_sales ?? [],
    pendingOfflineSaleCount: continuitySnapshot?.offline_sales.filter((sale) => sale.reconciliation_state === 'PENDING_REPLAY').length ?? 0,
    replayOfflineSales,
    statusMessage,
  };
}
