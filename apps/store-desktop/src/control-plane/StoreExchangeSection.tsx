import { DetailList, FormField, SectionCard, StatusBadge } from '@store/ui';
import type { StoreRuntimeWorkspaceState } from './useStoreRuntimeWorkspace';


export function StoreExchangeSection({ workspace }: { workspace: StoreRuntimeWorkspaceState }) {
  const saleLine = workspace.latestSale?.lines[0] ?? null;

  return (
    <SectionCard eyebrow="Exchange desk" title="Customer exchanges">
      {saleLine ? (
        <>
          <DetailList
            items={[
              { label: 'Original invoice', value: workspace.latestSale?.invoice_number ?? 'Unknown' },
              { label: 'Product', value: saleLine.product_name },
              { label: 'Sold quantity', value: String(saleLine.quantity) },
            ]}
          />

          <div style={{ height: '16px' }} />

          <FormField id="exchange-return-quantity" label="Exchange return quantity" value={workspace.exchangeReturnQuantity} onChange={workspace.setExchangeReturnQuantity} />
          <FormField id="replacement-quantity" label="Replacement quantity" value={workspace.replacementQuantity} onChange={workspace.setReplacementQuantity} />
          <FormField id="exchange-settlement-method" label="Exchange settlement method" value={workspace.exchangeSettlementMethod} onChange={workspace.setExchangeSettlementMethod} />

          <button
            type="button"
            onClick={() => void workspace.createExchange()}
            disabled={workspace.isBusy || !workspace.isSessionLive || !workspace.exchangeReturnQuantity || !workspace.replacementQuantity || !workspace.exchangeSettlementMethod}
            style={{
              border: 0,
              borderRadius: '999px',
              padding: '11px 18px',
              fontSize: '14px',
              fontWeight: 700,
              background:
                workspace.isBusy || !workspace.isSessionLive || !workspace.exchangeReturnQuantity || !workspace.replacementQuantity || !workspace.exchangeSettlementMethod
                  ? '#c5cad7'
                  : '#172033',
              color: '#ffffff',
              cursor:
                workspace.isBusy || !workspace.isSessionLive || !workspace.exchangeReturnQuantity || !workspace.replacementQuantity || !workspace.exchangeSettlementMethod
                  ? 'not-allowed'
                  : 'pointer',
            }}
          >
            Create exchange
          </button>
        </>
      ) : (
        <p style={{ margin: 0, color: '#4e5871' }}>Create a sale invoice first to open the exchange desk for this runtime shell.</p>
      )}

      {workspace.latestExchange ? (
        <div style={{ marginTop: '18px' }}>
          <h3 style={{ marginBottom: '10px' }}>Latest exchange</h3>
          <DetailList
            items={[
              { label: 'Replacement invoice', value: workspace.latestExchange.replacement_sale.invoice_number },
              { label: 'Credit note', value: workspace.latestExchange.sale_return.credit_note.credit_note_number },
              { label: 'Balance', value: `${workspace.latestExchange.balance_direction} ${workspace.latestExchange.balance_amount}` },
              {
                label: 'Status',
                value: <StatusBadge label={workspace.latestExchange.status} tone={workspace.latestExchange.status === 'COMPLETED' ? 'success' : 'warning'} />,
              },
            ]}
          />
        </div>
      ) : null}
    </SectionCard>
  );
}
