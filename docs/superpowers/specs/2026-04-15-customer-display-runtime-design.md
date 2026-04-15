# Customer Display Runtime Design

Date: 2026-04-15  
Owner: Codex  
Status: Draft

## Goal

Land the first `customer display` slice for `V2-001` as a read-only, customer-facing second-window experience owned by the active Store Desktop cashier terminal.

## Product Decision

The first customer-display runtime will:

- live inside `apps/store-desktop`
- be launched and owned by the active cashier runtime
- render in a second window for packaged desktop
- fall back to a same-machine secondary window in development and tests
- remain read-only with no separate auth or session lifecycle

This slice does **not** create a separate paired spoke device yet.

## Scope

Included:

- customer-display payload model
- customer-display React route/view
- cashier-side controller for opening, closing, and updating the display
- native packaged-runtime window management for customer display
- read-only display states:
  - `idle`
  - `active_cart`
  - `payment_in_progress`
  - `sale_complete`
  - `unavailable`
- browser-safe fallback posture for development/tests

Deferred:

- separate paired `customer_display` device lifecycle
- customer-side input or interaction authority
- second-monitor targeting heuristics beyond a bounded packaged runtime window
- payment-terminal-driven display animations or branded media loops

## Architecture

Customer display stays subordinate to the cashier terminal.

- `useStoreRuntimeWorkspace` remains the source of truth for sale state
- a new customer-display controller derives a small serialized view model from cashier state
- the display window only renders that payload
- the display never writes checkout state or calls control-plane mutations directly

The packaged desktop shell should expose a minimal command boundary for:

- open customer display window
- close customer display window

The React app should decide whether to render the main cashier workspace or the display route based on a route/query marker so the same bundle can serve both windows.

## UX States

### Idle

- branded waiting posture
- “Ready for next customer” style message
- no operator or runtime details

### Active Cart

- line items
- quantities
- line prices
- subtotal
- discount total when present
- tax total
- grand total

### Payment In Progress

- active cart content remains visible
- total due stays prominent
- status copy like “Processing payment”

### Sale Complete

- success/thank-you posture
- grand total
- amount paid
- change due for cash when applicable

### Unavailable

- bounded error posture if the display is open but no payload can be resolved

## Data Model

The display payload should stay intentionally small.

Recommended fields:

- `state`
- `title`
- `message`
- `currency_code`
- `line_items[]`
  - `label`
  - `quantity`
  - `amount`
- `subtotal`
- `discount_total`
- `tax_total`
- `grand_total`
- `cash_received`
- `change_due`
- `updated_at`

This payload should be derived in the cashier app, not rebuilt independently in the display window.

## File Structure

Frontend:

- `apps/store-desktop/src/customer-display/customerDisplayModel.ts`
- `apps/store-desktop/src/customer-display/customerDisplayRoute.tsx`
- `apps/store-desktop/src/customer-display/useCustomerDisplayController.ts`
- small integration changes in:
  - `apps/store-desktop/src/App.tsx`
  - `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.tsx`
  - `apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts`

Native shell:

- `apps/store-desktop/src-tauri/src/runtime_customer_display.rs`
- `apps/store-desktop/src-tauri/src/lib.rs`

## Testing

Required coverage:

- customer-display model tests for state derivation
- workspace/controller tests for display payload updates after checkout transitions
- native bridge tests for open/close customer display window commands
- existing desktop tests remain green

## Exit Criteria

This slice is complete when:

- Store Desktop can open a customer-display window in packaged runtime
- the display renders a customer-facing idle/cart/payment/complete posture
- checkout state changes drive display updates
- the display remains read-only and non-authoritative
- browser/test fallback stays functional
