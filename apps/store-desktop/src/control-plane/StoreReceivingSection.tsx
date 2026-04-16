import { ActionButton, DetailList, FormField, SectionCard, StatusBadge } from '@store/ui';
import type { StoreRuntimeWorkspaceState } from './useStoreRuntimeWorkspace';

function canCreateGoodsReceipt(workspace: StoreRuntimeWorkspaceState) {
  if (!workspace.selectedReceivingPurchaseOrder || workspace.receivingLineDrafts.length === 0) {
    return false;
  }
  return workspace.receivingLineDrafts.some((line) => {
    const receivedQuantity = Number(line.received_quantity);
    return Number.isFinite(receivedQuantity) && receivedQuantity > 0;
  });
}

export function StoreReceivingSection({ workspace }: { workspace: StoreRuntimeWorkspaceState }) {
  const selectedPurchaseOrder = workspace.selectedReceivingPurchaseOrder;
  const createDisabled = workspace.isBusy
    || !workspace.isSessionLive
    || !workspace.branchId
    || !canCreateGoodsReceipt(workspace);

  return (
    <SectionCard eyebrow="Reviewed receiving workflow" title="Branch receiving">
      <ActionButton
        onClick={() => void workspace.loadReceivingBoard()}
        disabled={workspace.isBusy || !workspace.isSessionLive || !workspace.branchId}
      >
        Load receiving board
      </ActionButton>

      <div style={{ marginTop: '16px' }}>
        <h3 style={{ marginBottom: '10px' }}>Reviewed receiving board</h3>
        <ul style={{ margin: 0, color: '#4e5871', lineHeight: 1.7 }}>
          {workspace.receivingBoard?.records.length ? (
            workspace.receivingBoard.records.map((record) => (
              <li key={record.purchase_order_id} style={{ marginBottom: '12px' }}>
                <div>
                  {record.purchase_order_number} :: {record.supplier_name} ::{' '}
                  <StatusBadge
                    label={record.receiving_status}
                    tone={
                      record.receiving_status === 'RECEIVED'
                        ? 'success'
                        : record.receiving_status === 'READY' || record.receiving_status === 'RECEIVED_WITH_VARIANCE'
                          ? 'warning'
                          : 'neutral'
                    }
                  />
                  {record.has_discrepancy ? ` :: variance ${record.variance_quantity}` : ''}
                </div>
                <div style={{ marginTop: '8px' }}>
                  <ActionButton
                    onClick={() => void workspace.selectReceivingPurchaseOrder(record.purchase_order_id)}
                    disabled={workspace.isBusy || !record.can_receive}
                  >
                    {`Select ${record.purchase_order_number}`}
                  </ActionButton>
                </div>
              </li>
            ))
          ) : (
            <li>No approved purchase orders are waiting for reviewed receipt.</li>
          )}
        </ul>
      </div>

      {selectedPurchaseOrder ? (
        <div style={{ marginTop: '16px' }}>
          <h3 style={{ marginBottom: '10px' }}>Selected purchase order</h3>
          <DetailList
            items={[
              { label: 'PO number', value: selectedPurchaseOrder.purchase_order_number },
              { label: 'Approval status', value: selectedPurchaseOrder.approval_status },
              { label: 'Line count', value: String(selectedPurchaseOrder.lines.length) },
            ]}
          />
        </div>
      ) : null}

      {workspace.receivingLineDrafts.length ? (
        <div style={{ marginTop: '16px' }}>
          {workspace.receivingLineDrafts.map((line) => (
            <div
              key={line.product_id}
              style={{
                border: '1px solid rgba(23,32,51,0.08)',
                borderRadius: '16px',
                marginBottom: '14px',
                padding: '14px',
              }}
            >
              <p style={{ margin: '0 0 6px', fontWeight: 700 }}>{line.product_name}</p>
              <p style={{ margin: '0 0 12px', color: '#4e5871' }}>
                {line.sku_code} :: ordered {line.ordered_quantity}
              </p>
              <FormField
                id={`runtime-receiving-quantity-${line.product_id}`}
                label={`Received quantity for ${line.product_name}`}
                value={line.received_quantity}
                onChange={(value) => workspace.setReceivingLineQuantity(line.product_id, value)}
                placeholder={String(line.ordered_quantity)}
              />
              <FormField
                id={`runtime-receiving-discrepancy-${line.product_id}`}
                label={`Discrepancy note for ${line.product_name}`}
                value={line.discrepancy_note}
                onChange={(value) => workspace.setReceivingLineDiscrepancyNote(line.product_id, value)}
                placeholder="Short shipment, damaged cartons, supplier holdback"
              />
            </div>
          ))}
        </div>
      ) : null}

      <div style={{ marginTop: '16px' }}>
        <FormField
          id="runtime-goods-receipt-note"
          label="Receipt note"
          value={workspace.goodsReceiptNote}
          onChange={workspace.setGoodsReceiptNote}
          placeholder="Optional receiving note"
          multiline
        />
        <ActionButton onClick={() => void workspace.createGoodsReceipt()} disabled={createDisabled}>
          Create goods receipt
        </ActionButton>
      </div>

      {workspace.latestGoodsReceipt ? (
        <div style={{ marginTop: '16px' }}>
          <h3 style={{ marginBottom: '10px' }}>Latest goods receipt</h3>
          <DetailList
            items={[
              { label: 'GRN number', value: workspace.latestGoodsReceipt.goods_receipt_number },
              { label: 'Received on', value: workspace.latestGoodsReceipt.received_on },
              { label: 'Received quantity', value: String(workspace.latestGoodsReceipt.received_quantity_total) },
              { label: 'Variance quantity', value: String(workspace.latestGoodsReceipt.variance_quantity_total) },
              { label: 'Receipt note', value: workspace.latestGoodsReceipt.note || 'None' },
            ]}
          />
        </div>
      ) : null}
    </SectionCard>
  );
}
