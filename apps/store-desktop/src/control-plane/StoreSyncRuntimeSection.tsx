import { ActionButton, DetailList, SectionCard } from '@store/ui';
import { useStoreRuntimeSpokePairing } from './useStoreRuntimeSpokePairing';
import { useStoreRuntimeSyncMonitoring } from './useStoreRuntimeSyncMonitoring';

type StoreSyncRuntimeSectionProps = {
  accessToken: string;
  tenantId: string;
  branchId: string;
  runtimeHubServiceUrl: string | null;
  runtimeHubManifestUrl: string | null;
};

export function StoreSyncRuntimeSection({
  accessToken,
  tenantId,
  branchId,
  runtimeHubServiceUrl,
  runtimeHubManifestUrl,
}: StoreSyncRuntimeSectionProps) {
  const syncMonitoring = useStoreRuntimeSyncMonitoring({
    accessToken,
    tenantId,
    branchId,
  });
  const spokePairing = useStoreRuntimeSpokePairing({
    isEnabled: Boolean(accessToken),
    runtimeHubManifestUrl,
    runtimeHubServiceUrl,
  });
  const conflicts = syncMonitoring.conflicts ?? [];
  const spokes = syncMonitoring.spokes ?? [];
  const envelopes = syncMonitoring.envelopes ?? [];

  return (
    <SectionCard eyebrow="Runtime sync" title="Hub sync monitoring">
      <p style={{ margin: 0, color: '#4e5871' }}>Read-only branch runtime posture for staff sessions.</p>

      {spokePairing.manifest ? (
        <div style={{ marginTop: '16px' }}>
          <h3 style={{ marginTop: 0, marginBottom: '12px' }}>Prepare spoke activation</h3>
          <DetailList
            items={[
              { label: 'Hub device', value: spokePairing.manifest.hub_device_code },
              { label: 'Pairing modes', value: spokePairing.manifest.pairing_modes.join(', ') },
              { label: 'Supported spoke roles', value: spokePairing.manifest.supported_runtime_profiles.join(', ') },
            ]}
          />
          <ActionButton
            onClick={() => void spokePairing.prepareDesktopSpokeActivation()}
            disabled={spokePairing.isBusy || !runtimeHubServiceUrl}
          >
            Prepare spoke activation
          </ActionButton>
        </div>
      ) : null}

      {spokePairing.spokeActivation ? (
        <div style={{ marginTop: '16px' }}>
          <DetailList
            items={[
              { label: 'Activation code', value: spokePairing.spokeActivation.activation_code },
              { label: 'Runtime role', value: spokePairing.spokeActivation.runtime_profile },
              { label: 'Pairing mode', value: spokePairing.spokeActivation.pairing_mode },
              { label: 'Expires at', value: spokePairing.spokeActivation.expires_at },
            ]}
          />
          <ul style={{ marginBottom: 0, marginTop: '16px', color: '#4e5871', lineHeight: 1.7 }}>
            {spokePairing.relayOperations.map((operation) => (
              <li key={operation}>
                {operation}
                {' '}:: allowed
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <div style={{ height: '16px' }} />

      <ActionButton
        onClick={() => void syncMonitoring.loadSyncMonitoring()}
        disabled={syncMonitoring.isBusy || !accessToken || !tenantId || !branchId}
      >
        Load sync monitoring
      </ActionButton>

      {syncMonitoring.syncStatus ? (
        <div style={{ marginTop: '16px' }}>
          <DetailList
            items={[
              { label: 'Hub device', value: syncMonitoring.syncStatus.source_device_id ?? syncMonitoring.syncStatus.hub_device_id ?? 'Unbound' },
              { label: 'Runtime state', value: syncMonitoring.syncStatus.runtime_state },
              { label: 'Branch cursor', value: String(syncMonitoring.syncStatus.branch_cursor) },
              { label: 'Last pull cursor', value: String(syncMonitoring.syncStatus.last_pull_cursor) },
              { label: 'Open conflicts', value: String(syncMonitoring.syncStatus.open_conflict_count) },
              { label: 'Connected spokes', value: String(syncMonitoring.syncStatus.connected_spoke_count) },
              { label: 'Pending mutations', value: String(syncMonitoring.syncStatus.pending_mutation_count) },
              { label: 'Local outbox depth', value: String(syncMonitoring.syncStatus.local_outbox_depth) },
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

      {spokes.length ? (
        <ul style={{ marginBottom: '16px', marginTop: '16px', color: '#4e5871', lineHeight: 1.7 }}>
          {spokes.map((record) => (
            <li key={record.spoke_device_id}>
              {record.runtime_profile} :: {record.connection_state} :: {record.hostname ?? record.runtime_kind}
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

      {spokePairing.errorMessage ? <p style={{ color: '#9d2b19', marginBottom: 0 }}>{spokePairing.errorMessage}</p> : null}
      {syncMonitoring.errorMessage ? <p style={{ color: '#9d2b19', marginBottom: 0 }}>{syncMonitoring.errorMessage}</p> : null}
    </SectionCard>
  );
}
