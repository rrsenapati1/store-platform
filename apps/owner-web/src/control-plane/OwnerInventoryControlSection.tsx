import { ActionButton, DetailList, FormField, SectionCard, StatusBadge } from '@store/ui';
import type { OwnerWorkspaceState } from './useOwnerWorkspace';

function branchTransferOptions(workspace: OwnerWorkspaceState) {
  return workspace.branches.filter((branch) => branch.branch_id !== workspace.branchId);
}

export function OwnerInventoryControlSection({ workspace }: { workspace: OwnerWorkspaceState }) {
  const transferBranches = branchTransferOptions(workspace);

  return (
    <>
      <SectionCard eyebrow="Inventory controls" title="Stock adjustments and counts">
        <FormField
          id="stock-adjustment-delta"
          label="Adjustment delta"
          value={workspace.adjustmentDelta}
          onChange={workspace.setAdjustmentDelta}
          placeholder="-2"
        />
        <FormField
          id="stock-adjustment-reason"
          label="Adjustment reason"
          value={workspace.adjustmentReason}
          onChange={workspace.setAdjustmentReason}
          placeholder="Shelf damage"
        />
        <ActionButton
          onClick={() => void workspace.createStockAdjustment()}
          disabled={workspace.isBusy || !workspace.actor || !workspace.branchId || !workspace.adjustmentDelta || !workspace.adjustmentReason}
        >
          Post stock adjustment
        </ActionButton>

        {workspace.latestStockAdjustment ? (
          <div style={{ marginTop: '16px' }}>
            <h3 style={{ marginBottom: '10px' }}>Latest stock adjustment</h3>
            <DetailList
              items={[
                { label: 'Reason', value: workspace.latestStockAdjustment.reason },
                { label: 'Delta', value: String(workspace.latestStockAdjustment.quantity_delta) },
                { label: 'Resulting stock', value: String(workspace.latestStockAdjustment.resulting_stock_on_hand) },
              ]}
            />
          </div>
        ) : null}

        <div style={{ height: '16px' }} />

        <FormField
          id="stock-count-quantity"
          label="Counted quantity"
          value={workspace.countedQuantity}
          onChange={workspace.setCountedQuantity}
          placeholder="20"
        />
        <FormField id="stock-count-note" label="Count note" value={workspace.countNote} onChange={workspace.setCountNote} />
        <ActionButton
          onClick={() => void workspace.createStockCount()}
          disabled={workspace.isBusy || !workspace.actor || !workspace.branchId || !workspace.countedQuantity}
        >
          Record stock count
        </ActionButton>

        {workspace.latestStockCount ? (
          <div style={{ marginTop: '16px' }}>
            <h3 style={{ marginBottom: '10px' }}>Latest stock count</h3>
            <DetailList
              items={[
                { label: 'Expected', value: String(workspace.latestStockCount.expected_quantity) },
                { label: 'Counted', value: String(workspace.latestStockCount.counted_quantity) },
                { label: 'Variance', value: String(workspace.latestStockCount.variance_quantity) },
              ]}
            />
          </div>
        ) : null}
      </SectionCard>

      <SectionCard eyebrow="Branch stock movement" title="Branch transfers">
        <FormField
          id="transfer-quantity"
          label="Transfer quantity"
          value={workspace.transferQuantity}
          onChange={workspace.setTransferQuantity}
          placeholder="5"
        />
        <div style={{ display: 'grid', gap: '8px', marginBottom: '16px' }}>
          <label htmlFor="transfer-destination-branch" style={{ color: '#27324a', fontSize: '0.95rem', fontWeight: 600 }}>
            Destination branch
          </label>
          <select
            id="transfer-destination-branch"
            value={workspace.transferDestinationBranchId}
            onChange={(event) => workspace.setTransferDestinationBranchId(event.target.value)}
            style={{
              border: '1px solid #d7dbea',
              borderRadius: '12px',
              color: '#1d2433',
              fontSize: '0.95rem',
              minHeight: '48px',
              padding: '0 14px',
            }}
          >
            <option value="">Select branch</option>
            {transferBranches.map((branch) => (
              <option key={branch.branch_id} value={branch.branch_id}>
                {branch.name}
              </option>
            ))}
          </select>
        </div>
        <ActionButton
          onClick={() => void workspace.createBranchTransfer()}
          disabled={workspace.isBusy || !workspace.actor || !workspace.branchId || !workspace.transferQuantity || !workspace.transferDestinationBranchId}
        >
          Create branch transfer
        </ActionButton>

        {workspace.latestTransfer ? (
          <div style={{ marginTop: '16px' }}>
            <h3 style={{ marginBottom: '10px' }}>Latest branch transfer</h3>
            <DetailList
              items={[
                { label: 'Transfer number', value: workspace.latestTransfer.transfer_number },
                { label: 'Quantity', value: String(workspace.latestTransfer.quantity) },
                { label: 'Status', value: <StatusBadge label={workspace.latestTransfer.status} tone="success" /> },
              ]}
            />
          </div>
        ) : null}
      </SectionCard>

      <SectionCard eyebrow="Transfer visibility" title="Transfer board">
        <ul style={{ marginBottom: 0, marginTop: 0, color: '#4e5871', lineHeight: 1.7 }}>
          {workspace.transferBoard?.records.length ? (
            workspace.transferBoard.records.map((record) => (
              <li key={record.transfer_order_id}>
                {record.transfer_number} :: {record.direction} :: {record.counterparty_branch_name} :: {record.product_name} :: {record.quantity}
              </li>
            ))
          ) : (
            <li>No branch transfers recorded yet.</li>
          )}
        </ul>
      </SectionCard>
    </>
  );
}
