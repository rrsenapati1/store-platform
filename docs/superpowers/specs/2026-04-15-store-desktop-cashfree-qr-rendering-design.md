# Store Desktop Cashfree QR Rendering Design

Date: 2026-04-15  
Status: Approved in terminal

## Goal

Upgrade the first `V2-003` Cashfree UPI QR checkout lane so Store Desktop and the customer display render a real scannable QR image with branded payment presentation instead of only printing the raw `upi://...` payload text.

## Why This Slice

- the payment-session backend lane already exists, but the cashier and customer surfaces still expose a developer-grade raw payload instead of a real checkout QR
- this is the missing user-facing piece between “payment session exists” and “customer can actually scan and pay comfortably”
- it stays bounded to presentation/runtime concerns without reopening provider, finalization, or offline-authority semantics

## Scope

### Included

- local QR rendering from the existing `checkoutPaymentSession.qr_payload.value`
- shared desktop/customer-display QR rendering utility
- relative expiry/countdown copy such as `Expires in ...`
- improved QR presentation in cashier billing and customer display

### Explicitly Deferred

- refund flows
- reconciliation/reporting work
- soundbox or terminal hardware integrations
- new payment-provider behavior

## Architecture

Keep QR generation local to `apps/store-desktop`.

- add one shared QR utility/component that converts the current UPI payload into a rendered image
- reuse that component in:
  - `StoreBillingSection.tsx`
  - `customerDisplayRoute.tsx`
- keep the existing payment-session state model untouched
- keep the existing customer-display payload untouched except for how the QR is rendered

This slice is intentionally presentation-first. The authoritative payment workflow remains:

1. backend creates checkout payment session
2. desktop polls session state
3. Cashfree confirmation finalizes the sale

## UX

### Cashier Surface

- show a real QR image with accessible labeling
- keep the relative expiry visible
- still show the raw payload text underneath for fallback/operator support
- keep retry/cancel/manual-fallback actions unchanged

### Customer Display

- show a larger customer-facing QR image
- show a short instruction like `Scan with any UPI app`
- show the relative expiry label
- keep the raw payload in smaller text for last-resort support/debug posture

## Testing

- billing-section regression proving a scannable QR image renders for active Cashfree sessions
- customer-display regression proving a customer-facing QR image renders when payment QR state is active
- full Store Desktop test/typecheck/build verification after implementation

## Success Criteria

- active Cashfree checkout sessions render a real QR image in the cashier UI
- active customer-display QR state renders a real QR image and countdown copy
- no backend payment semantics change
- Store Desktop verification remains green
