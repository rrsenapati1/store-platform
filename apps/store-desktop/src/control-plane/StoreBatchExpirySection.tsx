import { ActionButton, DetailList, FormField, SectionCard, StatusBadge } from '@store/ui';
import type { StoreRuntimeWorkspaceState } from './useStoreRuntimeWorkspace';

export function StoreBatchExpirySection({ workspace }: { workspace: StoreRuntimeWorkspaceState }) {
  const batchExpiryRecords = workspace.batchExpiryReport?.records ?? [];
  const firstBatchRecord = batchExpiryRecords[0] ?? null;
  const activeExpirySession = workspace.activeBatchExpirySession;
  const isOpenExpirySession = activeExpirySession?.status === 'OPEN';
  const isReviewedExpirySession = activeExpirySession?.status === 'REVIEWED';
  const activeExpirySessionDetails = activeExpirySession
    ? [
        { label: 'Session number', value: activeExpirySession.session_number },
        {
          label: 'Status',
          value: (
            <StatusBadge
              label={activeExpirySession.status}
              tone={
                activeExpirySession.status === 'APPROVED'
                  ? 'success'
                  : activeExpirySession.status === 'REVIEWED'
                    ? 'warning'
                    : 'neutral'
              }
            />
          ),
        },
        { label: 'Remaining quantity snapshot', value: String(activeExpirySession.remaining_quantity_snapshot) },
        ...(activeExpirySession.status === 'OPEN'
          ? [{ label: 'Session note', value: activeExpirySession.note || 'Pending' }]
          : [
              { label: 'Proposed quantity', value: String(activeExpirySession.proposed_quantity) },
              { label: 'Reason', value: activeExpirySession.reason || 'Pending' },
              { label: 'Session note', value: activeExpirySession.note || 'Pending' },
              { label: 'Review note', value: activeExpirySession.review_note || 'Pending' },
            ]),
      ]
    : [];

  return (
    <SectionCard eyebrow="Branch stock protection" title="Branch batch expiry">
      <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
        <ActionButton
          onClick={() => void workspace.loadBatchExpiryReport()}
          disabled={workspace.isBusy || !workspace.isSessionLive || !workspace.branchId}
        >
          Load branch expiry report
        </ActionButton>
        <ActionButton
          onClick={() => void workspace.loadBatchExpiryBoard()}
          disabled={workspace.isBusy || !workspace.isSessionLive || !workspace.branchId}
        >
          Load expiry board
        </ActionButton>
      </div>

      {workspace.batchExpiryReport ? (
        <>
          <div style={{ marginTop: '16px' }}>
            <h3 style={{ marginBottom: '10px' }}>Latest branch expiry report</h3>
            <DetailList
              items={[
                { label: 'Tracked lots', value: String(workspace.batchExpiryReport.tracked_lot_count) },
                { label: 'Expiring soon', value: String(workspace.batchExpiryReport.expiring_soon_count) },
                { label: 'Expired', value: String(workspace.batchExpiryReport.expired_count) },
              ]}
            />
          </div>
          <ul style={{ marginBottom: 0, marginTop: '16px', color: '#4e5871', lineHeight: 1.7 }}>
            {batchExpiryRecords.map((record) => (
              <li key={record.batch_lot_id}>
                {record.batch_number} :: {record.product_name} :: {record.remaining_quantity} ::{' '}
                <StatusBadge label={record.status} tone={record.status === 'FRESH' ? 'success' : 'warning'} />
              </li>
            ))}
          </ul>
        </>
      ) : (
        <p style={{ margin: '16px 0 0', color: '#4e5871' }}>
          Load the branch expiry report to review tracked lots and expiring stock.
        </p>
      )}

      <div style={{ marginTop: '16px' }}>
        <h3 style={{ marginBottom: '10px' }}>Expiry disposition board</h3>
        <ul style={{ marginBottom: 0, marginTop: 0, color: '#4e5871', lineHeight: 1.7 }}>
          {workspace.batchExpiryBoard?.records.length ? (
            workspace.batchExpiryBoard.records.map((record) => (
              <li key={record.batch_expiry_session_id}>
                {record.session_number} :: {record.batch_number} :: {record.status}
                {record.proposed_quantity == null ? '' : ` :: proposed ${record.proposed_quantity}`}
              </li>
            ))
          ) : (
            <li>No expiry review sessions recorded yet.</li>
          )}
        </ul>
      </div>

      <div style={{ height: '16px' }} />

      <FormField
        id="runtime-expiry-session-note"
        label="Expiry session note"
        value={workspace.expirySessionNote}
        onChange={workspace.setExpirySessionNote}
      />
      <ActionButton
        onClick={() => void workspace.createBatchExpirySession()}
        disabled={workspace.isBusy || !workspace.isSessionLive || !firstBatchRecord}
      >
        Open expiry review session
      </ActionButton>

      {activeExpirySession ? (
        <div style={{ marginTop: '16px' }}>
          <h3 style={{ marginBottom: '10px' }}>Latest expiry review session</h3>
          <DetailList items={activeExpirySessionDetails} />
        </div>
      ) : null}

      {isOpenExpirySession ? (
        <div style={{ marginTop: '16px' }}>
          <FormField
            id="runtime-expiry-review-quantity"
            label="Proposed write-off quantity"
            value={workspace.expiryWriteOffQuantity}
            onChange={workspace.setExpiryWriteOffQuantity}
          />
          <FormField
            id="runtime-expiry-review-reason"
            label="Expiry review reason"
            value={workspace.expiryWriteOffReason}
            onChange={workspace.setExpiryWriteOffReason}
          />
          <ActionButton
            onClick={() => void workspace.recordBatchExpirySession()}
            disabled={workspace.isBusy || !workspace.expiryWriteOffQuantity || !workspace.expiryWriteOffReason}
          >
            Record expiry review
          </ActionButton>
        </div>
      ) : null}

      {isReviewedExpirySession ? (
        <div style={{ marginTop: '16px' }}>
          <h3 style={{ marginBottom: '10px' }}>Review expiry session</h3>
          <FormField
            id="runtime-expiry-review-note"
            label="Expiry review note"
            value={workspace.expiryReviewNote}
            onChange={workspace.setExpiryReviewNote}
          />
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <ActionButton onClick={() => void workspace.approveBatchExpirySession()} disabled={workspace.isBusy}>
              Approve expiry session
            </ActionButton>
            <ActionButton onClick={() => void workspace.cancelBatchExpirySession()} disabled={workspace.isBusy}>
              Cancel expiry session
            </ActionButton>
          </div>
        </div>
      ) : null}

      {workspace.latestBatchWriteOff ? (
        <div style={{ marginTop: '16px' }}>
          <h3 style={{ marginBottom: '10px' }}>Latest expiry write-off</h3>
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
