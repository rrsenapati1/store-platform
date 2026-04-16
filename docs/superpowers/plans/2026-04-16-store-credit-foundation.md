# Store Credit Foundation Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add control-plane-owned store credit with owner issue/adjust flows, return-to-credit issuance, and partial Store Desktop checkout redemption tied to customer profiles.

**Architecture:** Implement store credit as a tenant-wide customer liability model with account summaries, issuance lots, and append-only ledger entries in the control plane. Thread that authority into return approval and sale creation, then expose the balance through owner-web customer management and Store Desktop checkout or return flows without creating parallel commercial surfaces.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, Pydantic, React, TypeScript, Vitest, pytest

---

### Task 1: Add Store Credit Types And Backend Persistence

**Files:**
- Create: `services/control-plane-api/alembic/versions/20260416_0031_customer_store_credit.py`
- Modify: `services/control-plane-api/store_control_plane/models/customers.py`
- Modify: `services/control-plane-api/store_control_plane/models/__init__.py`
- Modify: `services/control-plane-api/store_control_plane/repositories/customers.py`
- Modify: `services/control-plane-api/store_control_plane/schemas/customers.py`
- Modify: `packages/types/src/index.ts`
- Test: `services/control-plane-api/tests/test_store_credit_flow.py`

- [ ] **Step 1: Write the failing backend persistence tests**

Add tests in `services/control-plane-api/tests/test_store_credit_flow.py` for:
- creating a customer credit issue against an active customer profile
- reading account summary with active lots and ledger entries
- adjusting an existing balance

Use real route calls through the FastAPI test client and assert:
- account `available_balance`
- lot `remaining_amount`
- ledger entry ordering and `entry_type`

- [ ] **Step 2: Run the new backend tests to verify they fail**

Run: `C:\Users\Nebula\AppData\Local\Python\bin\python.exe -m pytest services/control-plane-api/tests/test_store_credit_flow.py -q`

Expected: failing import, schema, route, or persistence assertions because store credit models do not exist yet.

- [ ] **Step 3: Add the migration**

Implement `services/control-plane-api/alembic/versions/20260416_0031_customer_store_credit.py` to create:
- `customer_credit_accounts`
- `customer_credit_lots`
- `customer_credit_ledger_entries`

Include:
- tenant and customer-profile foreign keys
- numeric amount fields
- source and entry type text fields
- created or updated timestamps
- indexes on `tenant_id`, `customer_profile_id`, and `created_at`

- [ ] **Step 4: Add SQLAlchemy models**

Extend `services/control-plane-api/store_control_plane/models/customers.py` with:
- `CustomerCreditAccount`
- `CustomerCreditLot`
- `CustomerCreditLedgerEntry`

Register them in `services/control-plane-api/store_control_plane/models/__init__.py`.

Keep responsibility local to the customer domain instead of adding a new generic finance module.

- [ ] **Step 5: Add repository methods**

Extend `services/control-plane-api/store_control_plane/repositories/customers.py` with repository helpers for:
- loading or creating the credit account
- listing active lots
- listing recent ledger entries
- creating issue, adjustment, and redemption ledger rows
- updating account totals and lot remaining balances

Keep these methods focused on persistence primitives, not business validation.

- [ ] **Step 6: Add API and shared types**

Extend `services/control-plane-api/store_control_plane/schemas/customers.py` and `packages/types/src/index.ts` with:
- credit account summary response
- credit lot response
- credit ledger entry response
- issue and adjustment request payloads

Avoid expiry fields in all store-credit types.

- [ ] **Step 7: Re-run the backend tests**

Run: `C:\Users\Nebula\AppData\Local\Python\bin\python.exe -m pytest services/control-plane-api/tests/test_store_credit_flow.py -q`

Expected: fewer failures, limited to missing service or route behavior.

- [ ] **Step 8: Commit**

```bash
git add services/control-plane-api/alembic/versions/20260416_0031_customer_store_credit.py services/control-plane-api/store_control_plane/models/customers.py services/control-plane-api/store_control_plane/models/__init__.py services/control-plane-api/store_control_plane/repositories/customers.py services/control-plane-api/store_control_plane/schemas/customers.py packages/types/src/index.ts services/control-plane-api/tests/test_store_credit_flow.py
git commit -m "feat: add store credit persistence foundation"
```

### Task 2: Add Store Credit Service And Customer Routes

**Files:**
- Create: `services/control-plane-api/store_control_plane/services/store_credit.py`
- Modify: `services/control-plane-api/store_control_plane/services/__init__.py`
- Modify: `services/control-plane-api/store_control_plane/routes/customers.py`
- Modify: `services/control-plane-api/store_control_plane/services/customer_profiles.py`
- Modify: `services/control-plane-api/store_control_plane/repositories/customers.py`
- Test: `services/control-plane-api/tests/test_store_credit_flow.py`

- [ ] **Step 1: Add failing service or route assertions**

Extend `services/control-plane-api/tests/test_store_credit_flow.py` to assert:
- `GET /customer-profiles/{id}/store-credit` returns summary, lots, and ledger
- `POST /store-credit/issue` creates a new lot and increases balance
- `POST /store-credit/adjust` applies a signed adjustment with audit-traceable note
- archived profiles are rejected for new credit mutations

- [ ] **Step 2: Run the backend tests to verify they fail on missing routes**

Run: `C:\Users\Nebula\AppData\Local\Python\bin\python.exe -m pytest services/control-plane-api/tests/test_store_credit_flow.py -q`

Expected: 404 or validation failures for missing store-credit routes and service behavior.

- [ ] **Step 3: Implement the store-credit service**

Create `services/control-plane-api/store_control_plane/services/store_credit.py` with a `StoreCreditService` responsible for:
- requiring an active customer profile
- reading account summary, lots, and ledger
- issuing credit
- adjusting credit
- maintaining deterministic running balances

Keep manual issuance and manual adjustment as distinct source types.

- [ ] **Step 4: Wire customer routes**

Extend `services/control-plane-api/store_control_plane/routes/customers.py` with:
- `GET /v1/tenants/{tenant_id}/customer-profiles/{customer_profile_id}/store-credit`
- `POST /v1/tenants/{tenant_id}/customer-profiles/{customer_profile_id}/store-credit/issue`
- `POST /v1/tenants/{tenant_id}/customer-profiles/{customer_profile_id}/store-credit/adjust`

Make sure request and response models use the new schemas.

- [ ] **Step 5: Export the service**

Update `services/control-plane-api/store_control_plane/services/__init__.py` so the new service is importable through the existing service layer pattern.

- [ ] **Step 6: Re-run the backend tests**

Run: `C:\Users\Nebula\AppData\Local\Python\bin\python.exe -m pytest services/control-plane-api/tests/test_store_credit_flow.py -q`

Expected: Task 1 and Task 2 tests pass.

- [ ] **Step 7: Commit**

```bash
git add services/control-plane-api/store_control_plane/services/store_credit.py services/control-plane-api/store_control_plane/services/__init__.py services/control-plane-api/store_control_plane/routes/customers.py services/control-plane-api/store_control_plane/services/customer_profiles.py services/control-plane-api/store_control_plane/repositories/customers.py services/control-plane-api/tests/test_store_credit_flow.py
git commit -m "feat: add customer store credit routes"
```

### Task 3: Integrate Store Credit Into Billing And Returns

**Files:**
- Modify: `services/control-plane-api/store_control_plane/schemas/billing.py`
- Modify: `services/control-plane-api/store_control_plane/models/billing.py`
- Modify: `services/control-plane-api/store_control_plane/repositories/billing.py`
- Modify: `services/control-plane-api/store_control_plane/services/billing.py`
- Modify: `services/control-plane-api/store_control_plane/services/checkout_payments.py`
- Modify: `services/control-plane-api/store_control_plane/routes/billing.py`
- Modify: `services/control-plane-api/tests/test_billing_foundation_flow.py`
- Modify: `services/control-plane-api/tests/test_checkout_payment_sessions.py`
- Modify: `services/control-plane-api/tests/test_customer_profile_flow.py`
- Modify: `services/control-plane-api/tests/test_store_credit_flow.py`

- [ ] **Step 1: Write failing billing and return tests**

Extend backend tests to cover:
- sale creation with `store_credit_amount`
- rejecting credit redemption without `customer_profile_id`
- rejecting redemption above available balance
- split payment snapshot on the resulting sale
- approved return with `refund_method = STORE_CREDIT`
- return-to-credit creates a new credit lot and ledger issue entry

Prefer adding the sale-redemption assertions to `test_billing_foundation_flow.py` and the return-to-credit assertions to `test_store_credit_flow.py`.

- [ ] **Step 2: Run the targeted backend tests to verify they fail**

Run:
`C:\Users\Nebula\AppData\Local\Python\bin\python.exe -m pytest services/control-plane-api/tests/test_store_credit_flow.py services/control-plane-api/tests/test_billing_foundation_flow.py services/control-plane-api/tests/test_checkout_payment_sessions.py -q`

Expected: failures on missing billing fields and missing store-credit behavior.

- [ ] **Step 3: Extend billing schemas and models**

Update `services/control-plane-api/store_control_plane/schemas/billing.py` to add:
- `store_credit_amount` on sale create payload
- `store_credit_amount` or equivalent split-payment summary in sale response
- allow `refund_method = STORE_CREDIT` for sale returns

Update `services/control-plane-api/store_control_plane/models/billing.py` and repository serializers to persist any new store-credit snapshot fields needed on sales or payments.

- [ ] **Step 4: Implement sale redemption logic**

Update `services/control-plane-api/store_control_plane/services/billing.py` so sale creation:
- requires `customer_profile_id` when `store_credit_amount > 0`
- validates available balance
- allocates redemptions oldest-lot-first
- writes `REDEEMED` ledger entries
- decreases lot remaining balances
- stores sale snapshot reflecting split settlement

Keep inventory and sale authority in the same transaction.

- [ ] **Step 5: Implement return-to-credit approval**

Update the return approval path in `services/control-plane-api/store_control_plane/services/billing.py` so `STORE_CREDIT`:
- issues a new customer credit lot sourced from the sale return
- writes an `ISSUED` ledger entry
- does not attempt cash or UPI payout logic

- [ ] **Step 6: Keep checkout payment session compatibility**

Update `services/control-plane-api/store_control_plane/services/checkout_payments.py` only as needed so payment-session payload validation remains compatible with future split-payment checkout while not claiming provider-backed store-credit collection.

Do not expand the payment provider boundary beyond what this slice needs.

- [ ] **Step 7: Re-run the targeted backend tests**

Run:
`C:\Users\\Nebula\\AppData\\Local\\Python\\bin\\python.exe -m pytest services/control-plane-api/tests/test_store_credit_flow.py services/control-plane-api/tests/test_billing_foundation_flow.py services/control-plane-api/tests/test_checkout_payment_sessions.py -q`

Expected: targeted billing and store-credit tests pass.

- [ ] **Step 8: Commit**

```bash
git add services/control-plane-api/store_control_plane/schemas/billing.py services/control-plane-api/store_control_plane/models/billing.py services/control-plane-api/store_control_plane/repositories/billing.py services/control-plane-api/store_control_plane/services/billing.py services/control-plane-api/store_control_plane/services/checkout_payments.py services/control-plane-api/store_control_plane/routes/billing.py services/control-plane-api/tests/test_billing_foundation_flow.py services/control-plane-api/tests/test_checkout_payment_sessions.py services/control-plane-api/tests/test_customer_profile_flow.py services/control-plane-api/tests/test_store_credit_flow.py
git commit -m "feat: add store credit billing and return flows"
```

### Task 4: Add Owner-Web Store Credit Management

**Files:**
- Modify: `apps/owner-web/src/control-plane/client.ts`
- Modify: `apps/owner-web/src/control-plane/OwnerCustomerInsightsSection.tsx`
- Modify: `apps/owner-web/src/control-plane/OwnerCustomerInsightsSection.test.tsx`
- Modify: `packages/types/src/index.ts`

- [ ] **Step 1: Write failing owner-web tests**

Extend `apps/owner-web/src/control-plane/OwnerCustomerInsightsSection.test.tsx` to cover:
- loading store-credit summary for the selected customer profile
- issuing credit
- adjusting credit
- rendering recent ledger entries

- [ ] **Step 2: Run the owner-web test to verify it fails**

Run:
`npm run test --workspace @store/owner-web -- OwnerCustomerInsightsSection.test.tsx`

Expected: failures on missing client methods or missing store-credit UI.

- [ ] **Step 3: Add owner-web client methods**

Extend `apps/owner-web/src/control-plane/client.ts` with:
- `getCustomerStoreCredit`
- `issueCustomerStoreCredit`
- `adjustCustomerStoreCredit`

Reuse the shared response types from `packages/types/src/index.ts`.

- [ ] **Step 4: Extend the customer insights section**

Update `apps/owner-web/src/control-plane/OwnerCustomerInsightsSection.tsx` to show:
- available balance
- recent ledger
- manual issue form
- manual adjustment form

Keep this inside the existing customer insights surface rather than creating a new section.

- [ ] **Step 5: Re-run the owner-web test**

Run:
`npm run test --workspace @store/owner-web -- OwnerCustomerInsightsSection.test.tsx`

Expected: the focused owner-web test passes.

- [ ] **Step 6: Commit**

```bash
git add apps/owner-web/src/control-plane/client.ts apps/owner-web/src/control-plane/OwnerCustomerInsightsSection.tsx apps/owner-web/src/control-plane/OwnerCustomerInsightsSection.test.tsx packages/types/src/index.ts
git commit -m "feat: add owner store credit management"
```

### Task 5: Add Store Desktop Credit Redemption And Return-To-Credit UX

**Files:**
- Modify: `apps/store-desktop/src/control-plane/client.ts`
- Modify: `apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts`
- Modify: `apps/store-desktop/src/control-plane/StoreBillingSection.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.billing.test.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.returns.test.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreBillingSection.payment-session.test.tsx`
- Modify: `packages/types/src/index.ts`

- [ ] **Step 1: Write failing desktop checkout and return tests**

Extend desktop tests to cover:
- loading available store credit for selected customer profile
- applying partial store credit during sale creation
- blocking credit redemption for anonymous checkout
- creating a sale return with `STORE_CREDIT`

Prefer:
- redemption assertions in `StoreRuntimeWorkspace.billing.test.tsx`
- return-to-credit assertions in `StoreRuntimeWorkspace.returns.test.tsx`

- [ ] **Step 2: Run the focused desktop tests to verify they fail**

Run:
`npm run test --workspace @store/store-desktop -- StoreRuntimeWorkspace.billing.test.tsx StoreRuntimeWorkspace.returns.test.tsx`

Expected: failures on missing client calls, workspace state, or UI.

- [ ] **Step 3: Extend desktop client methods**

Update `apps/store-desktop/src/control-plane/client.ts` with:
- `getCustomerStoreCredit`
- `issueCustomerStoreCredit` only if the checkout surface truly needs it now, otherwise omit
- support for `store_credit_amount` on sale create
- support for `refund_method = STORE_CREDIT` in return payloads

Keep the desktop client focused on what checkout and returns actually need.

- [ ] **Step 4: Extend workspace state**

Update `apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts` with:
- selected-customer credit summary state
- `storeCreditAmount` input state
- load logic when a customer profile is selected
- sale create wiring that sends `store_credit_amount`
- return create wiring that allows `STORE_CREDIT`

Do not add a separate desktop store-credit app state machine.

- [ ] **Step 5: Extend billing UI**

Update `apps/store-desktop/src/control-plane/StoreBillingSection.tsx` to show:
- available store credit for selected profile
- store-credit amount input
- guidance that remaining balance is paid via the selected payment method

Keep the field hidden or disabled for anonymous checkout.

- [ ] **Step 6: Re-run the focused desktop tests**

Run:
`npm run test --workspace @store/store-desktop -- StoreRuntimeWorkspace.billing.test.tsx StoreRuntimeWorkspace.returns.test.tsx`

Expected: focused desktop tests pass.

- [ ] **Step 7: Commit**

```bash
git add apps/store-desktop/src/control-plane/client.ts apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts apps/store-desktop/src/control-plane/StoreBillingSection.tsx apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.billing.test.tsx apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.returns.test.tsx apps/store-desktop/src/control-plane/StoreBillingSection.payment-session.test.tsx packages/types/src/index.ts
git commit -m "feat: add desktop store credit redemption"
```

### Task 6: Run Full Verification And Update Docs

**Files:**
- Modify: `docs/TASK_LEDGER.md`
- Modify: `docs/WORKLOG.md`

- [ ] **Step 1: Update ledger and worklog**

Update:
- `docs/WORKLOG.md` with the store-credit slice and verification commands
- `docs/TASK_LEDGER.md` only if the task status should move within `V2-005`

- [ ] **Step 2: Run the backend verification**

Run:
`C:\Users\Nebula\AppData\Local\Python\bin\python.exe -m pytest services/control-plane-api/tests/test_store_credit_flow.py services/control-plane-api/tests/test_billing_foundation_flow.py services/control-plane-api/tests/test_checkout_payment_sessions.py services/control-plane-api/tests/test_customer_profile_flow.py -q`

Expected: all pass.

- [ ] **Step 3: Run the owner-web verification**

Run:
`npm run test --workspace @store/owner-web`
`npm run typecheck --workspace @store/owner-web`
`npm run build --workspace @store/owner-web`

Expected: all pass.

- [ ] **Step 4: Run the desktop verification**

Run:
`npm run test --workspace @store/store-desktop`
`npm run typecheck --workspace @store/store-desktop`
`npm run build --workspace @store/store-desktop`

Expected: all pass.

- [ ] **Step 5: Run repository hygiene verification**

Run:
`git -c core.safecrlf=false diff --check`

Expected: no whitespace or patch hygiene failures.

- [ ] **Step 6: Commit**

```bash
git add docs/TASK_LEDGER.md docs/WORKLOG.md
git commit -m "docs: record store credit foundation slice"
```
