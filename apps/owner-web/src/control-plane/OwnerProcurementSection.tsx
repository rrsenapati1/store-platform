import { ActionButton, DetailList, FormField, SectionCard, StatusBadge } from '@store/ui';
import type { OwnerWorkspaceState } from './useOwnerWorkspace';

export function OwnerProcurementSection({ workspace }: { workspace: OwnerWorkspaceState }) {
  return (
    <>
      <SectionCard eyebrow="Supplier foundation" title="Supplier master bootstrap">
        <FormField id="supplier-name" label="Supplier name" value={workspace.supplierName} onChange={workspace.setSupplierName} />
        <FormField id="supplier-gstin" label="Supplier GSTIN" value={workspace.supplierGstin} onChange={workspace.setSupplierGstin} />
        <FormField
          id="supplier-payment-terms-days"
          label="Payment terms (days)"
          value={workspace.supplierPaymentTermsDays}
          onChange={workspace.setSupplierPaymentTermsDays}
        />
        <ActionButton
          onClick={() => void workspace.createSupplier()}
          disabled={workspace.isBusy || !workspace.actor || !workspace.supplierName}
        >
          Create supplier
        </ActionButton>

        {workspace.latestSupplier ? (
          <div style={{ marginTop: '16px' }}>
            <h3 style={{ marginBottom: '10px' }}>Latest supplier</h3>
            <DetailList
              items={[
                { label: 'Name', value: workspace.latestSupplier.name },
                { label: 'GSTIN', value: workspace.latestSupplier.gstin ?? 'Not set' },
                { label: 'Terms', value: `${workspace.latestSupplier.payment_terms_days} days` },
              ]}
            />
          </div>
        ) : null}

        <ul style={{ marginBottom: 0, marginTop: '16px', color: '#4e5871', lineHeight: 1.7 }}>
          {workspace.suppliers.map((supplier) => (
            <li key={supplier.supplier_id}>{supplier.name}</li>
          ))}
        </ul>
      </SectionCard>

      <SectionCard eyebrow="Procurement foundation" title="Purchase-order approval bootstrap">
        <FormField id="purchase-quantity" label="Purchase quantity" value={workspace.purchaseQuantity} onChange={workspace.setPurchaseQuantity} />
        <FormField id="purchase-unit-cost" label="Unit cost" value={workspace.purchaseUnitCost} onChange={workspace.setPurchaseUnitCost} />
        <ActionButton
          onClick={() => void workspace.createPurchaseOrder()}
          disabled={
            workspace.isBusy ||
            !workspace.actor ||
            !workspace.branchId ||
            workspace.suppliers.length === 0 ||
            workspace.catalogProducts.length === 0 ||
            !workspace.purchaseQuantity ||
            !workspace.purchaseUnitCost
          }
        >
          Create purchase order
        </ActionButton>

        {workspace.latestPurchaseOrder ? (
          <div style={{ marginTop: '16px' }}>
            <h3 style={{ marginBottom: '10px' }}>Latest purchase order</h3>
            <DetailList
              items={[
                { label: 'PO number', value: workspace.latestPurchaseOrder.purchase_order_number },
                { label: 'Status', value: <StatusBadge label={workspace.latestPurchaseOrder.approval_status} tone="warning" /> },
                { label: 'Grand total', value: String(workspace.latestPurchaseOrder.grand_total) },
              ]}
            />
          </div>
        ) : null}

        <div style={{ height: '16px' }} />

        <FormField id="approval-note" label="Approval note" value={workspace.approvalNote} onChange={workspace.setApprovalNote} />
        <ActionButton
          onClick={() => void workspace.submitPurchaseOrder()}
          disabled={workspace.isBusy || !workspace.actor || !workspace.latestPurchaseOrder || !workspace.approvalNote}
        >
          Submit approval
        </ActionButton>

        <div style={{ height: '16px' }} />

        <FormField id="decision-note" label="Decision note" value={workspace.decisionNote} onChange={workspace.setDecisionNote} />
        <ActionButton
          onClick={() => void workspace.approvePurchaseOrder()}
          disabled={workspace.isBusy || !workspace.actor || !workspace.latestPurchaseOrder || !workspace.decisionNote}
        >
          Approve purchase order
        </ActionButton>

        {workspace.latestApprovalState ? (
          <div style={{ marginTop: '16px' }}>
            <h3 style={{ marginBottom: '10px' }}>Latest approval state</h3>
            <DetailList
              items={[
                { label: 'Supplier', value: workspace.latestApprovalState.supplier_name },
                { label: 'Status', value: <StatusBadge label={workspace.latestApprovalState.approval_status} tone={workspace.latestApprovalState.approval_status === 'APPROVED' ? 'success' : 'warning'} /> },
                { label: 'Quantity', value: String(workspace.latestApprovalState.ordered_quantity) },
              ]}
            />
          </div>
        ) : null}

        <ul style={{ marginBottom: 0, marginTop: '16px', color: '#4e5871', lineHeight: 1.7 }}>
          {workspace.purchaseOrders.map((purchaseOrder) => (
            <li key={purchaseOrder.purchase_order_id}>
              {purchaseOrder.supplier_name} :: {purchaseOrder.approval_status}
            </li>
          ))}
        </ul>
      </SectionCard>
    </>
  );
}
