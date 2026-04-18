import { ActionButton, DetailList, FormField, SectionCard, StatusBadge } from '@store/ui';
import type { OwnerWorkspaceState } from './useOwnerWorkspace';

export function OwnerBatchExpirySection({ workspace }: { workspace: OwnerWorkspaceState }) {
  const batchExpiryReportRecords = workspace.batchExpiryReport?.records ?? [];
  const batchExpiryBoardRecords = workspace.batchExpiryBoard?.records ?? [];
  const catalogProducts = workspace.catalogProducts ?? [];
  const firstBatchRecord = batchExpiryReportRecords[0] ?? null;
  const activeExpirySession = workspace.latestBatchExpirySession;
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
    <>
      <SectionCard eyebrow="Batch intake control" title="Batch expiry and lot control">
        <FormField id="lot-a-batch-number" label="Lot A batch number" value={workspace.lotABatchNumber} onChange={workspace.setLotABatchNumber} />
        <FormField id="lot-a-quantity" label="Lot A quantity" value={workspace.lotAQuantity} onChange={workspace.setLotAQuantity} />
        <FormField id="lot-a-expiry-date" label="Lot A expiry date" value={workspace.lotAExpiryDate} onChange={workspace.setLotAExpiryDate} />
        <FormField id="lot-b-batch-number" label="Lot B batch number" value={workspace.lotBBatchNumber} onChange={workspace.setLotBBatchNumber} />
        <FormField id="lot-b-quantity" label="Lot B quantity" value={workspace.lotBQuantity} onChange={workspace.setLotBQuantity} />
        <FormField id="lot-b-expiry-date" label="Lot B expiry date" value={workspace.lotBExpiryDate} onChange={workspace.setLotBExpiryDate} />
        <ActionButton
          onClick={() => void workspace.recordBatchLotsOnLatestGoodsReceipt()}
          disabled={
            workspace.isBusy
            || !workspace.actor
            || !workspace.tenantId
            || !workspace.branchId
            || !catalogProducts[0]
            || !workspace.lotABatchNumber
            || !workspace.lotAQuantity
            || !workspace.lotAExpiryDate
            || !workspace.lotBBatchNumber
            || !workspace.lotBQuantity
            || !workspace.lotBExpiryDate
          }
        >
          Record batch lots on latest goods receipt
        </ActionButton>

        {workspace.latestBatchLotIntake ? (
          <div style={{ marginTop: '16px' }}>
            <h3 style={{ marginBottom: '10px' }}>Latest batch lot intake</h3>
            <DetailList
              items={[
                { label: 'Goods receipt', value: workspace.latestBatchLotIntake.goods_receipt_id },
                { label: 'Batch numbers', value: workspace.latestBatchLotIntake.records.map((record) => record.batch_number).join(', ') },
                { label: 'Lots recorded', value: String(workspace.latestBatchLotIntake.records.length) },
              ]}
            />
          </div>
        ) : null}
      </SectionCard>

      <SectionCard eyebrow="Expiry visibility" title="Branch batch expiry report">
        <ActionButton
          onClick={() => void workspace.loadBatchExpiryReport()}
          disabled={workspace.isBusy || !workspace.actor || !workspace.branchId}
        >
          Load branch expiry report
        </ActionButton>

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
              {batchExpiryReportRecords.map((record) => (
                <li key={record.batch_lot_id}>
                  {record.batch_number} :: {record.product_name} :: {record.remaining_quantity} ::{' '}
                  <StatusBadge label={record.status} tone={record.status === 'FRESH' ? 'success' : 'warning'} />
                </li>
              ))}
            </ul>
          </>
        ) : (
          <p style={{ margin: '16px 0 0', color: '#4e5871' }}>Load the branch expiry report to review tracked lots and expiring stock.</p>
        )}

        <div style={{ height: '16px' }} />

        <FormField
          id="expiry-session-note"
          label="Expiry session note"
          value={workspace.expirySessionNote}
          onChange={workspace.setExpirySessionNote}
        />
        <ActionButton
          onClick={() => void workspace.createBatchExpirySession()}
          disabled={workspace.isBusy || !workspace.actor || !firstBatchRecord}
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
              id="expiry-review-quantity"
              label="Proposed write-off quantity"
              value={workspace.expiryWriteOffQuantity}
              onChange={workspace.setExpiryWriteOffQuantity}
            />
            <FormField
              id="expiry-review-reason"
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
              id="expiry-review-note"
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

        {workspace.latestBatchExpiryWriteOff ? (
          <div style={{ marginTop: '16px' }}>
            <h3 style={{ marginBottom: '10px' }}>Latest expiry write-off</h3>
            <DetailList
              items={[
                { label: 'Batch', value: workspace.latestBatchExpiryWriteOff.batch_number },
                { label: 'Remaining quantity', value: String(workspace.latestBatchExpiryWriteOff.remaining_quantity) },
                { label: 'Status', value: <StatusBadge label={workspace.latestBatchExpiryWriteOff.status} tone="warning" /> },
              ]}
            />
          </div>
        ) : null}

        <div style={{ marginTop: '16px' }}>
          <h3 style={{ marginBottom: '10px' }}>Expiry disposition board</h3>
          <ul style={{ marginBottom: 0, marginTop: 0, color: '#4e5871', lineHeight: 1.7 }}>
            {batchExpiryBoardRecords.length ? (
              batchExpiryBoardRecords.map((record) => (
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
      </SectionCard>
    </>
  );
}
