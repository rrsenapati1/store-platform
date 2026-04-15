import { ActionButton, DetailList, FormField, SectionCard, StatusBadge } from '@store/ui';
import { PaymentQrCode, usePaymentQrExpiry } from '../customer-display/paymentQr';
import type { StoreRuntimeWorkspaceState } from './useStoreRuntimeWorkspace';

export function StoreBillingSection({ workspace }: { workspace: StoreRuntimeWorkspaceState }) {
  const selectedItem = workspace.branchCatalogItems[0];
  const isCashfreeQrPayment = workspace.paymentMethod === 'CASHFREE_UPI_QR';
  const checkoutPaymentSession = workspace.checkoutPaymentSession;
  const isCheckoutTerminalState = checkoutPaymentSession
    && (checkoutPaymentSession.lifecycle_status === 'FAILED'
      || checkoutPaymentSession.lifecycle_status === 'EXPIRED'
      || checkoutPaymentSession.lifecycle_status === 'CANCELED'
      || checkoutPaymentSession.lifecycle_status === 'FINALIZED');
  const checkoutPaymentTone = checkoutPaymentSession?.lifecycle_status === 'FINALIZED'
    ? 'success'
    : isCheckoutTerminalState
      ? 'warning'
      : 'success';
  const isCheckoutActionDisabled = workspace.isBusy
    || workspace.isCheckoutPaymentBusy
    || (!workspace.isSessionLive && !workspace.offlineContinuityReady)
    || !workspace.actor
    || !selectedItem
    || !workspace.customerName
    || !workspace.saleQuantity
    || !workspace.paymentMethod
    || (isCashfreeQrPayment && !workspace.isSessionLive);
  const checkoutPaymentExpiry = usePaymentQrExpiry(checkoutPaymentSession?.qr_expires_at ?? null);

  return (
    <>
      <SectionCard eyebrow="Billing foundation" title="Counter checkout">
        <FormField id="runtime-customer-name" label="Customer name" value={workspace.customerName} onChange={workspace.setCustomerName} />
        <FormField id="runtime-customer-gstin" label="Customer GSTIN" value={workspace.customerGstin} onChange={workspace.setCustomerGstin} />
        <FormField id="runtime-sale-quantity" label="Sale quantity" value={workspace.saleQuantity} onChange={workspace.setSaleQuantity} />
        <FormField id="runtime-payment-method" label="Payment method" value={workspace.paymentMethod} onChange={workspace.setPaymentMethod} />
        <ActionButton
          onClick={() => void workspace.createSalesInvoice()}
          disabled={isCheckoutActionDisabled}
        >
          {isCashfreeQrPayment ? 'Start Cashfree UPI QR' : 'Create sales invoice'}
        </ActionButton>
        {isCashfreeQrPayment ? (
          <p style={{ marginBottom: 0, color: '#4e5871' }}>
            Cashfree QR stays online-only. If branch continuity is offline, switch to a manual payment method instead of starting a QR session.
          </p>
        ) : null}
      </SectionCard>

      {isCashfreeQrPayment || checkoutPaymentSession ? (
        <SectionCard eyebrow="Digital payment" title="Cashfree UPI QR payment">
          {checkoutPaymentSession ? (
            <>
              <DetailList
                items={[
                  {
                    label: 'Lifecycle',
                    value: <StatusBadge label={checkoutPaymentSession.lifecycle_status} tone={checkoutPaymentTone} />,
                  },
                  { label: 'Provider order', value: checkoutPaymentSession.provider_order_id },
                  { label: 'Amount', value: `${checkoutPaymentSession.currency_code} ${checkoutPaymentSession.order_amount.toFixed(2)}` },
                  { label: 'QR expires at', value: checkoutPaymentSession.qr_expires_at ?? 'Unknown' },
                ]}
              />
              {(checkoutPaymentSession.lifecycle_status === 'QR_READY' || checkoutPaymentSession.lifecycle_status === 'PENDING_CUSTOMER_PAYMENT') ? (
                <p style={{ color: '#4e5871' }}>Waiting for customer payment</p>
              ) : null}
              {checkoutPaymentSession.lifecycle_status === 'CONFIRMED' ? (
                <p style={{ color: '#4e5871' }}>Payment confirmed. Finalizing the sale now.</p>
              ) : null}
              {(checkoutPaymentSession.lifecycle_status === 'FAILED' || checkoutPaymentSession.lifecycle_status === 'EXPIRED') ? (
                <p style={{ color: '#9d2b19' }}>The QR payment attempt did not complete. Retry it or switch to a manual payment method.</p>
              ) : null}
              {checkoutPaymentSession.lifecycle_status === 'CANCELED' ? (
                <p style={{ color: '#4e5871' }}>This QR attempt was canceled. You can retry it or continue with a manual payment method.</p>
              ) : null}
              {checkoutPaymentSession.qr_payload?.value ? (
                <div
                  style={{
                    marginTop: '16px',
                    borderRadius: '16px',
                    border: '1px solid rgba(23, 32, 51, 0.12)',
                    padding: '16px',
                    background: 'rgba(244, 247, 255, 0.9)',
                    color: '#25314f',
                    display: 'grid',
                    gap: '14px',
                    justifyItems: 'center',
                  }}
                >
                  <strong style={{ display: 'block' }}>Cashfree UPI QR</strong>
                  <PaymentQrCode
                    alt="Cashfree UPI QR code"
                    value={checkoutPaymentSession.qr_payload.value}
                  />
                  <span style={{ fontSize: '14px', color: '#4e5871' }}>{checkoutPaymentExpiry}</span>
                  <span style={{ wordBreak: 'break-all', textAlign: 'center' }}>{checkoutPaymentSession.qr_payload.value}</span>
                </div>
              ) : null}
              <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginTop: '16px' }}>
                {(checkoutPaymentSession.lifecycle_status === 'FAILED'
                  || checkoutPaymentSession.lifecycle_status === 'EXPIRED'
                  || checkoutPaymentSession.lifecycle_status === 'CANCELED') ? (
                    <ActionButton onClick={() => void workspace.retryCheckoutPaymentSession()} disabled={workspace.isBusy || workspace.isCheckoutPaymentBusy}>
                      Retry Cashfree UPI QR
                    </ActionButton>
                  ) : null}
                {(checkoutPaymentSession.lifecycle_status === 'QR_READY'
                  || checkoutPaymentSession.lifecycle_status === 'PENDING_CUSTOMER_PAYMENT') ? (
                    <ActionButton onClick={() => void workspace.cancelCheckoutPaymentSession()} disabled={workspace.isBusy || workspace.isCheckoutPaymentBusy}>
                      Cancel QR payment
                    </ActionButton>
                  ) : null}
                {checkoutPaymentSession.lifecycle_status !== 'FINALIZED' ? (
                  <ActionButton onClick={() => void workspace.useManualCheckoutFallback()} disabled={workspace.isBusy || workspace.isCheckoutPaymentBusy}>
                    Switch to manual payment
                  </ActionButton>
                ) : null}
              </div>
            </>
          ) : (
            <p style={{ margin: 0, color: '#4e5871' }}>
              Start a Cashfree QR payment to generate a dynamic UPI payload for the cashier and customer display.
            </p>
          )}
        </SectionCard>
      ) : null}

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
