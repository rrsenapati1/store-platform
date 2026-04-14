import { ActionButton, DetailList, FormField, SectionCard, StatusBadge } from '@store/ui';
import type { OwnerWorkspaceState } from './useOwnerWorkspace';

export function OwnerBatchExpirySection({ workspace }: { workspace: OwnerWorkspaceState }) {
  const firstBatchRecord = workspace.batchExpiryReport?.records[0] ?? null;

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
            || !workspace.catalogProducts[0]
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
              {workspace.batchExpiryReport.records.map((record) => (
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
          id="expiry-write-off-quantity"
          label="Expiry write-off quantity"
          value={workspace.expiryWriteOffQuantity}
          onChange={workspace.setExpiryWriteOffQuantity}
        />
        <FormField
          id="expiry-write-off-reason"
          label="Expiry write-off reason"
          value={workspace.expiryWriteOffReason}
          onChange={workspace.setExpiryWriteOffReason}
        />
        <ActionButton
          onClick={() => void workspace.writeOffFirstExpiringLot()}
          disabled={workspace.isBusy || !workspace.actor || !firstBatchRecord || !workspace.expiryWriteOffQuantity || !workspace.expiryWriteOffReason}
        >
          Write off first expiring lot
        </ActionButton>

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
      </SectionCard>
    </>
  );
}
