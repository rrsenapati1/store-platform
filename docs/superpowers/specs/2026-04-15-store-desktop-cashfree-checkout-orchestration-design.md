# Store Desktop Cashfree Checkout Orchestration Design

Date: 2026-04-15  
Status: Approved in terminal

## Goal

Finish `V2-003` by replacing the current QR-only Cashfree lane with one unified in-store checkout orchestration model that supports:

- branded UPI QR rendered in Store/Korsenex style,
- Cashfree hosted checkout on the terminal/customer display,
- Cashfree hosted checkout handoff to the customer's phone,
- webhook-driven confirmation and sale finalization,
- operator recovery and reconciliation for stuck, expired, or confirmed-but-not-finalized sessions.

## Why This Slice

- the current implementation only supports `CASHFREE_UPI_QR`, which is too narrow for the intended India-first payment experience
- the customer-facing QR should be Store/Korsenex branded rather than a provider-branded concept
- real production closeout for `V2-003` requires broader payment coverage and operator recovery posture, not just happy-path QR creation

## Scope

### Included

- one canonical checkout-payment session model for Cashfree-backed in-store payments
- branded customer UPI QR rendering using provider-backed payment sessions
- hosted checkout handoff for cards, wallets, netbanking, EMI/pay-later, and other Cashfree-supported methods
- cashier choice between terminal-hosted and phone-hosted Cashfree checkout
- webhook plus polling reconciliation
- operator recovery/retry/cancel/finalize actions for incomplete sessions
- customer-display updates for QR, hosted-terminal, and phone-handoff states
- branch-level payment-session history for recent reconciliation

### Explicitly Deferred

- provider-side refund orchestration
- separate card terminal device SDKs
- mobile/tablet payment collection
- split tender
- offline provider payment replay

## Canonical Model

Each checkout payment session has three independent axes:

### Lifecycle

- `CREATED`
- `ACTION_REQUIRED`
- `PENDING_CUSTOMER`
- `CONFIRMED`
- `FAILED`
- `EXPIRED`
- `CANCELED`
- `FINALIZED`

### Handoff Surface

- `BRANDED_UPI_QR`
- `HOSTED_TERMINAL`
- `HOSTED_PHONE`

### Provider Mode

- `cashfree_upi`
- `cashfree_cards`
- `cashfree_netbanking`
- `cashfree_wallets`
- `cashfree_pay_later`
- `cashfree_emi`

Manual payments stay on the existing direct sale path. They are not checkout-payment sessions.

## Backend Architecture

Keep payment authority in the control plane.

### Data Contract Changes

The checkout-payment session must no longer be QR-only. It should store:

- `handoff_surface`
- `provider_payment_mode`
- `action_payload`
  - branded QR payload if applicable
  - hosted checkout URL if applicable
  - phone handoff URL if applicable
- `action_expires_at`
- `last_reconciled_at`
- `recovery_state`

The existing `qr_payload` and `qr_expires_at` fields should be generalized into the new action model, with compatibility preserved in the frontend/client contract only where needed during the migration.

### Provider Boundary

The Cashfree provider adapter should expose a single create method that accepts:

- payment mode
- handoff surface
- order amount
- customer details
- checkout session id

It should return:

- provider ids
- provider status
- action payload
- action expiry
- raw provider response

The provider adapter remains the only layer that knows how to derive branded-QR backing values versus hosted checkout URLs.

### Recovery and Reconciliation

Add bounded service operations for:

- refreshing provider status from provider ids
- finalizing a confirmed session idempotently
- retrying a failed/expired/canceled session by creating a fresh provider action
- listing recent checkout-payment sessions for a branch

Confirmed sessions with no finalized sale should remain recoverable rather than silently stuck.

## Desktop Architecture

Keep `useStoreRuntimeWorkspace.ts` orchestration-focused.

### Hook Boundary

`useStoreRuntimeCheckoutPayment.ts` should become the single desktop payment-session state boundary for:

- session creation
- session polling
- terminal-hosted checkout open state
- phone-handoff copy/open behavior
- recovery actions
- recent payment-session history

`useStoreRuntimeWorkspace.ts` is a mixed-responsibility hotspot over 1200 lines. The payment-specific state and behavior should stay inside the dedicated checkout-payment hook rather than further bloating the workspace entrypoint.

### Billing UI

`StoreBillingSection.tsx` should let the cashier choose:

- manual methods on the old direct sale path
- branded UPI QR
- Cashfree hosted checkout on terminal
- Cashfree hosted checkout on phone

For active sessions it should show:

- lifecycle
- payment mode
- handoff surface
- amount
- expiry
- active branded QR or hosted URL action
- retry/cancel/manual fallback/finalize-now actions where valid

### Customer Display

The customer display model should support:

- branded QR state
- hosted terminal checkout state
- phone handoff state, including a scannable link QR when useful

The customer display remains read-only and terminal-owned.

## Operator Recovery

Add one bounded recent-session view inside the billing section showing recent payment sessions with:

- lifecycle
- provider mode
- handoff surface
- provider order id
- last error
- finalized invoice if present

Allowed actions:

- refresh status
- retry session
- cancel session
- finalize confirmed session

All of these must be audit-recorded on the backend.

## Offline Posture

Provider-backed checkout remains online-only.

When online payment surfaces are unavailable:

- block creation of Cashfree-backed checkout-payment sessions
- keep manual methods usable
- never queue provider payment creation for offline replay

## Testing

### Backend

- create branded UPI QR session returns `handoff_surface = BRANDED_UPI_QR`
- create hosted terminal session returns hosted action payload
- create hosted phone session returns hosted action payload suitable for phone handoff
- confirmed payment finalizes exactly one sale
- confirmed-but-not-finalized session can be explicitly finalized later
- failed/expired/canceled session can be retried into a fresh provider action
- branch history route returns recent sessions

### Desktop

- billing section renders the new payment choices
- branded QR still renders a real QR image
- hosted terminal mode renders terminal action state
- hosted phone mode renders phone handoff action state
- recovery actions call the correct endpoints and update the UI

### Customer Display

- branded QR state renders a customer-facing QR
- hosted terminal state renders hosted-checkout instructions
- phone handoff state renders the phone payment handoff posture

## Success Criteria

- the cashier can start a branded UPI QR or a broader Cashfree hosted checkout from the same checkout system
- customer-facing payment presentation is Store/Korsenex branded where we control the surface
- Cashfree remains the authoritative payment rail and webhook source
- operator recovery and reconciliation exist for incomplete sessions
- `V2-003` is complete once this unified payment orchestration layer is shipped on top of the already-landed cash drawer and weighing scale slices
