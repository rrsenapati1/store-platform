import { ActionButton, DetailList, FormField, SectionCard, StatusBadge } from '@store/ui';
import type { StoreRuntimeWorkspaceState } from './useStoreRuntimeWorkspace';

export function StoreStockCountSection({ workspace }: { workspace: StoreRuntimeWorkspaceState }) {
  const activeSession = workspace.activeStockCountSession;
  const isOpenSession = activeSession?.status === 'OPEN';
  const isCountedSession = activeSession?.status === 'COUNTED';
  const selectedRecord = workspace.stockCountBoard?.records.find(
    (record) => record.product_id === workspace.selectedStockCountProductId,
  ) ?? null;
  const canOpenSession = Boolean(
    workspace.isSessionLive
    && workspace.selectedStockCountProductId
    && (!activeSession || activeSession.status === 'APPROVED' || activeSession.status === 'CANCELED'),
  );

  const activeSessionDetails = activeSession
    ? [
        { label: 'Session number', value: activeSession.session_number },
        {
          label: 'Status',
          value: (
            <StatusBadge
              label={activeSession.status}
              tone={
                activeSession.status === 'APPROVED'
                  ? 'success'
                  : activeSession.status === 'COUNTED'
                    ? 'warning'
                    : 'neutral'
              }
            />
          ),
        },
        ...(activeSession.status === 'OPEN'
          ? [{ label: 'Count note', value: activeSession.note || 'Pending' }]
          : [
              { label: 'Expected quantity', value: String(activeSession.expected_quantity) },
              { label: 'Counted quantity', value: String(activeSession.counted_quantity) },
              { label: 'Variance quantity', value: String(activeSession.variance_quantity) },
              { label: 'Count note', value: activeSession.note || 'Pending' },
              { label: 'Review note', value: activeSession.review_note || 'Pending' },
            ]),
      ]
    : [];

  return (
    <SectionCard eyebrow="Blind count workflow" title="Branch stock count">
      <ActionButton
        onClick={() => void workspace.loadStockCountBoard()}
        disabled={workspace.isBusy || !workspace.isSessionLive || !workspace.branchId}
      >
        Load stock-count board
      </ActionButton>

      <div style={{ marginTop: '16px' }}>
        <h3 style={{ marginBottom: '10px' }}>Stock count board</h3>
        <ul style={{ margin: 0, color: '#4e5871', lineHeight: 1.7 }}>
          {workspace.stockCountBoard?.records.length ? (
            workspace.stockCountBoard.records.map((record) => (
              <li key={record.stock_count_session_id} style={{ marginBottom: '12px' }}>
                <div>
                  {record.session_number} :: {record.product_name} :: {record.status}
                  {record.variance_quantity == null ? '' : ` :: variance ${record.variance_quantity}`}
                </div>
                <div style={{ marginTop: '8px' }}>
                  <ActionButton
                    onClick={() => workspace.setSelectedStockCountProductId(record.product_id)}
                    disabled={workspace.isBusy}
                  >
                    {`Select ${record.product_name}`}
                  </ActionButton>
                </div>
              </li>
            ))
          ) : (
            <li>No stock count sessions recorded yet.</li>
          )}
        </ul>
      </div>

      {selectedRecord ? (
        <div style={{ marginTop: '16px' }}>
          <h3 style={{ marginBottom: '10px' }}>Selected product</h3>
          <DetailList
            items={[
              { label: 'Product', value: selectedRecord.product_name },
              { label: 'SKU', value: selectedRecord.sku_code },
            ]}
          />
        </div>
      ) : null}

      <div style={{ marginTop: '16px' }}>
        <FormField
          id="runtime-stock-count-note"
          label="Count note"
          value={workspace.stockCountNote}
          onChange={workspace.setStockCountNote}
        />
        <ActionButton
          onClick={() => void workspace.createStockCountSession()}
          disabled={workspace.isBusy || !canOpenSession}
        >
          Open stock count session
        </ActionButton>
      </div>

      {activeSession ? (
        <div style={{ marginTop: '16px' }}>
          <h3 style={{ marginBottom: '10px' }}>Latest stock count session</h3>
          <DetailList items={activeSessionDetails} />
        </div>
      ) : null}

      {isOpenSession ? (
        <div style={{ marginTop: '16px' }}>
          <FormField
            id="runtime-stock-count-blind-quantity"
            label="Blind counted quantity"
            value={workspace.blindCountedQuantity}
            onChange={workspace.setBlindCountedQuantity}
          />
          <ActionButton
            onClick={() => void workspace.recordStockCountSession()}
            disabled={workspace.isBusy || !workspace.blindCountedQuantity}
          >
            Record blind count
          </ActionButton>
        </div>
      ) : null}

      {isCountedSession ? (
        <div style={{ marginTop: '16px' }}>
          <h3 style={{ marginBottom: '10px' }}>Review stock count session</h3>
          <FormField
            id="runtime-stock-count-review-note"
            label="Stock-count review note"
            value={workspace.stockCountReviewNote}
            onChange={workspace.setStockCountReviewNote}
          />
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <ActionButton onClick={() => void workspace.approveStockCountSession()} disabled={workspace.isBusy}>
              Approve stock count session
            </ActionButton>
            <ActionButton onClick={() => void workspace.cancelStockCountSession()} disabled={workspace.isBusy}>
              Cancel stock count session
            </ActionButton>
          </div>
        </div>
      ) : null}

      {workspace.latestApprovedStockCount ? (
        <div style={{ marginTop: '16px' }}>
          <h3 style={{ marginBottom: '10px' }}>Latest approved stock count</h3>
          <DetailList
            items={[
              { label: 'Expected', value: String(workspace.latestApprovedStockCount.expected_quantity) },
              { label: 'Counted', value: String(workspace.latestApprovedStockCount.counted_quantity) },
              { label: 'Variance', value: String(workspace.latestApprovedStockCount.variance_quantity) },
              { label: 'Closing stock', value: String(workspace.latestApprovedStockCount.closing_stock) },
            ]}
          />
        </div>
      ) : null}
    </SectionCard>
  );
}
