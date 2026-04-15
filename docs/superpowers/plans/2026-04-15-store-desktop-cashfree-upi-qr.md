# Store Desktop Cashfree UPI QR Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Cashfree dynamic UPI QR checkout lane to Store Desktop that finalizes sales only after confirmed payment.

**Architecture:** Introduce a new control-plane checkout payment-session module that owns Cashfree order creation, QR generation, status reconciliation, and idempotent sale finalization. Keep manual sales on the existing path, and add a separate desktop payment-session state boundary so `useStoreRuntimeWorkspace.ts` stays orchestration-focused instead of absorbing more payment/provider logic.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, Pydantic, TypeScript, React, Vitest, Tauri desktop runtime, Cashfree Payments APIs

---

### Task 1: Write Failing Backend Payment-Session Tests First

**Files:**
- Create: `services/control-plane-api/tests/test_checkout_payment_sessions.py`
- Modify: `services/control-plane-api/tests/test_billing_foundation_flow.py`

- [ ] Add a failing backend test for creating a branch checkout payment session that returns QR-ready posture instead of a sale.
- [ ] Add a failing backend test proving a confirmed Cashfree checkout session finalizes exactly one sale and decrements stock once.
- [ ] Add a failing backend test proving expired/failed sessions do not create sales.
- [ ] Add a failing backend test for bad Cashfree webhook signatures being rejected.
- [ ] Run the targeted pytest command and confirm the new tests fail for the expected missing-feature reasons.

### Task 2: Add Checkout Payment Session Persistence And Migration

**Files:**
- Create: `services/control-plane-api/alembic/versions/20260415_0023_checkout_payment_sessions.py`
- Modify: `services/control-plane-api/store_control_plane/models/billing.py`
- Modify: `services/control-plane-api/store_control_plane/models/__init__.py`
- Modify: `services/control-plane-api/store_control_plane/repositories/billing.py`

- [ ] Add the failing repository/model tests indirectly through Task 1 before implementation.
- [ ] Add a new checkout payment session model to `billing.py` instead of stuffing provider fields into `sales` or `payments`.
- [ ] Add the Alembic migration for the new table and its indexes/uniqueness rules.
- [ ] Extend the billing repository with checkout payment-session create/read/update/finalization helpers.
- [ ] Keep sale persistence separate so the new table acts as a precursor, not a replacement.
- [ ] Run the targeted backend tests again and confirm model/repository gaps are the remaining failures.

### Task 3: Add Cashfree In-Store Payment Provider Boundary

**Files:**
- Create: `services/control-plane-api/store_control_plane/services/checkout_payment_providers.py`
- Create: `services/control-plane-api/store_control_plane/services/checkout_payments.py`
- Modify: `services/control-plane-api/store_control_plane/config/settings.py`
- Modify: `services/control-plane-api/store_control_plane/services/__init__.py`

- [ ] Add a failing provider/service test path first via the backend tests from Task 1.
- [ ] Introduce dedicated settings for Cashfree in-store checkout, separate from SaaS subscription billing:
  - client id
  - client secret
  - API base URL
  - API version
  - webhook secret
- [ ] Implement a Cashfree checkout provider adapter for:
  - create order
  - create order-pay QR session
  - fetch payments for order
  - verify payment webhook signature
  - normalize webhook/poll status
- [ ] Persist raw provider response and derive QR payload defensively from provider data fields.
- [ ] Add idempotent finalization logic that creates the sale exactly once after confirmation.
- [ ] Re-run the targeted backend tests and make them pass.

### Task 4: Add Checkout Payment Session Routes And Schemas

**Files:**
- Modify: `services/control-plane-api/store_control_plane/schemas/billing.py`
- Modify: `services/control-plane-api/store_control_plane/routes/billing.py`
- Modify: `services/control-plane-api/store_control_plane/routes/__init__.py`
- Modify: `services/control-plane-api/store_control_plane/main.py`

- [ ] Add request/response schemas for checkout payment sessions, status reads, and cancel action.
- [ ] Add branch routes for create/read/cancel checkout payment sessions.
- [ ] Add a dedicated Cashfree payment webhook ingress route under billing.
- [ ] Keep the existing direct `POST /sales` route for manual methods only.
- [ ] Run targeted backend tests and confirm the API contract now passes.

### Task 5: Add Shared TS Types And Client Endpoints

**Files:**
- Modify: `packages/types/src/index.ts`
- Modify: `apps/store-desktop/src/control-plane/client.ts`

- [ ] Add new shared types for checkout payment session state, QR payload, and Cashfree-backed sale finalization posture.
- [ ] Add client methods for:
  - create checkout payment session
  - get checkout payment session
  - cancel checkout payment session
- [ ] Keep the existing `createSale` client for manual payment paths.
- [ ] Add or update minimal type-level tests if needed.

### Task 6: Extract Desktop Checkout Payment Session Logic Out Of The Large Workspace Hook

**Files:**
- Create: `apps/store-desktop/src/control-plane/useStoreRuntimeCheckoutPayment.ts`
- Modify: `apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts`

- [ ] Classify `useStoreRuntimeWorkspace.ts` as `mixed-responsibility` and keep its payment changes limited to orchestration wiring only.
- [ ] Add failing desktop tests first in the next task before implementing the new hook.
- [ ] Move the new QR payment-session state machine into `useStoreRuntimeCheckoutPayment.ts`:
  - start session
  - poll status
  - retry/cancel
  - block in offline continuity
  - surface finalized sale
- [ ] Keep the workspace hook thin by delegating provider/payment behavior to the new hook.

### Task 7: Write Failing Desktop And Customer-Display Tests First

**Files:**
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.billing.test.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.customer-display.test.tsx`
- Create: `apps/store-desktop/src/control-plane/StoreBillingSection.payment-session.test.tsx`

- [ ] Add a failing test for starting a Cashfree UPI QR session from the billing UI.
- [ ] Add a failing test for confirmed payment transitioning to a finalized sale.
- [ ] Add a failing test for expired/failed payment allowing retry or manual fallback.
- [ ] Add a failing customer-display test for QR-payment state.
- [ ] Run the targeted Vitest commands and confirm the new tests fail before implementation.

### Task 8: Update Desktop Billing And Customer Display UI

**Files:**
- Modify: `apps/store-desktop/src/control-plane/StoreBillingSection.tsx`
- Modify: `apps/store-desktop/src/customer-display/customerDisplayModel.ts`
- Modify: `apps/store-desktop/src/customer-display/customerDisplayRoute.tsx`
- Modify: `apps/store-desktop/src/customer-display/useCustomerDisplayController.ts`

- [ ] Add explicit payment-method choice for Cashfree QR vs manual methods.
- [ ] Render QR session states in the billing UI:
  - QR ready
  - pending customer payment
  - confirmed/finalizing
  - failed/expired
- [ ] Add retry/cancel/manual-fallback controls.
- [ ] Extend customer display state to show QR payload, total due, and payment countdown/status.
- [ ] Re-run the targeted Vitest files and make them pass.

### Task 9: Update Runtime Worklog And Verification

**Files:**
- Modify: `docs/WORKLOG.md`

- [ ] Add a worklog entry for the Cashfree UPI QR slice under `V2-003`.
- [ ] Run full verification:
  - `python -m pytest services/control-plane-api/tests/test_checkout_payment_sessions.py services/control-plane-api/tests/test_billing_foundation_flow.py -q`
  - `python -m pytest services/control-plane-api/tests -q`
  - `npm run test --workspace @store/store-desktop`
  - `npm run typecheck --workspace @store/store-desktop`
  - `npm run build --workspace @store/store-desktop`
  - `git -c core.safecrlf=false diff --check`
- [ ] Commit docs/spec/plan first with a docs commit.
- [ ] Commit the implementation and worklog as a separate feature commit.
