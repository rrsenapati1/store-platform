# Store Desktop Cashfree Checkout Orchestration Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the QR-only Cashfree desktop payment lane with a unified checkout orchestration flow covering branded UPI QR, hosted terminal checkout, hosted phone checkout, and operator recovery/reconciliation.

**Architecture:** Generalize the control-plane checkout-payment session from a QR-specific model into a surface/mode/action model, keep provider-specific derivation inside the Cashfree adapter, and concentrate desktop payment state inside `useStoreRuntimeCheckoutPayment.ts` so the giant workspace hook stays orchestration-focused. Extend the customer display and billing UI against that unified action contract instead of adding more QR-specific conditionals.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, TypeScript, React, Vitest, Tauri Store Desktop runtime, Cashfree Payments APIs

---

### Task 1: Update the spec-aligned payment contracts

**Files:**
- Modify: `services/control-plane-api/store_control_plane/models/billing.py`
- Modify: `services/control-plane-api/store_control_plane/schemas/billing.py`
- Modify: `services/control-plane-api/store_control_plane/repositories/billing.py`
- Modify: `packages/types/src/index.ts`
- Modify: `apps/store-desktop/src/control-plane/client.ts`

- [ ] **Step 1: Write the failing backend/schema test expectations for generalized checkout session payloads**
- [ ] **Step 2: Run the targeted checkout backend tests to verify they fail for missing handoff/action fields**
- [ ] **Step 3: Add backend model/repository/schema fields for `handoff_surface`, `provider_payment_mode`, `action_payload`, and `action_expires_at`**
- [ ] **Step 4: Extend shared TS types and desktop client payloads to match the generalized session contract**
- [ ] **Step 5: Re-run the targeted schema/backend tests and make sure they pass**

### Task 2: Generalize the Cashfree provider and checkout-payment service

**Files:**
- Modify: `services/control-plane-api/store_control_plane/services/checkout_payment_providers.py`
- Modify: `services/control-plane-api/store_control_plane/services/checkout_payments.py`
- Modify: `services/control-plane-api/store_control_plane/routes/billing.py`
- Test: `services/control-plane-api/tests/test_checkout_payment_sessions.py`
- Test: `services/control-plane-api/tests/test_billing_foundation_flow.py`

- [ ] **Step 1: Write failing backend tests for branded UPI QR, hosted terminal, hosted phone, and recovery actions**
- [ ] **Step 2: Run only those new backend payment tests and verify the failures are for missing behavior**
- [ ] **Step 3: Expand the Cashfree provider result model so it can return generalized action payloads for QR and hosted checkout**
- [ ] **Step 4: Update checkout-session creation logic to select provider mode and handoff surface from the request**
- [ ] **Step 5: Add bounded service operations for refresh/retry/finalize/list-history and wire routes for them**
- [ ] **Step 6: Re-run the targeted backend payment tests and make sure they pass**

### Task 3: Upgrade the desktop payment hook and workspace boundary

**Files:**
- Modify: `apps/store-desktop/src/control-plane/useStoreRuntimeCheckoutPayment.ts`
- Modify: `apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts`
- Test: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.billing.test.tsx`

- [ ] **Step 1: Write the failing desktop integration test for starting hosted terminal and hosted phone sessions**
- [ ] **Step 2: Run that desktop test and verify it fails before implementation**
- [ ] **Step 3: Extend the checkout-payment hook with generalized creation, history, refresh, retry, cancel, and finalize actions**
- [ ] **Step 4: Keep `useStoreRuntimeWorkspace.ts` edits narrow and local because it is a mixed-responsibility file over the 1200-line threshold**
- [ ] **Step 5: Re-run the targeted desktop integration test and make sure it passes**

### Task 4: Replace the QR-only cashier UI with unified payment orchestration

**Files:**
- Modify: `apps/store-desktop/src/control-plane/StoreBillingSection.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreBillingSection.payment-session.test.tsx`
- Modify: `apps/store-desktop/src/customer-display/paymentQr.tsx`

- [ ] **Step 1: Write failing billing-section tests for the new payment choices and hosted-checkout action states**
- [ ] **Step 2: Run the billing-section test file to verify those expectations fail**
- [ ] **Step 3: Add cashier choices for branded QR, hosted terminal, and hosted phone while preserving manual methods**
- [ ] **Step 4: Render generalized action payloads, recovery controls, and recent session history in the billing section**
- [ ] **Step 5: Re-run the billing-section tests and make sure they pass**

### Task 5: Extend the customer display for hosted checkout surfaces

**Files:**
- Modify: `apps/store-desktop/src/customer-display/customerDisplayModel.ts`
- Modify: `apps/store-desktop/src/customer-display/customerDisplayRoute.tsx`
- Modify: `apps/store-desktop/src/customer-display/customerDisplayRoute.test.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.customer-display.test.tsx`

- [ ] **Step 1: Write failing customer-display tests for hosted terminal and phone-handoff states**
- [ ] **Step 2: Run the customer-display test files and verify they fail for the missing states**
- [ ] **Step 3: Expand the display payload model to represent QR, terminal-hosted, and phone-hosted payment actions**
- [ ] **Step 4: Render those new payment states in the customer display route**
- [ ] **Step 5: Re-run the targeted customer-display tests and make sure they pass**

### Task 6: Close out V2-003 and verify end-to-end

**Files:**
- Modify: `docs/TASK_LEDGER.md`
- Modify: `docs/WORKLOG.md`

- [ ] **Step 1: Update the ledger to mark `V2-003` done once verification proves the unified payment orchestration slice is shipped**
- [ ] **Step 2: Add a worklog entry covering the unified Cashfree checkout orchestration closeout**
- [ ] **Step 3: Run full verification**

Run:
- `python -m pytest services/control-plane-api/tests/test_checkout_payment_sessions.py services/control-plane-api/tests/test_billing_foundation_flow.py -q`
- `python -m pytest services/control-plane-api/tests -q`
- `npm run test --workspace @store/store-desktop`
- `npm run typecheck --workspace @store/store-desktop`
- `npm run build --workspace @store/store-desktop`
- `cargo test --manifest-path apps/store-desktop/src-tauri/Cargo.toml --lib`
- `git -c core.safecrlf=false diff --check`

Expected:
- all commands exit `0`

- [ ] **Step 4: Commit docs and implementation with frequent, scoped commits**
- [ ] **Step 5: Push `main` only after all verification commands are green**
