import { startTransition, useState } from 'react';
import { ActionButton, DetailList, SectionCard } from '@store/ui';
import type { ControlPlaneSyncConflictRecord, ControlPlaneSyncEnvelopeRecord, ControlPlaneSyncStatus } from '@store/types';
import { storeControlPlaneClient } from './client';

type StoreSyncRuntimeSectionProps = {
  accessToken: string;
  tenantId: string;
  branchId: string;
};

export function StoreSyncRuntimeSection({ accessToken, tenantId, branchId }: StoreSyncRuntimeSectionProps) {
  const [syncStatus, setSyncStatus] = useState<ControlPlaneSyncStatus | null>(null);
  const [conflicts, setConflicts] = useState<ControlPlaneSyncConflictRecord[]>([]);
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
      const [statusResponse, conflictResponse, envelopeResponse] = await Promise.all([
        storeControlPlaneClient.getRuntimeSyncStatus(accessToken, tenantId, branchId),
        storeControlPlaneClient.listRuntimeSyncConflicts(accessToken, tenantId, branchId),
        storeControlPlaneClient.listRuntimeSyncEnvelopes(accessToken, tenantId, branchId),
      ]);
      startTransition(() => {
        setSyncStatus(statusResponse);
        setConflicts(conflictResponse.records);
        setEnvelopes(envelopeResponse.records);
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to load sync monitoring');
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <SectionCard eyebrow="Runtime sync" title="Hub sync monitoring">
      <p style={{ margin: 0, color: '#4e5871' }}>Read-only branch runtime posture for staff sessions.</p>

      <div style={{ height: '16px' }} />

      <ActionButton onClick={() => void loadSyncMonitoring()} disabled={isBusy || !accessToken || !tenantId || !branchId}>
        Load sync monitoring
      </ActionButton>

      {syncStatus ? (
        <div style={{ marginTop: '16px' }}>
          <DetailList
            items={[
              { label: 'Hub device', value: syncStatus.source_device_id ?? syncStatus.hub_device_id ?? 'Unbound' },
              { label: 'Runtime state', value: syncStatus.runtime_state },
              { label: 'Branch cursor', value: String(syncStatus.branch_cursor) },
              { label: 'Last pull cursor', value: String(syncStatus.last_pull_cursor) },
              { label: 'Open conflicts', value: String(syncStatus.open_conflict_count) },
              { label: 'Connected spokes', value: String(syncStatus.connected_spoke_count) },
              { label: 'Pending mutations', value: String(syncStatus.pending_mutation_count) },
              { label: 'Local outbox depth', value: String(syncStatus.local_outbox_depth) },
            ]}
          />
        </div>
      ) : null}

      {conflicts.length ? (
        <ul style={{ marginBottom: '16px', marginTop: '16px', color: '#4e5871', lineHeight: 1.7 }}>
          {conflicts.map((record) => (
            <li key={record.id}>
              {record.table_name} :: {record.record_id} :: {record.reason}
            </li>
          ))}
        </ul>
      ) : null}

      {envelopes.length ? (
        <ul style={{ marginBottom: 0, marginTop: '16px', color: '#4e5871', lineHeight: 1.7 }}>
          {envelopes.map((record) => (
            <li key={record.id}>
              {record.entity_type} :: {record.status}
            </li>
          ))}
        </ul>
      ) : null}

      {errorMessage ? <p style={{ color: '#9d2b19', marginBottom: 0 }}>{errorMessage}</p> : null}
    </SectionCard>
  );
}
