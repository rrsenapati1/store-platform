import { ActionButton, DetailList, FormField, SectionCard } from '@store/ui';
import type { StoreRuntimeWorkspaceState } from './useStoreRuntimeWorkspace';

const RESTOCK_SOURCE_OPTIONS = [
  { value: 'BACKROOM_AVAILABLE', label: 'Backroom available' },
  { value: 'BACKROOM_UNCERTAIN', label: 'Backroom uncertain' },
  { value: 'BACKROOM_UNAVAILABLE', label: 'Backroom unavailable' },
];

export function StoreRestockSection({ workspace }: { workspace: StoreRuntimeWorkspaceState }) {
  const scannedLookup = workspace.latestScanLookup;
  const branchCatalogItem = workspace.branchCatalogItems.find(
    (item) => item.product_id === scannedLookup?.product_id,
  );
  const activeTask = workspace.restockBoard?.records.find(
    (record) => record.product_id === scannedLookup?.product_id && record.has_active_task,
  ) ?? null;
  const reorderPoint = branchCatalogItem?.reorder_point ?? null;
  const targetStock = branchCatalogItem?.target_stock ?? null;
  const stockOnHand = scannedLookup?.stock_on_hand ?? null;
  const suggestedRestock = stockOnHand !== null && targetStock !== null
    ? Math.max(targetStock - stockOnHand, 0)
    : null;

  return (
    <SectionCard eyebrow="Assisted stock workflow" title="Assisted restock">
      <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginBottom: '16px' }}>
        <ActionButton onClick={() => void workspace.loadRestockBoard()} disabled={workspace.isBusy || !workspace.isSessionLive}>
          Refresh restock board
        </ActionButton>
      </div>

      {scannedLookup ? (
        <div style={{ marginBottom: '16px' }}>
          <h3 style={{ marginBottom: '10px' }}>Latest scanned stock workflow</h3>
          <DetailList
            items={[
              { label: 'Product', value: scannedLookup.product_name },
              { label: 'SKU', value: scannedLookup.sku_code },
              { label: 'Stock on hand', value: String(scannedLookup.stock_on_hand) },
              { label: 'Reorder point', value: reorderPoint !== null ? String(reorderPoint) : 'No policy set' },
              { label: 'Target stock', value: targetStock !== null ? String(targetStock) : 'No policy set' },
              { label: 'Suggested restock', value: suggestedRestock !== null ? String(suggestedRestock) : 'No policy set' },
              { label: 'Active restock task', value: activeTask?.task_number ?? 'No active task' },
            ]}
          />
          {suggestedRestock !== null ? (
            <p style={{ marginBottom: 0, color: '#4e5871' }}>
              Suggested restock -&gt; {suggestedRestock}
            </p>
          ) : (
            <p style={{ marginBottom: 0, color: '#4e5871' }}>
              This scanned product does not have a branch replenishment policy yet.
            </p>
          )}
          {activeTask ? (
            <p style={{ marginBottom: 0, color: '#4e5871' }}>
              Active restock task -&gt; {activeTask.task_number}
            </p>
          ) : null}
        </div>
      ) : (
        <p style={{ color: '#4e5871' }}>
          Scan and look up a branch item first to drive an assisted restock workflow from the runtime counter surface.
        </p>
      )}

      <FormField
        id="runtime-restock-requested-quantity"
        label="Restock requested quantity"
        value={workspace.restockRequestedQuantity}
        onChange={workspace.setRestockRequestedQuantity}
        placeholder={suggestedRestock !== null ? String(suggestedRestock) : '12'}
      />
      <div style={{ display: 'grid', gap: '8px', marginBottom: '16px' }}>
        <label htmlFor="runtime-restock-source-posture" style={{ fontWeight: 600 }}>
          Restock source posture
        </label>
        <select
          id="runtime-restock-source-posture"
          value={workspace.restockSourcePosture}
          onChange={(event) => workspace.setRestockSourcePosture(event.target.value)}
          style={{
            borderRadius: '12px',
            border: '1px solid rgba(23, 32, 51, 0.14)',
            padding: '11px 14px',
            fontSize: '15px',
            background: '#fff',
            color: '#172033',
          }}
        >
          {RESTOCK_SOURCE_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>
      <FormField
        id="runtime-restock-note"
        label="Restock note"
        value={workspace.restockNote}
        onChange={workspace.setRestockNote}
        placeholder="Shelf gap on aisle 2"
      />
      <FormField
        id="runtime-restock-picked-quantity"
        label="Restock picked quantity"
        value={workspace.restockPickedQuantity}
        onChange={workspace.setRestockPickedQuantity}
        placeholder="10"
      />
      <FormField
        id="runtime-restock-completion-note"
        label="Restock completion note"
        value={workspace.restockCompletionNote}
        onChange={workspace.setRestockCompletionNote}
        placeholder="Shelf filled before rush hour"
      />

      <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
        <ActionButton
          onClick={() => void workspace.createRestockTaskForLatestScanLookup()}
          disabled={workspace.isBusy || !workspace.isSessionLive || !scannedLookup || !branchCatalogItem || !workspace.restockRequestedQuantity}
        >
          Create restock task for scanned product
        </ActionButton>
        <ActionButton
          onClick={() => void workspace.pickActiveRestockTaskForLatestScanLookup()}
          disabled={workspace.isBusy || !workspace.isSessionLive || !activeTask || !workspace.restockPickedQuantity}
        >
          Mark active task picked
        </ActionButton>
        <ActionButton
          onClick={() => void workspace.completeActiveRestockTaskForLatestScanLookup()}
          disabled={workspace.isBusy || !workspace.isSessionLive || !activeTask}
        >
          Complete active task
        </ActionButton>
        <ActionButton
          onClick={() => void workspace.cancelActiveRestockTaskForLatestScanLookup()}
          disabled={workspace.isBusy || !workspace.isSessionLive || !activeTask}
        >
          Cancel active task
        </ActionButton>
      </div>

      <div style={{ marginTop: '16px' }}>
        <h3 style={{ marginBottom: '10px' }}>Restock board summary</h3>
        <ul style={{ marginTop: 0, marginBottom: '16px', color: '#4e5871', lineHeight: 1.7 }}>
          <li>Open tasks -&gt; {workspace.restockBoard?.open_count ?? 0}</li>
          <li>Picked tasks -&gt; {workspace.restockBoard?.picked_count ?? 0}</li>
          <li>Completed tasks -&gt; {workspace.restockBoard?.completed_count ?? 0}</li>
          <li>Canceled tasks -&gt; {workspace.restockBoard?.canceled_count ?? 0}</li>
        </ul>
        <ul style={{ margin: 0, color: '#4e5871', lineHeight: 1.7 }}>
          {workspace.restockBoard?.records.length ? (
            workspace.restockBoard.records.map((record) => (
              <li key={record.restock_task_id}>
                {record.task_number} :: {record.product_name} :: {record.status} :: requested {record.requested_quantity} :: picked {record.picked_quantity ?? 0}
                {record.completion_note ? ` :: ${record.completion_note}` : ''}
              </li>
            ))
          ) : (
            <li>No restock tasks recorded yet.</li>
          )}
        </ul>
      </div>
    </SectionCard>
  );
}
