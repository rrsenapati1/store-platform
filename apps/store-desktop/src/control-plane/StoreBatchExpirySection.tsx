import { ActionButton, DetailList, FormField, SectionCard, StatusBadge } from '@store/ui';
import type { StoreRuntimeWorkspaceState } from './useStoreRuntimeWorkspace';

export function StoreBatchExpirySection({ workspace }: { workspace: StoreRuntimeWorkspaceState }) {
  const firstBatchRecord = workspace.batchExpiryReport?.records[0] ?? null;

  return (
    <SectionCard eyebrow="Branch stock protection" title="Branch batch expiry">
      <ActionButton
        onClick={() => void workspace.loadBatchExpiryReport()}
        disabled={workspace.isBusy || !workspace.isSessionLive || !workspace.branchId}
      >
        Load branch expiry report
      </ActionButton>

      {workspace.batchExpiryReport ? (
        <div style={{ marginTop: '16px' }}>
          <h3 style={{ marginBottom: '10px' }}>Latest branch expiry report</h3>
          <DetailList
            items={[
              { label: 'Tracked lots', value: String(workspace.batchExpiryReport.tracked_lot_count) },
              { label: 'Expiring soon', value: String(workspace.batchExpiryReport.expiring_soon_count) },
              { label: 'Expired', value: String(workspace.batchExpiryReport.expired_count) },
            ]}
          />
          <ul style={{ marginBottom: 0, marginTop: '16px', color: '#4e5871', lineHeight: 1.7 }}>
            {workspace.batchExpiryReport.records.map((record) => (
              <li key={record.batch_lot_id}>
                {record.batch_number} :: {record.product_name} :: {record.remaining_quantity} ::{' '}
                <StatusBadge label={record.status} tone={record.status === 'FRESH' ? 'success' : 'warning'} />
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <div style={{ height: '16px' }} />

      <FormField
        id="runtime-expiry-write-off-quantity"
        label="Expiry write-off quantity"
        value={workspace.expiryWriteOffQuantity}
        onChange={workspace.setExpiryWriteOffQuantity}
      />
      <FormField
        id="runtime-expiry-write-off-reason"
        label="Expiry write-off reason"
        value={workspace.expiryWriteOffReason}
        onChange={workspace.setExpiryWriteOffReason}
      />
      <ActionButton
        onClick={() => void workspace.createBatchExpiryWriteOff()}
        disabled={workspace.isBusy || !workspace.isSessionLive || !firstBatchRecord || !workspace.expiryWriteOffReason || !workspace.expiryWriteOffQuantity}
      >
        Write off first expiring lot
      </ActionButton>

      {workspace.latestBatchWriteOff ? (
        <div style={{ marginTop: '16px' }}>
          <h3 style={{ marginBottom: '10px' }}>Latest batch write-off</h3>
          <DetailList
            items={[
              { label: 'Batch', value: workspace.latestBatchWriteOff.batch_number },
              { label: 'Remaining quantity', value: String(workspace.latestBatchWriteOff.remaining_quantity) },
              { label: 'Reason', value: workspace.latestBatchWriteOff.reason },
            ]}
          />
        </div>
      ) : null}
    </SectionCard>
  );
}
