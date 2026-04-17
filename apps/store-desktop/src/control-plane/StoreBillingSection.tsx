import type {
  ControlPlaneCheckoutPaymentSession,
  ControlPlaneCheckoutPricePreview,
  ControlPlaneCheckoutPricePreviewLine,
} from '@store/types';
import { ActionButton, DetailList, FormField, SectionCard, StatusBadge } from '@store/ui';
import { PaymentQrCode, usePaymentQrExpiry } from '../customer-display/paymentQr';
import type { StoreRuntimeWorkspaceState } from './useStoreRuntimeWorkspace';

function isProviderBackedPaymentMethod(paymentMethod: string) {
  return paymentMethod === 'CASHFREE_UPI_QR'
    || paymentMethod === 'CASHFREE_HOSTED_TERMINAL'
    || paymentMethod === 'CASHFREE_HOSTED_PHONE';
}

function describePaymentMethod(paymentMethod: string) {
  if (paymentMethod === 'CASHFREE_UPI_QR') {
    return {
      title: 'Korsenex UPI QR',
      actionLabel: 'Start branded UPI QR',
      helpText: 'Cashfree stays the payment rail while the customer-facing QR remains branded for Store/Korsenex.',
    };
  }
  if (paymentMethod === 'CASHFREE_HOSTED_TERMINAL') {
    return {
      title: 'Cashfree hosted checkout',
      actionLabel: 'Start hosted terminal checkout',
      helpText: 'Open Cashfree hosted checkout on this terminal for cards, wallets, EMI, and other supported methods.',
    };
  }
  if (paymentMethod === 'CASHFREE_HOSTED_PHONE') {
    return {
      title: 'Cashfree hosted checkout',
      actionLabel: 'Start phone checkout link',
      helpText: 'Generate a hosted checkout link for the customer phone while keeping webhook-based sale finalization.',
    };
  }
  return {
    title: 'Manual payment',
    actionLabel: 'Create sales invoice',
    helpText: 'Manual payment methods continue to work during offline continuity or when provider-backed checkout is unavailable.',
  };
}

function CheckoutPaymentActionCard({ checkoutPaymentSession }: { checkoutPaymentSession: ControlPlaneCheckoutPaymentSession }) {
  const expiry = usePaymentQrExpiry(checkoutPaymentSession.qr_expires_at ?? checkoutPaymentSession.action_expires_at ?? null);
  if (checkoutPaymentSession.action_payload.kind === 'upi_qr' && checkoutPaymentSession.qr_payload?.value) {
    return (
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
        <strong style={{ display: 'block' }}>{checkoutPaymentSession.action_payload.label ?? 'Korsenex UPI QR'}</strong>
        <PaymentQrCode
          alt="Cashfree UPI QR code"
          value={checkoutPaymentSession.qr_payload.value}
        />
        <span style={{ fontSize: '14px', color: '#4e5871' }}>{expiry}</span>
        <span style={{ wordBreak: 'break-all', textAlign: 'center' }}>{checkoutPaymentSession.qr_payload.value}</span>
      </div>
    );
  }

  const isPhoneHandoff = checkoutPaymentSession.handoff_surface === 'HOSTED_PHONE';
  return (
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
      }}
    >
      <strong>{checkoutPaymentSession.action_payload.label ?? 'Cashfree hosted checkout'}</strong>
      <span>{checkoutPaymentSession.action_payload.description ?? 'Continue the hosted checkout flow.'}</span>
      <a
        href={checkoutPaymentSession.action_payload.value}
        target="_blank"
        rel="noreferrer"
        style={{ color: '#173a8c', fontWeight: 700, wordBreak: 'break-all' }}
      >
        {checkoutPaymentSession.action_payload.label ?? checkoutPaymentSession.action_payload.value}
      </a>
      <span style={{ fontSize: '14px', color: '#4e5871' }}>{expiry}</span>
      {isPhoneHandoff && checkoutPaymentSession.qr_payload?.value ? (
        <div style={{ display: 'grid', gap: '12px', justifyItems: 'center' }}>
          <PaymentQrCode
            alt="Cashfree UPI QR code"
            value={checkoutPaymentSession.qr_payload.value}
          />
          <span style={{ fontSize: '14px', color: '#4e5871' }}>Scan this on the customer phone to continue hosted checkout.</span>
        </div>
      ) : null}
    </div>
  );
}

function describePreviewLineDiscountSource(
  preview: ControlPlaneCheckoutPricePreview,
  line: ControlPlaneCheckoutPricePreviewLine,
) {
  if (!line.promotion_discount_source) {
    return 'None';
  }
  return line.promotion_discount_source
    .split('+')
    .map((segment) => {
      const trimmedSegment = segment.trim();
      if (trimmedSegment === 'CODE') {
        return preview.promotion_code_campaign?.code ?? trimmedSegment;
      }
      if (trimmedSegment === 'AUTOMATIC_CART' || trimmedSegment === 'AUTOMATIC_ITEM_CATEGORY') {
        return preview.automatic_campaign?.name ?? trimmedSegment;
      }
      if (trimmedSegment === 'ASSIGNED_VOUCHER') {
        return preview.customer_voucher?.voucher_code ?? trimmedSegment;
      }
      return trimmedSegment;
    })
    .join(' + ');
}

export function StoreBillingSection({ workspace }: { workspace: StoreRuntimeWorkspaceState }) {
  const selectedItem = workspace.branchCatalogItems[0];
  const hasSelectedCustomerProfile = workspace.selectedCustomerProfile !== null;
  const selectedCustomerVouchers = workspace.selectedCustomerVouchers;
  const selectedCustomerVoucher = workspace.selectedCustomerVoucher;
  const selectedCustomerStoreCredit = workspace.selectedCustomerStoreCredit;
  const selectedCustomerLoyalty = workspace.selectedCustomerLoyalty;
  const loyaltyProgram = workspace.loyaltyProgram;
  const paymentMethodDescription = describePaymentMethod(workspace.paymentMethod);
  const isDigitalCheckout = isProviderBackedPaymentMethod(workspace.paymentMethod);
  const checkoutPaymentSession = workspace.checkoutPaymentSession;
  const checkoutPaymentTone = checkoutPaymentSession?.lifecycle_status === 'FINALIZED'
    ? 'success'
    : checkoutPaymentSession?.lifecycle_status === 'ACTION_READY'
      || checkoutPaymentSession?.lifecycle_status === 'PENDING_CUSTOMER_PAYMENT'
      ? 'success'
      : 'warning';
  const digitalPaymentTitle = checkoutPaymentSession
    ? (checkoutPaymentSession.handoff_surface === 'BRANDED_UPI_QR' ? 'Korsenex UPI QR' : 'Cashfree hosted checkout')
    : paymentMethodDescription.title;
  const checkoutPromotionDiscountAmount = checkoutPaymentSession?.promotion_discount_amount ?? 0;
  const isCheckoutActionDisabled = workspace.isBusy
    || workspace.isCheckoutPaymentBusy
    || (!workspace.isSessionLive && !workspace.offlineContinuityReady)
    || !workspace.actor
    || !selectedItem
    || !workspace.customerName
    || !workspace.saleQuantity
    || !workspace.paymentMethod
    || (isDigitalCheckout && !workspace.isSessionLive);

  return (
    <>
      <SectionCard eyebrow="Billing foundation" title="Counter checkout">
        <FormField
          id="runtime-customer-profile-search"
          label="Customer profile search"
          value={workspace.customerProfileSearchQuery}
          onChange={workspace.setCustomerProfileSearchQuery}
        />
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginBottom: '14px' }}>
          <ActionButton onClick={() => void workspace.loadCustomerProfiles()} disabled={workspace.isBusy || !workspace.isSessionLive}>
            Find customer profiles
          </ActionButton>
          <ActionButton
            onClick={() => void workspace.createCustomerProfileFromCheckout()}
            disabled={workspace.isBusy || !workspace.isSessionLive || !workspace.customerName.trim()}
          >
            Create customer profile from checkout
          </ActionButton>
          {hasSelectedCustomerProfile ? (
            <ActionButton onClick={() => void workspace.clearSelectedCustomerProfile()} disabled={workspace.isBusy}>
              Use manual customer details
            </ActionButton>
          ) : null}
        </div>
        {workspace.customerProfiles.length ? (
          <ul style={{ marginTop: 0, marginBottom: '16px', color: '#4e5871', lineHeight: 1.7, paddingLeft: '20px' }}>
            {workspace.customerProfiles.map((profile) => (
              <li key={profile.id}>
                <ActionButton onClick={() => workspace.selectCustomerProfile(profile.id)} disabled={workspace.isBusy}>
                  {`Use customer profile ${profile.full_name}`}
                </ActionButton>
              </li>
            ))}
          </ul>
        ) : null}
        {hasSelectedCustomerProfile ? (
          <p style={{ marginTop: 0, marginBottom: '14px', color: '#4e5871' }}>
            Linked customer profile: <strong>{workspace.selectedCustomerProfile?.full_name}</strong>
          </p>
        ) : null}
        {hasSelectedCustomerProfile ? (
          <div style={{ marginBottom: '14px' }}>
            <DetailList
              items={[
                { label: 'Available customer vouchers', value: String(selectedCustomerVouchers.length) },
                {
                  label: 'Selected voucher',
                  value: selectedCustomerVoucher
                    ? `${selectedCustomerVoucher.voucher_name} (${selectedCustomerVoucher.voucher_amount})`
                    : 'None',
                },
              ]}
            />
            {selectedCustomerVouchers.length ? (
              <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginTop: '14px' }}>
                {selectedCustomerVouchers.map((voucher) => (
                  <ActionButton
                    key={voucher.id}
                    onClick={() => workspace.selectCustomerVoucher(voucher.id)}
                    disabled={workspace.isBusy || voucher.status !== 'ACTIVE'}
                  >
                    {`Apply voucher ${voucher.voucher_code}`}
                  </ActionButton>
                ))}
                {selectedCustomerVoucher ? (
                  <ActionButton onClick={() => workspace.clearSelectedCustomerVoucher()} disabled={workspace.isBusy}>
                    Clear customer voucher
                  </ActionButton>
                ) : null}
              </div>
            ) : null}
          </div>
        ) : null}
        {hasSelectedCustomerProfile && selectedCustomerStoreCredit ? (
          <>
            <DetailList
              items={[
                { label: 'Available store credit', value: String(selectedCustomerStoreCredit.available_balance) },
                { label: 'Issued total', value: String(selectedCustomerStoreCredit.issued_total) },
                { label: 'Redeemed total', value: String(selectedCustomerStoreCredit.redeemed_total) },
              ]}
            />
            <div style={{ marginTop: '14px' }}>
              <FormField
                id="runtime-store-credit-amount"
                label="Apply store credit amount"
                value={workspace.storeCreditAmount}
                onChange={workspace.setStoreCreditAmount}
              />
            </div>
          </>
        ) : null}
        {hasSelectedCustomerProfile && selectedCustomerLoyalty ? (
          <>
            <DetailList
              items={[
                { label: 'Available loyalty points', value: String(selectedCustomerLoyalty.available_points) },
                { label: 'Earned loyalty points', value: String(selectedCustomerLoyalty.earned_total) },
                { label: 'Redeemed loyalty points', value: String(selectedCustomerLoyalty.redeemed_total) },
                {
                  label: 'Redemption rule',
                  value: loyaltyProgram
                    ? `${loyaltyProgram.redeem_step_points} pts = ${loyaltyProgram.redeem_value_per_step}`
                    : 'Program unavailable',
                },
                {
                  label: 'Minimum redeem',
                  value: loyaltyProgram ? String(loyaltyProgram.minimum_redeem_points) : 'Program unavailable',
                },
              ]}
            />
            <div style={{ marginTop: '14px' }}>
              <FormField
                id="runtime-loyalty-points"
                label="Redeem loyalty points"
                value={workspace.loyaltyPointsToRedeem}
                onChange={workspace.setLoyaltyPointsToRedeem}
              />
            </div>
          </>
        ) : null}
        <FormField
          id="runtime-promotion-code"
          label="Promotion code"
          value={workspace.promotionCode}
          onChange={workspace.setPromotionCode}
        />
        {workspace.promotionCode ? (
          <div style={{ marginBottom: '14px' }}>
            <ActionButton onClick={() => workspace.clearPromotionCode()} disabled={workspace.isBusy}>
              Clear promotion code
            </ActionButton>
          </div>
        ) : null}
        <FormField
          id="runtime-customer-name"
          label="Customer name"
          value={workspace.customerName}
          onChange={workspace.setCustomerName}
          disabled={hasSelectedCustomerProfile}
        />
        <FormField
          id="runtime-customer-gstin"
          label="Customer GSTIN"
          value={workspace.customerGstin}
          onChange={workspace.setCustomerGstin}
          disabled={hasSelectedCustomerProfile}
        />
        <FormField id="runtime-sale-quantity" label="Sale quantity" value={workspace.saleQuantity} onChange={workspace.setSaleQuantity} />
        <FormField id="runtime-payment-method" label="Payment method" value={workspace.paymentMethod} onChange={workspace.setPaymentMethod} />
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginBottom: '14px' }}>
          {['Cash', 'UPI', 'CASHFREE_UPI_QR', 'CASHFREE_HOSTED_TERMINAL', 'CASHFREE_HOSTED_PHONE'].map((paymentChoice) => (
            <ActionButton key={paymentChoice} onClick={() => workspace.setPaymentMethod(paymentChoice)}>
              {paymentChoice}
            </ActionButton>
          ))}
        </div>
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginBottom: '14px' }}>
          <ActionButton
            onClick={() => void workspace.refreshCheckoutPricePreview()}
            disabled={
              workspace.isBusy
              || !workspace.isSessionLive
              || !workspace.actor
              || !selectedItem
              || !workspace.customerName
              || !workspace.saleQuantity
            }
          >
            Refresh checkout pricing
          </ActionButton>
        </div>
        {workspace.checkoutPricePreviewError ? (
          <p style={{ color: '#9d2b19' }}>{workspace.checkoutPricePreviewError}</p>
        ) : null}
        <ActionButton
          onClick={() => void workspace.createSalesInvoice()}
          disabled={isCheckoutActionDisabled}
        >
          {paymentMethodDescription.actionLabel}
        </ActionButton>
        <p style={{ marginBottom: 0, color: '#4e5871' }}>
          {paymentMethodDescription.helpText}
        </p>
      </SectionCard>

      {workspace.checkoutPricePreview ? (() => {
        const checkoutPricePreview = workspace.checkoutPricePreview;
        return (
          <SectionCard eyebrow="Commercial pricing" title="Checkout pricing">
            <DetailList
              items={[
                {
                  label: 'Automatic campaign',
                  value: checkoutPricePreview.automatic_campaign?.name ?? 'None',
                },
                {
                  label: 'Promotion code',
                  value: checkoutPricePreview.promotion_code_campaign?.code ?? 'None',
                },
                {
                  label: 'Customer voucher',
                  value: checkoutPricePreview.customer_voucher?.voucher_code ?? 'None',
                },
                { label: 'MRP total', value: String(checkoutPricePreview.summary.mrp_total) },
                {
                  label: 'Selling subtotal',
                  value: String(checkoutPricePreview.summary.selling_price_subtotal),
                },
                {
                  label: 'Automatic discount',
                  value: String(checkoutPricePreview.summary.automatic_discount_total),
                },
                {
                  label: 'Code discount',
                  value: String(checkoutPricePreview.summary.promotion_code_discount_total),
                },
                {
                  label: 'Voucher discount',
                  value: String(checkoutPricePreview.summary.customer_voucher_discount_total),
                },
                {
                  label: 'Loyalty discount',
                  value: checkoutPricePreview.summary.loyalty_discount_total.toFixed(2),
                },
                { label: 'Tax total', value: String(checkoutPricePreview.summary.tax_total) },
                {
                  label: 'Invoice total',
                  value: String(checkoutPricePreview.summary.invoice_total),
                },
                {
                  label: 'Store credit used',
                  value: String(checkoutPricePreview.summary.store_credit_amount),
                },
                {
                  label: 'Remaining payable',
                  value: String(checkoutPricePreview.summary.final_payable_amount),
                },
              ]}
            />
            <div style={{ marginTop: '16px', display: 'grid', gap: '16px' }}>
              {checkoutPricePreview.lines.map((line) => (
                <div
                  key={`${line.product_id}-${line.sku_code ?? 'line'}`}
                  style={{
                    borderRadius: '14px',
                    border: '1px solid rgba(23, 32, 51, 0.12)',
                    padding: '14px 16px',
                    background: 'rgba(248, 250, 255, 0.92)',
                    display: 'grid',
                    gap: '8px',
                  }}
                >
                  <strong>{`${line.product_name} x ${line.quantity}`}</strong>
                  <DetailList
                    items={[
                      { label: 'MRP posture', value: `Rs. ${line.mrp.toFixed(2)}` },
                      { label: 'Selling posture', value: `Rs. ${line.unit_selling_price.toFixed(2)}` },
                      {
                        label: 'Discount source',
                        value: describePreviewLineDiscountSource(checkoutPricePreview, line),
                      },
                      { label: 'Line total', value: `Rs. ${line.line_total.toFixed(2)}` },
                    ]}
                  />
                </div>
              ))}
            </div>
          </SectionCard>
        );
      })() : null}

      {isDigitalCheckout || checkoutPaymentSession ? (
        <SectionCard eyebrow="Digital payment" title={digitalPaymentTitle}>
          {checkoutPaymentSession ? (
            <>
              <DetailList
                items={[
                  {
                    label: 'Lifecycle',
                    value: <StatusBadge label={checkoutPaymentSession.lifecycle_status} tone={checkoutPaymentTone} />,
                  },
                  { label: 'Provider order', value: checkoutPaymentSession.provider_order_id },
                  { label: 'Mode', value: checkoutPaymentSession.provider_payment_mode },
                  { label: 'Surface', value: checkoutPaymentSession.handoff_surface },
                  { label: 'Amount', value: `${checkoutPaymentSession.currency_code} ${checkoutPaymentSession.order_amount.toFixed(2)}` },
                  { label: 'Promotion code', value: checkoutPaymentSession.promotion_code ?? 'None' },
                  { label: 'Customer voucher', value: checkoutPaymentSession.customer_voucher_name ?? 'None' },
                  { label: 'Promotion discount', value: checkoutPromotionDiscountAmount.toFixed(2) },
                  { label: 'Voucher discount', value: (checkoutPaymentSession.customer_voucher_discount_total ?? 0).toFixed(2) },
                  { label: 'Recovery', value: checkoutPaymentSession.recovery_state },
                ]}
              />
              {checkoutPaymentSession.lifecycle_status === 'ACTION_READY' || checkoutPaymentSession.lifecycle_status === 'PENDING_CUSTOMER_PAYMENT' ? (
                <p style={{ color: '#4e5871' }}>Waiting for customer payment.</p>
              ) : null}
              {checkoutPaymentSession.lifecycle_status === 'CONFIRMED' ? (
                <p style={{ color: '#9d2b19' }}>
                  Payment is confirmed but the sale is not finalized yet. Finalize it now or refresh the status.
                </p>
              ) : null}
              {checkoutPaymentSession.last_error_message ? (
                <p style={{ color: '#9d2b19' }}>{checkoutPaymentSession.last_error_message}</p>
              ) : null}
              <CheckoutPaymentActionCard checkoutPaymentSession={checkoutPaymentSession} />
              <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginTop: '16px' }}>
                <ActionButton onClick={() => void workspace.refreshCheckoutPaymentSession()} disabled={workspace.isBusy || workspace.isCheckoutPaymentBusy}>
                  Refresh payment status
                </ActionButton>
                {checkoutPaymentSession.recovery_state === 'FINALIZE_REQUIRED' ? (
                  <ActionButton onClick={() => void workspace.finalizeCheckoutPaymentSession()} disabled={workspace.isBusy || workspace.isCheckoutPaymentBusy}>
                    Finalize confirmed payment
                  </ActionButton>
                ) : null}
                {checkoutPaymentSession.recovery_state === 'RETRYABLE' ? (
                  <ActionButton onClick={() => void workspace.retryCheckoutPaymentSession()} disabled={workspace.isBusy || workspace.isCheckoutPaymentBusy}>
                    Retry payment session
                  </ActionButton>
                ) : null}
                {(checkoutPaymentSession.lifecycle_status === 'ACTION_READY'
                  || checkoutPaymentSession.lifecycle_status === 'PENDING_CUSTOMER_PAYMENT') ? (
                    <ActionButton onClick={() => void workspace.cancelCheckoutPaymentSession()} disabled={workspace.isBusy || workspace.isCheckoutPaymentBusy}>
                      Cancel checkout session
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
              Start a Cashfree-backed checkout session to generate a branded QR, terminal checkout, or phone checkout link.
            </p>
          )}
        </SectionCard>
      ) : null}

      {workspace.checkoutPaymentHistory?.length ? (
        <SectionCard eyebrow="Recovery" title="Recent payment sessions">
          <ul style={{ margin: 0, paddingLeft: '20px', display: 'grid', gap: '16px' }}>
            {workspace.checkoutPaymentHistory.map((session) => (
              <li key={session.id} style={{ color: '#4e5871' }}>
                <div style={{ display: 'grid', gap: '8px' }}>
                  <strong style={{ color: '#172033' }}>{session.provider_order_id}</strong>
                  <span>{session.handoff_surface} :: {session.provider_payment_mode} :: {session.lifecycle_status}</span>
                  {session.last_error_message ? <span>{session.last_error_message}</span> : null}
                  <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                    <ActionButton onClick={() => void workspace.refreshCheckoutPaymentSession(session.id)} disabled={workspace.isBusy || workspace.isCheckoutPaymentBusy}>
                      Refresh payment status
                    </ActionButton>
                    {session.recovery_state === 'FINALIZE_REQUIRED' ? (
                      <ActionButton onClick={() => void workspace.finalizeCheckoutPaymentSession(session.id)} disabled={workspace.isBusy || workspace.isCheckoutPaymentBusy}>
                        Finalize confirmed payment
                      </ActionButton>
                    ) : null}
                    {session.recovery_state === 'RETRYABLE' ? (
                      <ActionButton onClick={() => void workspace.retryCheckoutPaymentSession(session.id)} disabled={workspace.isBusy || workspace.isCheckoutPaymentBusy}>
                        Retry payment session
                      </ActionButton>
                    ) : null}
                    {(session.lifecycle_status === 'ACTION_READY' || session.lifecycle_status === 'PENDING_CUSTOMER_PAYMENT') ? (
                      <ActionButton onClick={() => void workspace.cancelCheckoutPaymentSession(session.id)} disabled={workspace.isBusy || workspace.isCheckoutPaymentBusy}>
                        Cancel checkout session
                      </ActionButton>
                    ) : null}
                  </div>
                </div>
              </li>
            ))}
          </ul>
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
