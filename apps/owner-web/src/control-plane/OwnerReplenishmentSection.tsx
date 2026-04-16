import { ActionButton, DetailList, FormField, SectionCard, StatusBadge } from '@store/ui';
import type { OwnerWorkspaceState } from './useOwnerWorkspace';

export function OwnerReplenishmentSection({ workspace }: { workspace: OwnerWorkspaceState }) {
  const latestPolicy =
    workspace.latestBranchCatalogItem?.reorder_point != null && workspace.latestBranchCatalogItem?.target_stock != null
      ? workspace.latestBranchCatalogItem
      : null;

  return (
    <>
      <SectionCard eyebrow="Branch replenishment" title="Replenishment policy">
        <FormField
          id="replenishment-reorder-point"
          label="Reorder point"
          value={workspace.replenishmentReorderPoint}
          onChange={workspace.setReplenishmentReorderPoint}
          placeholder="10"
        />
        <FormField
          id="replenishment-target-stock"
          label="Target stock"
          value={workspace.replenishmentTargetStock}
          onChange={workspace.setReplenishmentTargetStock}
          placeholder="24"
        />
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          <ActionButton
            onClick={() => void workspace.updateFirstBranchReplenishmentPolicy()}
            disabled={
              workspace.isBusy ||
              !workspace.actor ||
              !workspace.branchId ||
              workspace.branchCatalogItems.length === 0 ||
              !workspace.replenishmentReorderPoint ||
              !workspace.replenishmentTargetStock
            }
          >
            Set replenishment policy for first branch item
          </ActionButton>
          <ActionButton onClick={() => void workspace.loadReplenishmentBoard()} disabled={workspace.isBusy || !workspace.actor || !workspace.branchId}>
            Refresh replenishment board
          </ActionButton>
        </div>

        {latestPolicy ? (
          <div style={{ marginTop: '16px' }}>
            <h3 style={{ marginBottom: '10px' }}>Latest replenishment policy</h3>
            <DetailList
              items={[
                { label: 'Product', value: latestPolicy.product_name },
                { label: 'Reorder point', value: String(latestPolicy.reorder_point) },
                { label: 'Target stock', value: String(latestPolicy.target_stock) },
              ]}
            />
          </div>
        ) : null}
      </SectionCard>

      <SectionCard eyebrow="Low-stock visibility" title="Replenishment board">
        <ul style={{ marginBottom: 0, marginTop: 0, color: '#4e5871', lineHeight: 1.7 }}>
          {workspace.replenishmentBoard?.records.length ? (
            workspace.replenishmentBoard.records.map((record) => (
              <li key={record.product_id}>
                {record.product_name} ::{' '}
                <StatusBadge label={record.replenishment_status} tone={record.replenishment_status === 'LOW_STOCK' ? 'warning' : 'success'} /> :: suggest{' '}
                {record.suggested_reorder_quantity}
              </li>
            ))
          ) : (
            <li>No replenishment suggestions yet.</li>
          )}
        </ul>
      </SectionCard>
    </>
  );
}
