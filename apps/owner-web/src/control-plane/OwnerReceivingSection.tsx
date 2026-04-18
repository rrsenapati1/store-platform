import { ActionButton, DetailList, FormField, SectionCard, StatusBadge } from '@store/ui';
import type { OwnerWorkspaceState } from './useOwnerWorkspace';

function isReceiptReady(workspace: OwnerWorkspaceState) {
  return workspace.latestApprovalState?.approval_status === 'APPROVED';
}

function latestReceivingRecord(workspace: OwnerWorkspaceState) {
  if (!workspace.latestPurchaseOrder || !workspace.receivingBoard) {
    return null;
  }
  return workspace.receivingBoard.records.find((record) => record.purchase_order_id === workspace.latestPurchaseOrder?.id) ?? null;
}

function receiptSummary(workspace: OwnerWorkspaceState) {
  const orderedQuantity = workspace.latestPurchaseOrder?.lines.reduce((sum, line) => sum + line.quantity, 0) ?? 0;
  const receivedQuantity = workspace.receivingLineDrafts.reduce((sum, line) => sum + (Number(line.received_quantity) || 0), 0);
  return {
    orderedQuantity,
    receivedQuantity,
    varianceQuantity: Math.max(orderedQuantity - receivedQuantity, 0),
  };
}

function canSubmitReviewedReceipt(workspace: OwnerWorkspaceState) {
  if (!workspace.latestPurchaseOrder || !isReceiptReady(workspace)) {
    return false;
  }
  const record = latestReceivingRecord(workspace);
  if (record && !record.can_receive) {
    return false;
  }
  if (workspace.receivingLineDrafts.length !== workspace.latestPurchaseOrder.lines.length) {
    return false;
  }
  return workspace.receivingLineDrafts.some((line) => (Number(line.received_quantity) || 0) > 0)
    && workspace.receivingLineDrafts.every((line) => {
      const receiptLine = workspace.latestPurchaseOrder?.lines.find((item) => item.product_id === line.product_id);
      if (!receiptLine) {
        return false;
      }
      const receivedQuantity = Number(line.received_quantity);
      return Number.isFinite(receivedQuantity) && receivedQuantity >= 0 && receivedQuantity <= receiptLine.quantity;
    });
}

export function OwnerReceivingSection({ workspace }: { workspace: OwnerWorkspaceState }) {
  const goodsReceipts = workspace.goodsReceipts ?? [];
  const inventorySnapshot = workspace.inventorySnapshot ?? [];
  const inventoryLedger = workspace.inventoryLedger ?? [];
  const receivingBoardRecords = workspace.receivingBoard?.records ?? [];
  const reviewedReceiptSummary = receiptSummary(workspace);
  const boardRecord = latestReceivingRecord(workspace);

  return (
    <>
      <SectionCard eyebrow="Receiving foundation" title="Approved purchase-order receipt">
        {workspace.latestPurchaseOrder ? (
          <DetailList
            items={[
              { label: 'PO number', value: workspace.latestPurchaseOrder.purchase_order_number },
              { label: 'Approval status', value: workspace.latestPurchaseOrder.approval_status },
              { label: 'Ordered quantity', value: String(reviewedReceiptSummary.orderedQuantity) },
              { label: 'Receiving status', value: boardRecord ? boardRecord.receiving_status : 'READY' },
            ]}
          />
        ) : null}

        <div style={{ height: '16px' }} />

        {workspace.latestPurchaseOrder?.lines.map((line) => {
          const reviewedLine = workspace.receivingLineDrafts.find((entry) => entry.product_id === line.product_id);
          const branchCatalogItem = workspace.branchCatalogItems.find((entry) => entry.product_id === line.product_id);
          const isSerialized = branchCatalogItem?.tracking_mode === 'SERIALIZED';
          const receivedQuantity = Number(reviewedLine?.received_quantity ?? line.quantity) || 0;
          const varianceQuantity = Math.max(line.quantity - receivedQuantity, 0);
          return (
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
                {line.sku_code} :: ordered {line.quantity}
              </p>
              <FormField
                id={`receiving-quantity-${line.product_id}`}
                label={`Received quantity for ${line.product_name}`}
                value={reviewedLine?.received_quantity ?? String(line.quantity)}
                onChange={(value) => workspace.setReceivingLineQuantity(line.product_id, value)}
                placeholder={String(line.quantity)}
              />
              <FormField
                id={`receiving-discrepancy-${line.product_id}`}
                label={`Discrepancy note for ${line.product_name}`}
                value={reviewedLine?.discrepancy_note ?? ''}
                onChange={(value) => workspace.setReceivingLineDiscrepancyNote(line.product_id, value)}
                placeholder="Short shipment, damaged cartons, supplier holdback"
              />
              {isSerialized ? (
                <FormField
                  id={`receiving-serial-numbers-${line.product_id}`}
                  label={`Serial / IMEI numbers for ${line.product_name}`}
                  value={reviewedLine?.serial_numbers ?? ''}
                  onChange={(value) => workspace.setReceivingLineSerialNumbers(line.product_id, value)}
                  placeholder="One serial per line or comma separated"
                  multiline
                />
              ) : null}
              <p style={{ margin: 0, color: '#4e5871' }}>Variance: {varianceQuantity}</p>
            </div>
          );
        })}

        <FormField
          id="goods-receipt-note"
          label="Receipt note"
          value={workspace.goodsReceiptNote}
          onChange={workspace.setGoodsReceiptNote}
          placeholder="Optional receiving note"
          multiline
        />

        <DetailList
          items={[
            { label: 'Received quantity', value: String(reviewedReceiptSummary.receivedQuantity) },
            { label: 'Variance quantity', value: String(reviewedReceiptSummary.varianceQuantity) },
          ]}
        />

        <div style={{ height: '16px' }} />

        <ActionButton
          onClick={() => void workspace.createGoodsReceipt()}
          disabled={workspace.isBusy || !workspace.actor || !workspace.branchId || !canSubmitReviewedReceipt(workspace)}
        >
          Create goods receipt
        </ActionButton>

        {workspace.latestGoodsReceipt ? (
          <div style={{ marginTop: '16px' }}>
            <h3 style={{ marginBottom: '10px' }}>Latest goods receipt</h3>
            <DetailList
              items={[
                { label: 'GRN number', value: workspace.latestGoodsReceipt.goods_receipt_number },
                { label: 'Received on', value: workspace.latestGoodsReceipt.received_on },
                { label: 'Line count', value: String(workspace.latestGoodsReceipt.lines.length) },
                { label: 'Received quantity', value: String(workspace.latestGoodsReceipt.received_quantity_total ?? workspace.latestGoodsReceipt.lines.reduce((sum, line) => sum + line.quantity, 0)) },
                {
                  label: 'Variance quantity',
                  value: String(
                    workspace.latestGoodsReceipt.variance_quantity_total
                    ?? workspace.latestGoodsReceipt.lines.reduce(
                      (sum, line) => sum + Math.max((line.variance_quantity ?? Math.max((line.ordered_quantity ?? line.quantity) - line.quantity, 0)), 0),
                      0,
                    ),
                  ),
                },
                { label: 'Receipt note', value: workspace.latestGoodsReceipt.note || 'None' },
                {
                  label: 'Receipt posture',
                  value: (
                    <StatusBadge
                      label={workspace.latestGoodsReceipt.has_discrepancy ? 'RECEIVED_WITH_VARIANCE' : 'RECEIVED'}
                      tone={workspace.latestGoodsReceipt.has_discrepancy ? 'warning' : 'success'}
                    />
                  ),
                },
              ]}
            />
            <ul style={{ marginBottom: 0, marginTop: '12px', color: '#4e5871', lineHeight: 1.7 }}>
              {workspace.latestGoodsReceipt.lines.map((line) => (
                <li key={line.product_id}>
                  {line.product_name} :: received {line.quantity} / ordered {line.ordered_quantity ?? line.quantity} :: variance {line.variance_quantity ?? Math.max((line.ordered_quantity ?? line.quantity) - line.quantity, 0)}
                  {line.discrepancy_note ? ` :: ${line.discrepancy_note}` : ''}
                  {line.serial_numbers?.length ? ` :: serials ${line.serial_numbers.join(', ')}` : ''}
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        <ul style={{ marginBottom: 0, marginTop: '16px', color: '#4e5871', lineHeight: 1.7 }}>
          {goodsReceipts.map((goodsReceipt) => (
            <li key={goodsReceipt.goods_receipt_id}>
              {goodsReceipt.goods_receipt_number} :: {goodsReceipt.received_quantity}
            </li>
          ))}
        </ul>
      </SectionCard>

      <SectionCard eyebrow="Receiving status" title="Receiving board">
        <ul style={{ marginBottom: 0, marginTop: 0, color: '#4e5871', lineHeight: 1.7 }}>
          {receivingBoardRecords.map((record) => (
            <li key={record.purchase_order_id}>
              {record.purchase_order_number} ::{' '}
              <StatusBadge
                label={record.receiving_status}
                tone={record.receiving_status === 'RECEIVED' ? 'success' : record.receiving_status === 'READY' || record.receiving_status === 'RECEIVED_WITH_VARIANCE' ? 'warning' : 'neutral'}
              />
              {record.has_discrepancy ? ` :: variance ${record.variance_quantity}` : ''}
            </li>
          ))}
          {!receivingBoardRecords.length ? <li>No approved purchase orders are waiting for receipt.</li> : null}
        </ul>
      </SectionCard>

      <SectionCard eyebrow="Inventory foundation" title="Inventory snapshot">
        <ul style={{ marginBottom: 0, marginTop: 0, color: '#4e5871', lineHeight: 1.7 }}>
          {inventorySnapshot.length === 0 ? (
            <li>No branch stock has been received yet.</li>
          ) : (
            inventorySnapshot.map((record) => (
              <li key={record.product_id}>
                {record.product_name} {'->'} {record.stock_on_hand}
              </li>
            ))
          )}
        </ul>
      </SectionCard>

      <SectionCard eyebrow="Append-only ledger" title="Inventory ledger">
        <ul style={{ marginBottom: 0, marginTop: 0, color: '#4e5871', lineHeight: 1.7 }}>
          {inventoryLedger.length === 0 ? (
            <li>No inventory movements recorded yet.</li>
          ) : (
            inventoryLedger.map((record) => (
              <li key={record.inventory_ledger_entry_id}>
                {record.product_name} :: {record.entry_type} :: {record.quantity}
              </li>
            ))
          )}
        </ul>
      </SectionCard>
    </>
  );
}
