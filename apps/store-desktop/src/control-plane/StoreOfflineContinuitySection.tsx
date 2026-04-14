import { ActionButton, DetailList, SectionCard, StatusBadge } from '@store/ui';
import type { StoreRuntimeWorkspaceState } from './useStoreRuntimeWorkspace';

function formatReconciliationState(state: string) {
  switch (state) {
    case 'PENDING_REPLAY':
      return 'Pending reconciliation';
    case 'REPLAYING':
      return 'Replaying';
    case 'RECONCILED':
      return 'Reconciled';
    case 'CONFLICT':
      return 'Conflict review required';
    case 'REJECTED':
      return 'Rejected';
    default:
      return state;
  }
}

function toneForState(state: string): 'neutral' | 'success' | 'warning' {
  switch (state) {
    case 'RECONCILED':
      return 'success';
    case 'CONFLICT':
    case 'REJECTED':
      return 'neutral';
    case 'REPLAYING':
    case 'PENDING_REPLAY':
      return 'warning';
    default:
      return 'neutral';
  }
}

export function StoreOfflineContinuitySection({ workspace }: { workspace: StoreRuntimeWorkspaceState }) {
  const bannerMessage = 'Cloud unavailable. Branch continuity mode is active.';
  const secondaryMessage = workspace.offlineContinuityMessage && workspace.offlineContinuityMessage !== bannerMessage
    ? workspace.offlineContinuityMessage
    : null;

  if (!workspace.hasLoadedOfflineContinuity) {
    return (
      <SectionCard eyebrow="Offline continuity" title="Branch continuity">
        <p style={{ margin: 0, color: '#4e5871' }}>Checking whether this runtime can continue issuing local offline sales.</p>
      </SectionCard>
    );
  }

  if (!workspace.offlineContinuityReady && workspace.offlineSales.length === 0) {
    return (
      <SectionCard eyebrow="Offline continuity" title="Branch continuity">
        <p style={{ margin: 0, color: '#4e5871' }}>
          Offline sales are only available on approved branch hubs after a branch stock snapshot has been seeded locally.
        </p>
      </SectionCard>
    );
  }

  return (
    <SectionCard eyebrow="Offline continuity" title={`Pending offline sales: ${workspace.pendingOfflineSaleCount}`}>
      {workspace.isOfflineContinuityActive ? (
        <p style={{ marginTop: 0, color: '#9d2b19', fontWeight: 700 }}>
          {bannerMessage}
        </p>
      ) : null}
      {secondaryMessage ? (
        <p style={{ color: '#4e5871' }}>{secondaryMessage}</p>
      ) : null}
      <DetailList
        items={[
          { label: 'Backend', value: workspace.offlineContinuityBackendLabel },
          { label: 'Snapshot', value: workspace.offlineContinuityCachedAt ?? 'Not seeded yet' },
          { label: 'Conflicts', value: String(workspace.offlineConflictCount) },
        ]}
      />
      <ActionButton
        onClick={() => void workspace.replayOfflineSales()}
        disabled={workspace.isBusy || !workspace.pendingOfflineSaleCount}
      >
        Replay offline sales
      </ActionButton>

      <div style={{ marginTop: '16px' }}>
        <h3 style={{ marginTop: 0, marginBottom: '12px', fontSize: '15px' }}>Offline sales</h3>
        <ul style={{ margin: 0, color: '#4e5871', lineHeight: 1.7 }}>
          {workspace.offlineSales.length ? (
            workspace.offlineSales.map((sale) => (
              <li key={sale.continuity_sale_id}>
                {sale.continuity_invoice_number}
                {' '}::{' '}
                <StatusBadge label={formatReconciliationState(sale.reconciliation_state)} tone={toneForState(sale.reconciliation_state)} />
                {sale.replayed_invoice_number ? ` :: ${sale.replayed_invoice_number}` : ''}
              </li>
            ))
          ) : (
            <li>No offline sales recorded in this runtime yet.</li>
          )}
        </ul>
      </div>

      {workspace.offlineConflicts.length ? (
        <div style={{ marginTop: '16px' }}>
          <h3 style={{ marginTop: 0, marginBottom: '12px', fontSize: '15px' }}>Conflict review</h3>
          <ul style={{ margin: 0, color: '#4e5871', lineHeight: 1.7 }}>
            {workspace.offlineConflicts.map((conflict) => (
              <li key={`${conflict.continuity_sale_id}:${conflict.recorded_at}`}>
                {conflict.continuity_sale_id} :: {conflict.message}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </SectionCard>
  );
}
