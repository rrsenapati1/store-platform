import { ActionButton, CommerceSummaryRow, CommerceTotalsBlock, SectionCard, StatusBadge } from '@store/ui';
import type { StoreRuntimeWorkspaceState } from './useStoreRuntimeWorkspace';

function formatCurrency(value: number | null | undefined) {
  return Number(value ?? 0).toFixed(2);
}

function resolveCheckoutStatusTone(status: string | null | undefined): 'success' | 'warning' | 'neutral' {
  if (status === 'FINALIZED') {
    return 'success';
  }
  if (status === 'ACTION_READY' || status === 'PENDING_CUSTOMER_PAYMENT') {
    return 'warning';
  }
  return 'neutral';
}

export function StoreRuntimeSellPaymentPanel({ workspace }: { workspace: StoreRuntimeWorkspaceState }) {
  const checkoutSession = workspace.checkoutPaymentSession;
  const previewSummary = workspace.checkoutPricePreview?.summary;
  const payableAmount = checkoutSession?.order_amount ?? previewSummary?.final_payable_amount ?? previewSummary?.invoice_total ?? 0;
  const latestOfflineSale = workspace.offlineSales?.at(-1) ?? null;
  const showOfflineDraft = workspace.isOfflineContinuityActive && latestOfflineSale !== null;
  const canFinalizeSale = !checkoutSession
    && Boolean(workspace.actor)
    && workspace.isSessionLive
    && Boolean(workspace.activeCashierSession)
    && Boolean(workspace.saleQuantity)
    && Boolean(workspace.branchCatalogItems[0])
    && !workspace.isBusy
    && !workspace.isCheckoutPaymentBusy;

  return (
    <SectionCard eyebrow="Settlement" title="Payment and session">
      <p style={{ marginTop: 0, color: '#4e5871' }}>
        One primary action, one visible session posture.
      </p>
      <div style={{ display: 'grid', gap: '18px' }}>
        <CommerceTotalsBlock title="Payment">
          <CommerceSummaryRow label="Method" value={workspace.paymentMethod} />
          <CommerceSummaryRow label="Payable" value={formatCurrency(payableAmount)} emphasis />
          <CommerceSummaryRow
            label="Checkout session"
            value={
              checkoutSession ? (
                <StatusBadge
                  label={checkoutSession.lifecycle_status}
                  tone={resolveCheckoutStatusTone(checkoutSession.lifecycle_status)}
                />
              ) : 'Not started'
            }
          />
        </CommerceTotalsBlock>

        <CommerceTotalsBlock title="Runtime">
          <CommerceSummaryRow
            label="Cashier session"
            value={workspace.activeCashierSession?.session_number ?? 'Register not open'}
          />
          <CommerceSummaryRow label="Cashier" value={workspace.activeCashierSession?.staff_full_name ?? workspace.actor?.full_name ?? 'Unknown'} />
          <CommerceSummaryRow label="Runtime" value={workspace.runtimeShellLabel ?? 'Resolving runtime'} />
        </CommerceTotalsBlock>

        {showOfflineDraft ? (
          <CommerceTotalsBlock title="Offline continuity">
            <CommerceSummaryRow
              label="Status"
              value={workspace.offlineContinuityMessage || 'Cloud unavailable. Branch continuity mode is active.'}
            />
            <CommerceSummaryRow label="Draft invoice" value={latestOfflineSale.continuity_invoice_number} />
            <CommerceSummaryRow label="Reconciliation" value="Pending reconciliation" />
          </CommerceTotalsBlock>
        ) : null}

        <div style={{ display: 'grid', gap: '10px' }}>
          {checkoutSession ? (
            <>
              <ActionButton
                onClick={() => void workspace.refreshCheckoutPaymentSession?.()}
                disabled={workspace.isCheckoutPaymentBusy || workspace.isBusy}
              >
                Continue payment
              </ActionButton>
              <ActionButton disabled>Finalize sale</ActionButton>
            </>
          ) : (
            <ActionButton
              onClick={() => void workspace.createSalesInvoice?.()}
              disabled={!canFinalizeSale}
            >
              Finalize sale
            </ActionButton>
          )}
        </div>

        {workspace.errorMessage ? (
          <p style={{ margin: 0, color: '#9d2b19' }}>{workspace.errorMessage}</p>
        ) : null}
      </div>
    </SectionCard>
  );
}
