import { useState } from 'react';
import type {
  ControlPlaneSyncConflictRecord,
  ControlPlaneSyncEnvelopeRecord,
  ControlPlaneSyncSpokeRecord,
  ControlPlaneSyncStatus,
} from '@store/types';
import { storeControlPlaneClient } from './client';

type UseStoreRuntimeSyncMonitoringArgs = {
  accessToken: string;
  tenantId: string;
  branchId: string;
};

export function useStoreRuntimeSyncMonitoring({
  accessToken,
  tenantId,
  branchId,
}: UseStoreRuntimeSyncMonitoringArgs) {
  const [syncStatus, setSyncStatus] = useState<ControlPlaneSyncStatus | null>(null);
  const [conflicts, setConflicts] = useState<ControlPlaneSyncConflictRecord[]>([]);
  const [spokes, setSpokes] = useState<ControlPlaneSyncSpokeRecord[]>([]);
  const [envelopes, setEnvelopes] = useState<ControlPlaneSyncEnvelopeRecord[]>([]);
  const [errorMessage, setErrorMessage] = useState('');
  const [isBusy, setIsBusy] = useState(false);

  async function loadSyncMonitoring() {
    if (!accessToken || !tenantId || !branchId) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const [statusResponse, conflictResponse, spokeResponse, envelopeResponse] = await Promise.all([
        storeControlPlaneClient.getRuntimeSyncStatus(accessToken, tenantId, branchId),
        storeControlPlaneClient.listRuntimeSyncConflicts(accessToken, tenantId, branchId),
        storeControlPlaneClient.listRuntimeSyncSpokes(accessToken, tenantId, branchId),
        storeControlPlaneClient.listRuntimeSyncEnvelopes(accessToken, tenantId, branchId),
      ]);
      setSyncStatus(statusResponse);
      setConflicts(Array.isArray(conflictResponse.records) ? conflictResponse.records : []);
      setSpokes(Array.isArray(spokeResponse.records) ? spokeResponse.records : []);
      setEnvelopes(Array.isArray(envelopeResponse.records) ? envelopeResponse.records : []);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to load sync monitoring');
    } finally {
      setIsBusy(false);
    }
  }

  return {
    conflicts,
    envelopes,
    errorMessage,
    isBusy,
    loadSyncMonitoring,
    spokes,
    syncStatus,
  };
}
