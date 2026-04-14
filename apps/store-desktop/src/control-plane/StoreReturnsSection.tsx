import { DetailList, FormField, SectionCard, StatusBadge } from '@store/ui';
import type { StoreRuntimeWorkspaceState } from './useStoreRuntimeWorkspace';


export function StoreReturnsSection({ workspace }: { workspace: StoreRuntimeWorkspaceState }) {
  const saleLine = workspace.latestSale?.lines[0] ?? null;

  return (
    <SectionCard eyebrow="Counter return desk" title="Customer returns">
      {saleLine ? (
        <>
          <DetailList
            items={[
              { label: 'Invoice', value: workspace.latestSale?.invoice_number ?? 'Unknown' },
              { label: 'Product', value: saleLine.product_name },
              { label: 'Sold quantity', value: String(saleLine.quantity) },
            ]}
          />

          <div style={{ height: '16px' }} />

          <FormField id="return-quantity" label="Return quantity" value={workspace.returnQuantity} onChange={workspace.setReturnQuantity} />
          <FormField id="refund-amount" label="Refund amount" value={workspace.refundAmount} onChange={workspace.setRefundAmount} />
          <FormField id="refund-method" label="Refund method" value={workspace.refundMethod} onChange={workspace.setRefundMethod} />

          <button
            type="button"
            onClick={() => void workspace.createSaleReturn()}
            disabled={workspace.isBusy || !workspace.isSessionLive || !workspace.returnQuantity || !workspace.refundAmount || !workspace.refundMethod}
            style={{
              border: 0,
              borderRadius: '999px',
              padding: '11px 18px',
              fontSize: '14px',
              fontWeight: 700,
              background:
                workspace.isBusy || !workspace.isSessionLive || !workspace.returnQuantity || !workspace.refundAmount || !workspace.refundMethod
                  ? '#c5cad7'
                  : '#172033',
              color: '#ffffff',
              cursor:
                workspace.isBusy || !workspace.isSessionLive || !workspace.returnQuantity || !workspace.refundAmount || !workspace.refundMethod
                  ? 'not-allowed'
                  : 'pointer',
            }}
          >
            Create sale return
          </button>
        </>
      ) : (
        <p style={{ margin: 0, color: '#4e5871' }}>Create a sale invoice first to open the return desk for this runtime shell.</p>
      )}

      {workspace.latestSaleReturn ? (
        <div style={{ marginTop: '18px' }}>
          <h3 style={{ marginBottom: '10px' }}>Latest sale return</h3>
          <DetailList
            items={[
              { label: 'Credit note', value: workspace.latestSaleReturn.credit_note.credit_note_number },
              { label: 'Refund', value: `${workspace.latestSaleReturn.refund_method} ${workspace.latestSaleReturn.refund_amount}` },
              {
                label: 'Status',
                value: <StatusBadge label={workspace.latestSaleReturn.status} tone={workspace.latestSaleReturn.status === 'REFUND_APPROVED' ? 'success' : 'warning'} />,
              },
            ]}
          />
        </div>
      ) : null}
    </SectionCard>
  );
}
