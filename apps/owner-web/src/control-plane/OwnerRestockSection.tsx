import { ActionButton, DetailList, FormField, SectionCard, StatusBadge } from '@store/ui';
import type { OwnerWorkspaceState } from './useOwnerWorkspace';

export function OwnerRestockSection({ workspace }: { workspace: OwnerWorkspaceState }) {
  const lowStockRecord = workspace.replenishmentBoard?.records.find((record) => record.replenishment_status === 'LOW_STOCK') ?? null;

  return (
    <>
      <SectionCard eyebrow="Shelf/backroom coordination" title="Restock task workflow">
        <FormField
          id="restock-requested-quantity"
          label="Requested quantity"
          value={workspace.restockRequestedQuantity}
          onChange={workspace.setRestockRequestedQuantity}
          placeholder="12"
        />
        <FormField
          id="restock-source-posture"
          label="Source posture"
          value={workspace.restockSourcePosture}
          onChange={workspace.setRestockSourcePosture}
          placeholder="BACKROOM_AVAILABLE"
        />
        <FormField
          id="restock-note"
          label="Restock note"
          value={workspace.restockNote}
          onChange={workspace.setRestockNote}
          placeholder="Front shelf refill"
        />
        <FormField
          id="restock-picked-quantity"
          label="Picked quantity"
          value={workspace.restockPickedQuantity}
          onChange={workspace.setRestockPickedQuantity}
          placeholder="10"
        />
        <FormField
          id="restock-completion-note"
          label="Completion note"
          value={workspace.restockCompletionNote}
          onChange={workspace.setRestockCompletionNote}
          placeholder="Shelf refill done"
        />
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          <ActionButton
            onClick={() => void workspace.createRestockTask()}
            disabled={
              workspace.isBusy ||
              !workspace.actor ||
              !workspace.branchId ||
              lowStockRecord == null ||
              !workspace.restockRequestedQuantity
            }
          >
            Create restock task
          </ActionButton>
          <ActionButton
            onClick={() => void workspace.pickRestockTask()}
            disabled={workspace.isBusy || !workspace.actor || !workspace.branchId || !workspace.latestRestockTask || !workspace.restockPickedQuantity}
          >
            Mark task picked
          </ActionButton>
          <ActionButton
            onClick={() => void workspace.completeRestockTask()}
            disabled={workspace.isBusy || !workspace.actor || !workspace.branchId || !workspace.latestRestockTask}
          >
            Complete restock task
          </ActionButton>
          <ActionButton
            onClick={() => void workspace.cancelRestockTask()}
            disabled={workspace.isBusy || !workspace.actor || !workspace.branchId || !workspace.latestRestockTask}
          >
            Cancel restock task
          </ActionButton>
          <ActionButton onClick={() => void workspace.loadRestockBoard()} disabled={workspace.isBusy || !workspace.actor || !workspace.branchId}>
            Refresh restock board
          </ActionButton>
        </div>

        {workspace.latestRestockTask ? (
          <div style={{ marginTop: '16px' }}>
            <h3 style={{ marginBottom: '10px' }}>Latest restock task</h3>
            <DetailList
              items={[
                { label: 'Task number', value: workspace.latestRestockTask.task_number },
                {
                  label: 'Status',
                  value: (
                    <StatusBadge
                      label={workspace.latestRestockTask.status}
                      tone={workspace.latestRestockTask.status === 'COMPLETED' ? 'success' : 'warning'}
                    />
                  ),
                },
                { label: 'Requested quantity', value: String(workspace.latestRestockTask.requested_quantity) },
                {
                  label: 'Picked quantity',
                  value:
                    workspace.latestRestockTask.picked_quantity == null ? 'Not picked yet' : String(workspace.latestRestockTask.picked_quantity),
                },
                { label: 'Source posture', value: workspace.latestRestockTask.source_posture },
                { label: 'Completion note', value: workspace.latestRestockTask.completion_note ?? 'Pending completion' },
              ]}
            />
          </div>
        ) : null}
      </SectionCard>

      <SectionCard eyebrow="Branch restock visibility" title="Restock board">
        <ul style={{ marginBottom: 0, marginTop: 0, color: '#4e5871', lineHeight: 1.7 }}>
          {workspace.restockBoard?.records.length ? (
            workspace.restockBoard.records.map((record) => (
              <li key={record.restock_task_id}>
                {record.product_name} :: {record.status} :: requested {record.requested_quantity} :: picked {record.picked_quantity ?? 0}
              </li>
            ))
          ) : (
            <li>No restock tasks recorded yet.</li>
          )}
        </ul>
      </SectionCard>
    </>
  );
}
