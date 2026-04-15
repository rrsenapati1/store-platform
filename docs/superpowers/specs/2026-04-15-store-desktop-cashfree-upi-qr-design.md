# Store Desktop Cashfree UPI QR Design

Date: 2026-04-15  
Status: Approved in terminal

## Goal

Land the final `V2-003` payment slice as a packaged `Store Desktop` Cashfree dynamic UPI QR checkout flow that creates a payment session first, confirms payment through Cashfree, and only then finalizes the sale, invoice, and stock movement.

## Why This Slice

- it completes the first production in-store payment lane for `V2-003` without pretending generic terminal hardware exists before a real provider path does
- it fits the India-first rollout by using dynamic UPI QR instead of card terminals or a fake cashier-confirmed payment simulation
- it preserves accounting and inventory correctness by refusing to create real sales for abandoned or expired QR attempts

## Scope

### Included

- control-plane-backed checkout payment sessions for branch sales
- Cashfree order creation and order-pay flow for UPI `qrcode`
- packaged `Store Desktop` QR checkout UI
- payment status polling and webhook ingestion
- idempotent sale finalization only after confirmed payment
- customer-display QR and payment-status rendering
- offline continuity fallback to manual payment methods only

### Explicitly Deferred

- card terminals or POS device SDKs
- soundbox integrations
- split-tender QR flows
- provider-driven refunds
- mobile/tablet payment collection
- payment-led offline authority

## Cashfree Boundary

The control plane should own the provider integration. `Store Desktop` must not call Cashfree directly.

The provider flow is:

1. create a Cashfree order from the backend
2. create an order-pay session using UPI `qrcode`
3. persist the canonical checkout payment session locally in the control plane
4. render the QR payload on desktop/customer display
5. reconcile status through webhook plus polling
6. finalize the sale exactly once after provider confirmation

Official Cashfree references used for this slice:

- Create Order API: `POST /pg/orders` returns `payment_session_id`  
  Source: [Cashfree Create Order](https://www.cashfree.com/docs/api-reference/payments/latest/orders/create)
- Order Pay API: `POST /pg/orders/sessions` supports UPI with `channel = qrcode`  
  Source: [Cashfree Order Pay](https://www.cashfree.com/docs/api-reference/payments/latest/payments/pay)
- Get Payments for an Order: `GET /pg/orders/{order_id}/payments` exposes payment status and provider payment records  
  Source: [Cashfree Get Payments for an Order](https://www.cashfree.com/docs/api-reference/payments/latest/payments/get-payments-for-order)
- Payment webhooks and signature verification  
  Sources: [Cashfree Payment Webhooks](https://www.cashfree.com/docs/api-reference/payments/latest/payments/webhooks), [Cashfree Webhook Signature Verification](https://www.cashfree.com/docs/payments/webhooks)

Important implementation note:

- the official docs clearly support UPI `qrcode`, but the latest reference pages do not show a concrete QR response example for Order Pay
- because of that, the implementation should persist the raw provider response and derive `qr_payload` from provider fields defensively
- deriving QR content from `data.url` or provider QR fields is an inference from the docs and should be isolated inside the provider adapter

## Architecture

Add a new in-store payments boundary under billing instead of overloading the existing one-step sale route.

### Control Plane

Add a dedicated checkout payment-session module:

- `CheckoutPaymentSession`
  - branch/device/operator/cart context
  - current provider status
  - current lifecycle status
  - current QR payload
  - expiry
  - raw provider refs
  - finalized sale id when complete
- provider adapter for `Cashfree`
  - create provider order
  - create QR payment session
  - fetch payment status
  - verify webhook signature
  - normalize provider events
- finalization service
  - creates the sale only after provider confirmation
  - must be idempotent
  - must not duplicate inventory ledger writes

### Store Desktop

Replace the direct QR-as-payment-method billing path with:

1. build cart
2. choose `Cashfree UPI QR`
3. request checkout payment session
4. render QR and countdown
5. poll session status
6. when confirmed, fetch finalized sale state
7. allow retry/cancel/switch-to-manual on failure or expiry

Desktop must still allow manual payment methods like `Cash` and manual `UPI` so offline continuity remains usable.

### Customer Display

Extend the current customer-display model with a QR-payment posture:

- total due
- QR payload
- expiry/countdown
- pending/paid/expired status

The customer display remains read-only and terminal-owned.

## Canonical State Model

Add one canonical checkout payment session lifecycle:

- `CREATED`
- `QR_READY`
- `PENDING_CUSTOMER_PAYMENT`
- `CONFIRMED`
- `FAILED`
- `EXPIRED`
- `CANCELED`
- `FINALIZED`

Rules:

- `CONFIRMED` means Cashfree reported payment success
- `FINALIZED` means the store sale was created from that confirmed payment
- only one sale may be finalized from one confirmed payment session
- failed/expired/canceled sessions must never create sales

## Data Model

Add a new control-plane table for branch checkout payment sessions with fields like:

- `id`
- `tenant_id`
- `branch_id`
- `device_id`
- `actor_user_id`
- `provider_name`
- `provider_order_id`
- `provider_payment_session_id`
- `provider_payment_id`
- `provider_status`
- `lifecycle_status`
- `order_amount`
- `currency_code`
- `payment_method`
- `cart_summary_hash`
- `cart_snapshot`
- `customer_name`
- `customer_gstin`
- `qr_payload`
- `qr_expires_at`
- `provider_response_payload`
- `confirmed_at`
- `failed_at`
- `expired_at`
- `finalized_sale_id`
- `finalized_at`

The sale itself remains in the existing sales tables. This slice adds a payment-session precursor, not a replacement sale model.

## API Surface

Add bounded routes under branch billing:

- `POST /v1/tenants/{tenant_id}/branches/{branch_id}/checkout-payment-sessions`
  - creates a new checkout payment session for the current cart
- `GET /v1/tenants/{tenant_id}/branches/{branch_id}/checkout-payment-sessions/{session_id}`
  - reads current status and finalized sale if present
- `POST /v1/tenants/{tenant_id}/branches/{branch_id}/checkout-payment-sessions/{session_id}/cancel`
  - operator abandonment
- `POST /v1/billing/webhooks/cashfree/payments`
  - provider webhook ingress

The existing `POST /sales` route should remain for manual payment paths. Cashfree QR should use the new session flow, not the old direct sale path.

## Finalization Rules

Finalization must be idempotent.

Recommended rule:

- if a session is already `FINALIZED`, return the existing sale
- if a session is `CONFIRMED` and not finalized, create the sale and mark the session `FINALIZED` in the same transaction boundary
- if a session is not `CONFIRMED`, reject finalization

This prevents duplicate sales from:

- repeated desktop polling
- duplicate webhook delivery
- operator refresh/retry behavior

## Offline Continuity

Cashfree QR is online-only.

When the control plane or provider lane is unavailable:

- block `Cashfree UPI QR`
- surface an operator message explaining that QR needs online connectivity
- allow manual methods such as `Cash` or manual `UPI`
- preserve the existing offline sale path only for those manual methods

No offline replay should ever attempt to recreate a Cashfree QR session.

## UI Surfaces

### Store Billing Section

Add explicit QR payment flow states:

- ready to start QR
- QR active
- waiting for customer payment
- confirmed/finalizing
- finalized
- failed
- expired
- canceled

Actions:

- start QR payment
- retry QR
- cancel QR
- switch to manual payment

### Customer Display

Show:

- total due
- QR
- countdown/status
- success state after confirmation

### Runtime Diagnostics

Expose payment-session posture in the packaged runtime:

- provider configured/unconfigured
- active QR session
- latest provider status
- latest payment error

This should live beside the existing hardware/runtime posture, not in a separate product area.

## Error Handling

Primary failure classes:

- provider config missing
- Cashfree order creation failed
- QR generation failed
- webhook signature invalid
- payment expired
- payment failed
- finalization failed after confirmation

Rules:

- provider errors should not create a sale
- signature failure should reject webhook processing and log an operator-visible error
- finalization failure after confirmation should leave the session in a recoverable `CONFIRMED`-but-not-finalized posture for idempotent retry

## Testing

### Backend

- create payment session returns QR-ready payload
- webhook verification rejects bad signatures
- confirmed payment finalizes exactly one sale
- repeated finalization attempts remain idempotent
- failed/expired sessions do not create sales
- manual sale route still works

### Desktop

- billing UI enters QR-payment flow
- QR-confirmed flow ends in finalized sale
- expired/failed session offers retry or manual fallback
- offline continuity blocks QR and keeps manual methods

### Customer Display

- QR payment state renders total/QR/countdown
- confirmed payment transitions to success

## Success Criteria

- Store Desktop can start a Cashfree dynamic UPI QR payment for an online checkout
- the customer display can show the active QR payment state
- confirmed Cashfree payments create exactly one sale/invoice and one stock decrement path
- failed or expired QR attempts never create sales
- offline continuity remains manual-only for payment methods and does not attempt provider QR replay
