import { ActionButton, DetailList, FormField, SectionCard, StatusBadge } from '@store/ui';
import type { OwnerWorkspaceState } from './useOwnerWorkspace';

export function OwnerProcurementFinanceSection({ workspace }: { workspace: OwnerWorkspaceState }) {
  return (
    <>
      <SectionCard eyebrow="Procurement finance" title="Supplier billing and settlement">
        <ActionButton
          onClick={() => void workspace.createPurchaseInvoice()}
          disabled={workspace.isBusy || !workspace.actor || !workspace.latestGoodsReceipt}
        >
          Create purchase invoice
        </ActionButton>

        {workspace.latestPurchaseInvoice ? (
          <div style={{ marginTop: '16px' }}>
            <h3 style={{ marginBottom: '10px' }}>Latest purchase invoice</h3>
            <DetailList
              items={[
                { label: 'Invoice number', value: workspace.latestPurchaseInvoice.invoice_number },
                { label: 'Due date', value: workspace.latestPurchaseInvoice.due_date },
                { label: 'Grand total', value: String(workspace.latestPurchaseInvoice.grand_total) },
              ]}
            />
          </div>
        ) : null}

        <div style={{ height: '16px' }} />

        <FormField
          id="supplier-return-quantity"
          label="Supplier return quantity"
          value={workspace.supplierReturnQuantity}
          onChange={workspace.setSupplierReturnQuantity}
        />
        <ActionButton
          onClick={() => void workspace.createSupplierReturn()}
          disabled={workspace.isBusy || !workspace.actor || !workspace.latestPurchaseInvoice || !workspace.supplierReturnQuantity}
        >
          Create supplier return
        </ActionButton>

        {workspace.latestSupplierReturn ? (
          <div style={{ marginTop: '16px' }}>
            <h3 style={{ marginBottom: '10px' }}>Latest supplier return</h3>
            <DetailList
              items={[
                { label: 'Credit note', value: workspace.latestSupplierReturn.supplier_credit_note_number },
                { label: 'Grand total', value: String(workspace.latestSupplierReturn.grand_total) },
                { label: 'Issued on', value: workspace.latestSupplierReturn.issued_on },
              ]}
            />
          </div>
        ) : null}

        <div style={{ height: '16px' }} />

        <FormField
          id="supplier-payment-amount"
          label="Supplier payment amount"
          value={workspace.supplierPaymentAmount}
          onChange={workspace.setSupplierPaymentAmount}
        />
        <FormField
          id="supplier-payment-reference"
          label="Supplier payment reference"
          value={workspace.supplierPaymentReference}
          onChange={workspace.setSupplierPaymentReference}
        />
        <ActionButton
          onClick={() => void workspace.createSupplierPayment()}
          disabled={workspace.isBusy || !workspace.actor || !workspace.latestPurchaseInvoice || !workspace.supplierPaymentAmount}
        >
          Record supplier payment
        </ActionButton>

        {workspace.latestSupplierPayment ? (
          <div style={{ marginTop: '16px' }}>
            <h3 style={{ marginBottom: '10px' }}>Latest supplier payment</h3>
            <DetailList
              items={[
                { label: 'Payment number', value: workspace.latestSupplierPayment.payment_number },
                { label: 'Amount', value: String(workspace.latestSupplierPayment.amount) },
                { label: 'Method', value: workspace.latestSupplierPayment.payment_method },
              ]}
            />
          </div>
        ) : null}
      </SectionCard>

      <SectionCard eyebrow="Supplier finance visibility" title="Supplier payables">
        {workspace.supplierPayablesReport ? (
          <>
            <DetailList
              items={[
                { label: 'Invoiced total', value: String(workspace.supplierPayablesReport.invoiced_total) },
                { label: 'Credit note total', value: String(workspace.supplierPayablesReport.credit_note_total) },
                { label: 'Paid total', value: String(workspace.supplierPayablesReport.paid_total) },
                { label: 'Outstanding total', value: String(workspace.supplierPayablesReport.outstanding_total) },
              ]}
            />
            <ul style={{ marginBottom: 0, marginTop: '16px', color: '#4e5871', lineHeight: 1.7 }}>
              {workspace.supplierPayablesReport.records.map((record) => (
                <li key={record.purchase_invoice_id}>
                  {record.supplier_name} :: {record.purchase_invoice_number} ::{' '}
                  <StatusBadge label={record.settlement_status} tone={record.settlement_status === 'SETTLED' ? 'success' : 'warning'} />
                </li>
              ))}
            </ul>
          </>
        ) : (
          <p style={{ margin: 0, color: '#4e5871' }}>Create a purchase invoice to load the supplier payables view.</p>
        )}
      </SectionCard>
    </>
  );
}
