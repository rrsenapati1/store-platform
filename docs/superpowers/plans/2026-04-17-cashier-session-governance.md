# Cashier Session Governance Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add control-plane-owned cashier sessions that gate Store Desktop billing/returns, link sales and returns to the active session, and expose owner-web oversight and force-close controls.

**Architecture:** Extend the existing workforce authority boundary with a new `BranchCashierSession` model, repository operations, service methods, and routes. Reuse the existing Store Desktop runtime actor/device context and owner-web workforce management patterns so cashier sessions become a thin operational layer on top of already-approved staff/device activation instead of a second identity system.

**Tech Stack:** FastAPI, SQLAlchemy async ORM, Alembic, React, TypeScript, Vitest, pytest

---

### Task 1: Add failing backend tests for cashier session authority

**Files:**
- Modify: `services/control-plane-api/tests/test_staff_device_foundation_flow.py`
- Modify: `services/control-plane-api/tests/test_billing_foundation_flow.py`
- Modify: `services/control-plane-api/tests/test_checkout_payment_sessions.py`

- [ ] **Step 1: Add a failing workforce flow test for cashier session lifecycle**

Add coverage for:
- opening a cashier session on a registered device
- rejecting a second open session on the same device
- closing a cashier session
- force-closing an open cashier session

- [ ] **Step 2: Run the new workforce cashier-session test to verify it fails**

Run: `python -m pytest services/control-plane-api/tests/test_staff_device_foundation_flow.py -q`
Expected: FAIL because cashier-session routes/model/service do not exist yet

- [ ] **Step 3: Add failing billing and checkout-session tests**

Add coverage for:
- sale creation rejected when `cashier_session_id` is missing
- checkout payment session rejected when `cashier_session_id` is missing
- sale creation persists `cashier_session_id`

- [ ] **Step 4: Run the targeted billing tests to verify they fail**

Run: `python -m pytest services/control-plane-api/tests/test_billing_foundation_flow.py services/control-plane-api/tests/test_checkout_payment_sessions.py -q`
Expected: FAIL because billing does not yet require or persist cashier sessions

- [ ] **Step 5: Commit the red backend tests**

```bash
git add services/control-plane-api/tests/test_staff_device_foundation_flow.py services/control-plane-api/tests/test_billing_foundation_flow.py services/control-plane-api/tests/test_checkout_payment_sessions.py
git commit -m "test: add cashier session backend coverage"
```

### Task 2: Implement backend cashier session authority and billing integration

**Files:**
- Modify: `services/control-plane-api/store_control_plane/models/workforce.py`
- Modify: `services/control-plane-api/store_control_plane/models/billing.py`
- Modify: `services/control-plane-api/store_control_plane/models/__init__.py`
- Modify: `services/control-plane-api/store_control_plane/repositories/workforce.py`
- Modify: `services/control-plane-api/store_control_plane/repositories/billing.py`
- Modify: `services/control-plane-api/store_control_plane/repositories/__init__.py`
- Modify: `services/control-plane-api/store_control_plane/services/workforce.py`
- Modify: `services/control-plane-api/store_control_plane/services/billing.py`
- Modify: `services/control-plane-api/store_control_plane/services/checkout_payments.py`
- Modify: `services/control-plane-api/store_control_plane/routes/workforce.py`
- Modify: `services/control-plane-api/store_control_plane/schemas/workforce.py`
- Modify: `services/control-plane-api/store_control_plane/schemas/billing.py`
- Modify: `services/control-plane-api/store_control_plane/schemas/__init__.py`
- Create: `services/control-plane-api/alembic/versions/20260417_0041_cashier_session_governance.py`

- [ ] **Step 1: Add the `BranchCashierSession` ORM model and sale/session foreign keys**

Add:
- `branch_cashier_sessions` model in `models/workforce.py`
- nullable `cashier_session_id` fields on sales, returns, and checkout payment sessions in billing models
- exports in `models/__init__.py`

- [ ] **Step 2: Add repository operations for cashier sessions**

Implement repository helpers for:
- create session
- find active session by device
- find active session by staff profile and branch
- get session by id
- list sessions by branch/status
- close / force-close session
- aggregate linked sale/return counts and gross billed amount

- [ ] **Step 3: Extend schemas and routes**

Add request/response models and routes for:
- list cashier sessions
- create cashier session
- get cashier session detail
- close cashier session
- force-close cashier session

- [ ] **Step 4: Implement service-layer rules in `WorkforceService`**

Add service methods that enforce:
- one open session per device
- one open session per staff profile per branch
- actor/device/staff compatibility
- audit events on open/close/force-close

- [ ] **Step 5: Integrate billing and checkout-payment authority**

Require `cashier_session_id` in:
- `BillingService.create_sale`
- sale return creation path
- checkout payment session creation/finalization path

Persist the linked session id and update cashier-session `last_activity_at`.

- [ ] **Step 6: Run targeted backend tests until green**

Run: `python -m pytest services/control-plane-api/tests/test_staff_device_foundation_flow.py services/control-plane-api/tests/test_billing_foundation_flow.py services/control-plane-api/tests/test_checkout_payment_sessions.py -q`
Expected: PASS

- [ ] **Step 7: Commit backend implementation**

```bash
git add services/control-plane-api/store_control_plane/models services/control-plane-api/store_control_plane/repositories services/control-plane-api/store_control_plane/services services/control-plane-api/store_control_plane/routes/workforce.py services/control-plane-api/store_control_plane/schemas services/control-plane-api/alembic/versions/20260417_0041_cashier_session_governance.py
git commit -m "feat: add cashier session authority"
```

### Task 3: Add failing Store Desktop tests for session gating

**Files:**
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.billing.test.tsx`
- Create: `apps/store-desktop/src/control-plane/StoreCashierSessionSection.test.tsx`

- [ ] **Step 1: Add a failing billing-workspace test**

Cover:
- billing actions disabled before session open
- session open enables sale creation
- sale request carries `cashier_session_id`

- [ ] **Step 2: Add a failing cashier-session section test**

Cover:
- open-session form
- active-session banner
- close-session action

- [ ] **Step 3: Run desktop cashier-session tests to verify they fail**

Run: `npm run test --workspace @store/store-desktop -- StoreRuntimeWorkspace.billing.test.tsx StoreCashierSessionSection.test.tsx`
Expected: FAIL because runtime state/actions/UI do not exist yet

- [ ] **Step 4: Commit the red desktop tests**

```bash
git add apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.billing.test.tsx apps/store-desktop/src/control-plane/StoreCashierSessionSection.test.tsx
git commit -m "test: add desktop cashier session coverage"
```

### Task 4: Implement Store Desktop cashier session runtime flow

**Files:**
- Modify: `apps/store-desktop/src/control-plane/client.ts`
- Modify: `apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts`
- Modify: `apps/store-desktop/src/control-plane/StoreBillingSection.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreReturnsSection.tsx`
- Modify: `apps/store-desktop/src/control-plane/useStoreRuntimeCheckoutPayment.ts`
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.tsx`
- Create: `apps/store-desktop/src/control-plane/storeCashierSessionActions.ts`
- Create: `apps/store-desktop/src/control-plane/StoreCashierSessionSection.tsx`

- [ ] **Step 1: Extend the desktop client with cashier-session APIs**

Add client functions for:
- list cashier sessions
- create cashier session
- close cashier session

- [ ] **Step 2: Add cashier-session actions**

Create `storeCashierSessionActions.ts` for:
- loading branch sessions
- opening a session
- closing a session

- [ ] **Step 3: Extend runtime workspace state**

Track:
- session board/history
- active cashier session
- opening float / opening note
- closing note

Wire active `cashier_session_id` into sale, return, and checkout payment session calls.

- [ ] **Step 4: Gate billing and returns**

In `StoreBillingSection.tsx` and returns flow:
- disable action buttons without an open session
- show explicit blocked posture text

- [ ] **Step 5: Add the cashier-session section UI**

Render:
- open-session form when none exists
- active-session summary when open
- close-session action

- [ ] **Step 6: Run targeted desktop tests until green**

Run: `npm run test --workspace @store/store-desktop -- StoreRuntimeWorkspace.billing.test.tsx StoreCashierSessionSection.test.tsx`
Expected: PASS

- [ ] **Step 7: Run the existing desktop activation/runtime regression relevant to staff/device context**

Run: `npm run test --workspace @store/store-desktop -- StoreRuntimeWorkspace.activation.test.tsx`
Expected: PASS

- [ ] **Step 8: Commit desktop implementation**

```bash
git add apps/store-desktop/src/control-plane/client.ts apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts apps/store-desktop/src/control-plane/StoreBillingSection.tsx apps/store-desktop/src/control-plane/StoreReturnsSection.tsx apps/store-desktop/src/control-plane/useStoreRuntimeCheckoutPayment.ts apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.tsx apps/store-desktop/src/control-plane/storeCashierSessionActions.ts apps/store-desktop/src/control-plane/StoreCashierSessionSection.tsx apps/store-desktop/src/control-plane/StoreCashierSessionSection.test.tsx
git commit -m "feat: add desktop cashier session governance"
```

### Task 5: Add owner-web oversight tests

**Files:**
- Create: `apps/owner-web/src/control-plane/OwnerCashierSessionSection.test.tsx`

- [ ] **Step 1: Add a failing owner-web test**

Cover:
- list active and closed cashier sessions
- force-close an open session

- [ ] **Step 2: Run the owner-web cashier-session test to verify it fails**

Run: `npm run test --workspace @store/owner-web -- OwnerCashierSessionSection.test.tsx`
Expected: FAIL because section and client flows do not exist yet

- [ ] **Step 3: Commit the red owner-web test**

```bash
git add apps/owner-web/src/control-plane/OwnerCashierSessionSection.test.tsx
git commit -m "test: add owner cashier session coverage"
```

### Task 6: Implement owner-web cashier session oversight

**Files:**
- Modify: `apps/owner-web/src/control-plane/client.ts`
- Modify: `apps/owner-web/src/control-plane/useOwnerWorkspace.ts`
- Modify: `apps/owner-web/src/control-plane/OwnerWorkspace.tsx`
- Create: `apps/owner-web/src/control-plane/OwnerCashierSessionSection.tsx`

- [ ] **Step 1: Extend owner-web client with cashier-session APIs**

Add:
- list cashier sessions
- get session detail if needed
- force-close session

- [ ] **Step 2: Extend owner workspace state**

Track session records and selected branch session posture inside `useOwnerWorkspace.ts`.

- [ ] **Step 3: Add the owner session board UI**

Render:
- active sessions
- recent closed sessions
- force-close action with reason input

- [ ] **Step 4: Run the targeted owner-web test until green**

Run: `npm run test --workspace @store/owner-web -- OwnerCashierSessionSection.test.tsx`
Expected: PASS

- [ ] **Step 5: Run the existing owner workforce/device regression**

Run: `npm run test --workspace @store/owner-web -- OwnerDeviceClaimSection.test.tsx`
Expected: PASS

- [ ] **Step 6: Commit owner-web implementation**

```bash
git add apps/owner-web/src/control-plane/client.ts apps/owner-web/src/control-plane/useOwnerWorkspace.ts apps/owner-web/src/control-plane/OwnerWorkspace.tsx apps/owner-web/src/control-plane/OwnerCashierSessionSection.tsx apps/owner-web/src/control-plane/OwnerCashierSessionSection.test.tsx
git commit -m "feat: add owner cashier session oversight"
```

### Task 7: Update docs and run full slice verification

**Files:**
- Modify: `docs/WORKLOG.md`
- Modify: `docs/TASK_LEDGER.md`

- [ ] **Step 1: Update worklog for the cashier-session slice**

Record:
- backend cashier-session authority
- desktop billing gating
- owner-web force-close oversight
- verification commands

- [ ] **Step 2: Advance the task ledger**

Update `V2-006` from `Todo` to `In Progress`.

- [ ] **Step 3: Run full slice verification**

Run:
- `python -m pytest services/control-plane-api/tests/test_staff_device_foundation_flow.py services/control-plane-api/tests/test_billing_foundation_flow.py services/control-plane-api/tests/test_checkout_payment_sessions.py -q`
- `npm run test --workspace @store/store-desktop -- StoreRuntimeWorkspace.activation.test.tsx StoreRuntimeWorkspace.billing.test.tsx StoreCashierSessionSection.test.tsx`
- `npm run test --workspace @store/owner-web -- OwnerDeviceClaimSection.test.tsx OwnerCashierSessionSection.test.tsx`
- `npm run typecheck --workspace @store/store-desktop`
- `npm run build --workspace @store/store-desktop`
- `npm run typecheck --workspace @store/owner-web`
- `npm run build --workspace @store/owner-web`
- `git -c core.safecrlf=false diff --check`

- [ ] **Step 4: Commit docs and final slice integration**

```bash
git add docs/WORKLOG.md docs/TASK_LEDGER.md
git commit -m "docs: log cashier session governance"
```
