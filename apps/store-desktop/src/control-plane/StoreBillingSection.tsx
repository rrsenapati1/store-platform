import { ActionButton, DetailList, FormField, SectionCard, StatusBadge } from '@store/ui';
import type { StoreRuntimeWorkspaceState } from './useStoreRuntimeWorkspace';

export function StoreBillingSection({ workspace }: { workspace: StoreRuntimeWorkspaceState }) {
  const selectedItem = workspace.branchCatalogItems[0];

  return (
    <>
      <SectionCard eyebrow="Billing foundation" title="Counter checkout">
        <FormField id="runtime-customer-name" label="Customer name" value={workspace.customerName} onChange={workspace.setCustomerName} />
        <FormField id="runtime-customer-gstin" label="Customer GSTIN" value={workspace.customerGstin} onChange={workspace.setCustomerGstin} />
        <FormField id="runtime-sale-quantity" label="Sale quantity" value={workspace.saleQuantity} onChange={workspace.setSaleQuantity} />
        <FormField id="runtime-payment-method" label="Payment method" value={workspace.paymentMethod} onChange={workspace.setPaymentMethod} />
        <ActionButton
          onClick={() => void workspace.createSalesInvoice()}
          disabled={workspace.isBusy || !workspace.isSessionLive || !workspace.actor || !selectedItem || !workspace.customerName || !workspace.saleQuantity || !workspace.paymentMethod}
        >
          Create sales invoice
        </ActionButton>
      </SectionCard>

      <SectionCard eyebrow="Latest invoice" title="Latest sales invoice">
        {workspace.latestSale ? (
          <DetailList
            items={[
              { label: 'Invoice', value: workspace.latestSale.invoice_number },
              { label: 'Kind', value: workspace.latestSale.invoice_kind },
              { label: 'IRN', value: <StatusBadge label={workspace.latestSale.irn_status} tone={workspace.latestSale.irn_status === 'IRN_PENDING' ? 'warning' : 'success'} /> },
              { label: 'Grand total', value: String(workspace.latestSale.grand_total) },
            ]}
          />
        ) : (
          <p style={{ margin: 0, color: '#4e5871' }}>No sales invoice created in this runtime session yet.</p>
        )}
      </SectionCard>

      <SectionCard eyebrow="Sales log" title="Sales register">
        <ul style={{ margin: 0, color: '#4e5871', lineHeight: 1.7 }}>
          {workspace.sales.length ? (
            workspace.sales.map((sale) => (
              <li key={sale.sale_id}>
                {sale.invoice_number} :: {sale.customer_name} :: {sale.payment_method} :: {sale.grand_total}
              </li>
            ))
          ) : (
            <li>No sales invoices posted yet.</li>
          )}
        </ul>
      </SectionCard>

      <SectionCard eyebrow="Branch stock" title="Live inventory snapshot">
        <ul style={{ margin: 0, color: '#4e5871', lineHeight: 1.7 }}>
          {workspace.inventorySnapshot.length ? (
            workspace.inventorySnapshot.map((record) => (
              <li key={record.product_id}>
                {record.product_name} {'->'} {record.stock_on_hand}
              </li>
            ))
          ) : (
            <li>No branch stock loaded yet.</li>
          )}
        </ul>
      </SectionCard>
    </>
  );
}
