import { ActionButton, DetailList, SectionCard, StatusBadge } from '@store/ui';
import type { OwnerWorkspaceState } from './useOwnerWorkspace';

function isReceiptReady(workspace: OwnerWorkspaceState) {
  return workspace.latestApprovalState?.approval_status === 'APPROVED';
}

export function OwnerReceivingSection({ workspace }: { workspace: OwnerWorkspaceState }) {
  return (
    <>
      <SectionCard eyebrow="Receiving foundation" title="Approved purchase-order receipt">
        <ActionButton
          onClick={() => void workspace.createGoodsReceipt()}
          disabled={workspace.isBusy || !workspace.actor || !workspace.branchId || !workspace.latestPurchaseOrder || !isReceiptReady(workspace)}
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
              ]}
            />
          </div>
        ) : null}

        <ul style={{ marginBottom: 0, marginTop: '16px', color: '#4e5871', lineHeight: 1.7 }}>
          {workspace.goodsReceipts.map((goodsReceipt) => (
            <li key={goodsReceipt.goods_receipt_id}>
              {goodsReceipt.goods_receipt_number} :: {goodsReceipt.received_quantity}
            </li>
          ))}
        </ul>
      </SectionCard>

      <SectionCard eyebrow="Receiving status" title="Receiving board">
        <ul style={{ marginBottom: 0, marginTop: 0, color: '#4e5871', lineHeight: 1.7 }}>
          {workspace.receivingBoard?.records.map((record) => (
            <li key={record.purchase_order_id}>
              {record.purchase_order_number} ::{' '}
              <StatusBadge
                label={record.receiving_status}
                tone={record.receiving_status === 'RECEIVED' ? 'success' : record.receiving_status === 'READY' ? 'warning' : 'neutral'}
              />
            </li>
          )) ?? <li>No approved purchase orders are waiting for receipt.</li>}
        </ul>
      </SectionCard>

      <SectionCard eyebrow="Inventory foundation" title="Inventory snapshot">
        <ul style={{ marginBottom: 0, marginTop: 0, color: '#4e5871', lineHeight: 1.7 }}>
          {workspace.inventorySnapshot.length === 0 ? (
            <li>No branch stock has been received yet.</li>
          ) : (
            workspace.inventorySnapshot.map((record) => (
              <li key={record.product_id}>
                {record.product_name} {'->'} {record.stock_on_hand}
              </li>
            ))
          )}
        </ul>
      </SectionCard>

      <SectionCard eyebrow="Append-only ledger" title="Inventory ledger">
        <ul style={{ marginBottom: 0, marginTop: 0, color: '#4e5871', lineHeight: 1.7 }}>
          {workspace.inventoryLedger.length === 0 ? (
            <li>No inventory movements recorded yet.</li>
          ) : (
            workspace.inventoryLedger.map((record) => (
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
