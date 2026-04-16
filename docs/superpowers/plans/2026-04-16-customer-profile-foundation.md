# Customer Profile Foundation Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add first-class tenant-scoped customer profiles, link checkout to them optionally, and upgrade owner-web and store-desktop to use explicit customer identity instead of sales-only derived reporting.

**Architecture:** Add a control-plane customer profile write model and keep sales/payment records snapshot-based by storing both optional `customer_profile_id` linkage and immutable customer snapshot fields. Reuse the existing customer reporting routes by making them profile-aware for newly linked sales while preserving fallback behavior for legacy unlinked sales. Surface profile management in owner-web and profile search/select/create inside desktop checkout without forcing customer linkage for every sale.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, Pydantic, React 19, TypeScript, Vitest, Testing Library, Vite

---

### Task 1: Add failing backend tests for customer profile authority

**Files:**
- Create: `services/control-plane-api/tests/test_customer_profile_flow.py`
- Modify: `services/control-plane-api/tests/test_billing_foundation_flow.py`
- Modify: `services/control-plane-api/tests/test_customer_reporting_flow.py`

- [ ] **Step 1: Write the failing customer profile API test**

Cover:
- create profile
- search profile by name/GSTIN
- update profile
- archive/reactivate profile
- duplicate GSTIN rejection when GSTIN is present

- [ ] **Step 2: Extend existing billing and reporting tests with failing assertions**

Add assertions for:
- sale creation with `customer_profile_id`
- checkout payment session create with `customer_profile_id`
- reporting preferring profile-backed identity for linked sales

- [ ] **Step 3: Run targeted backend tests to verify they fail**

Run:
- `python -m pytest services/control-plane-api/tests/test_customer_profile_flow.py -q`
- `python -m pytest services/control-plane-api/tests/test_billing_foundation_flow.py services/control-plane-api/tests/test_customer_reporting_flow.py -q`

- [ ] **Step 4: Commit the red backend test work**

`git commit -m "test: add customer profile backend coverage"`

### Task 2: Implement control-plane customer profile model, repository, service, and routes

**Files:**
- Create: `services/control-plane-api/alembic/versions/20260416_0030_customer_profiles.py`
- Modify: `services/control-plane-api/store_control_plane/models/customers.py`
- Modify: `services/control-plane-api/store_control_plane/models/__init__.py`
- Modify: `services/control-plane-api/store_control_plane/repositories/customers.py`
- Modify: `services/control-plane-api/store_control_plane/repositories/__init__.py`
- Modify: `services/control-plane-api/store_control_plane/schemas/customers.py`
- Modify: `services/control-plane-api/store_control_plane/services/customer_reporting.py`
- Create: `services/control-plane-api/store_control_plane/services/customer_profiles.py`
- Modify: `services/control-plane-api/store_control_plane/services/__init__.py`
- Modify: `services/control-plane-api/store_control_plane/routes/customers.py`

- [ ] **Step 1: Add the migration and ORM model**

Implement `customer_profiles` with:
- `id`
- `tenant_id`
- `full_name`
- `phone`
- `email`
- `gstin`
- `default_note`
- `tags`
- `status`
- audit timestamps

Add tenant-scoped unique handling for non-null `gstin`.

- [ ] **Step 2: Extend customer schemas**

Add:
- customer profile create/update/detail/list schemas
- archive/reactivate response shape
- customer reporting response fields needed to expose `customer_profile_id` where useful

- [ ] **Step 3: Add repository support**

In `repositories/customers.py`, add a focused `CustomerProfileRepository` beside the existing reporting repository with methods for:
- search/list
- get by id
- get by GSTIN
- create
- update
- archive
- reactivate
- bulk load by ids for reporting/billing hydration

- [ ] **Step 4: Add service layer**

Create `services/customer_profiles.py` to own:
- normalization
- duplicate GSTIN enforcement
- active/archived lifecycle rules
- tenant-scoped lookup and mutation behavior

- [ ] **Step 5: Add routes**

Extend `routes/customers.py` with:
- `GET /v1/tenants/{tenant_id}/customer-profiles`
- `POST /v1/tenants/{tenant_id}/customer-profiles`
- `GET /v1/tenants/{tenant_id}/customer-profiles/{customer_profile_id}`
- `PATCH /v1/tenants/{tenant_id}/customer-profiles/{customer_profile_id}`
- `POST /v1/tenants/{tenant_id}/customer-profiles/{customer_profile_id}/archive`
- `POST /v1/tenants/{tenant_id}/customer-profiles/{customer_profile_id}/reactivate`

Use the same branch-capable reporting/billing permissions already used for customer visibility.

- [ ] **Step 6: Run the targeted customer profile backend tests**

Run:
- `python -m pytest services/control-plane-api/tests/test_customer_profile_flow.py -q`

- [ ] **Step 7: Commit**

`git commit -m "feat: add customer profile control-plane authority"`

### Task 3: Link billing and checkout payment sessions to optional customer profiles

**Files:**
- Modify: `services/control-plane-api/store_control_plane/models/billing.py`
- Modify: `services/control-plane-api/store_control_plane/repositories/billing.py`
- Modify: `services/control-plane-api/store_control_plane/schemas/billing.py`
- Modify: `services/control-plane-api/store_control_plane/services/billing.py`
- Modify: `services/control-plane-api/store_control_plane/services/checkout_payments.py`
- Modify: `services/control-plane-api/store_control_plane/routes/billing.py`

- [ ] **Step 1: Extend billing models and schemas**

Add nullable `customer_profile_id` to:
- `Sale`
- `CheckoutPaymentSession`

Add optional `customer_profile_id` to:
- `SaleCreateRequest`
- `CheckoutPaymentSessionCreateRequest`
- relevant response payloads used by desktop

- [ ] **Step 2: Update billing repository create methods**

Thread `customer_profile_id` through:
- `create_sale`
- `create_checkout_payment_session`

- [ ] **Step 3: Update billing and checkout services**

When a profile id is provided:
- resolve the profile in tenant scope
- reject archived or unknown profiles
- default snapshot fields from the profile
- still persist immutable `customer_name` and `customer_gstin` snapshots on sale/session records

When no profile id is provided:
- preserve existing anonymous/manual checkout behavior exactly

- [ ] **Step 4: Update billing routes**

Pass through optional `customer_profile_id` without changing route structure.

- [ ] **Step 5: Run targeted backend tests for billing linkage**

Run:
- `python -m pytest services/control-plane-api/tests/test_billing_foundation_flow.py -q`
- `python -m pytest services/control-plane-api/tests/test_checkout_payment_sessions.py -q`

- [ ] **Step 6: Commit**

`git commit -m "feat: link billing to customer profiles"`

### Task 4: Make customer reporting profile-aware without breaking legacy history

**Files:**
- Modify: `services/control-plane-api/store_control_plane/models/customers.py`
- Modify: `services/control-plane-api/store_control_plane/repositories/customers.py`
- Modify: `services/control-plane-api/store_control_plane/services/customer_reporting.py`
- Modify: `services/control-plane-api/store_control_plane/schemas/customers.py`
- Modify: `services/control-plane-api/tests/test_customer_reporting_flow.py`

- [ ] **Step 1: Extend reporting snapshots or repository reads**

Ensure reporting has access to:
- `customer_profile_id` on linked sales
- bulk-loaded customer profiles for linked activity

- [ ] **Step 2: Update customer directory/history/report logic**

Rules:
- linked sales use profile identity
- legacy unlinked sales still use current name/GSTIN-derived fallback
- anonymous walk-ins remain excluded from named customer directory

- [ ] **Step 3: Keep history backward compatible**

Do not require a historical backfill. New linked activity should be profile-backed, old activity should still remain visible.

- [ ] **Step 4: Run reporting regression tests**

Run:
- `python -m pytest services/control-plane-api/tests/test_customer_reporting_flow.py -q`

- [ ] **Step 5: Commit**

`git commit -m "feat: make customer reporting profile-aware"`

### Task 5: Add owner-web customer profile management on top of customer insights

**Files:**
- Modify: `packages/types/src/index.ts`
- Modify: `apps/owner-web/src/control-plane/client.ts`
- Modify: `apps/owner-web/src/control-plane/OwnerCustomerInsightsSection.tsx`
- Modify: `apps/owner-web/src/control-plane/OwnerCustomerInsightsSection.test.tsx`

- [ ] **Step 1: Add shared customer profile types**

Add `ControlPlaneCustomerProfile` request/response types needed by owner-web and desktop.

- [ ] **Step 2: Extend the owner-web client**

Add methods for:
- list/search customer profiles
- create profile
- get profile
- patch profile
- archive/reactivate profile

- [ ] **Step 3: Update the owner customer section**

Extend `OwnerCustomerInsightsSection.tsx` to:
- search profiles
- load a selected profile
- edit basic fields
- archive/reactivate
- keep history rendering for the selected profile

Do not create a separate owner customer-management app.

- [ ] **Step 4: Add/adjust tests**

Cover:
- profile search load
- profile update
- archive/reactivate
- history still renders

- [ ] **Step 5: Run owner-web tests**

Run:
- `npm run test --workspace @store/owner-web -- OwnerCustomerInsightsSection.test.tsx`
- `npm run typecheck --workspace @store/owner-web`

- [ ] **Step 6: Commit**

`git commit -m "feat: add owner customer profile management"`

### Task 6: Add store-desktop customer profile selection and inline create in checkout

**Files:**
- Modify: `packages/types/src/index.ts`
- Modify: `apps/store-desktop/src/control-plane/client.ts`
- Modify: `apps/store-desktop/src/control-plane/useStoreRuntimeCheckoutPayment.ts`
- Modify: `apps/store-desktop/src/control-plane/storeRuntimeContinuityPolicy.ts`
- Modify: `apps/store-desktop/src/control-plane/useStoreRuntimeOfflineContinuity.ts`
- Modify: `apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts`
- Modify: `apps/store-desktop/src/control-plane/StoreBillingSection.tsx`
- Create: `apps/store-desktop/src/control-plane/StoreBillingSection.customer-profile.test.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.customers.test.tsx`

- [ ] **Step 1: Extend the desktop client**

Add customer-profile methods matching the owner-web client.

- [ ] **Step 2: Extend desktop checkout state**

Add workspace state for:
- customer search query
- customer profile results
- selected `customerProfileId`
- inline create draft and loading/error posture

- [ ] **Step 3: Thread profile linkage through checkout flows**

Update:
- manual sale creation in `useStoreRuntimeWorkspace.ts`
- provider-backed checkout in `useStoreRuntimeCheckoutPayment.ts`
- offline continuity draft/replay payloads in `storeRuntimeContinuityPolicy.ts` and `useStoreRuntimeOfflineContinuity.ts`

Carry optional `customer_profile_id` through live and degraded flows without breaking anonymous checkout.

- [ ] **Step 4: Upgrade the billing UI**

In `StoreBillingSection.tsx` add:
- customer search field
- matching profile list
- select action
- clear selection action
- inline create for no-match cases
- linked profile posture near billing fields

Keep manual `customerName` / `customerGstin` fields visible so snapshot override and anonymous/manual billing remain possible.

- [ ] **Step 5: Add desktop tests**

Cover:
- search/select profile
- inline create then select
- clear selection to anonymous/manual mode
- checkout payload includes `customer_profile_id` when linked

- [ ] **Step 6: Run desktop verification**

Run:
- `npm run test --workspace @store/store-desktop -- StoreBillingSection.customer-profile.test.tsx StoreRuntimeWorkspace.customers.test.tsx`
- `npm run typecheck --workspace @store/store-desktop`

- [ ] **Step 7: Commit**

`git commit -m "feat: add desktop checkout customer profile flow"`

### Task 7: Verify the slice end-to-end and document it

**Files:**
- Modify: `docs/WORKLOG.md`
- Modify: `docs/TASK_LEDGER.md`

- [ ] **Step 1: Update docs**

Add a concise `V2-005` worklog entry and move the ledger forward only if the slice is fully green.

- [ ] **Step 2: Run targeted cross-surface verification**

Run:
- `python -m pytest services/control-plane-api/tests/test_customer_profile_flow.py services/control-plane-api/tests/test_billing_foundation_flow.py services/control-plane-api/tests/test_customer_reporting_flow.py services/control-plane-api/tests/test_checkout_payment_sessions.py -q`
- `npm run test --workspace @store/owner-web -- OwnerCustomerInsightsSection.test.tsx`
- `npm run test --workspace @store/store-desktop -- StoreBillingSection.customer-profile.test.tsx StoreRuntimeWorkspace.customers.test.tsx`

- [ ] **Step 3: Run broader verification**

Run:
- `npm run test --workspace @store/owner-web`
- `npm run typecheck --workspace @store/owner-web`
- `npm run build --workspace @store/owner-web`
- `npm run test --workspace @store/store-desktop`
- `npm run typecheck --workspace @store/store-desktop`
- `npm run build --workspace @store/store-desktop`
- `git -c core.safecrlf=false diff --check`

- [ ] **Step 4: Prepare integration**

If everything is green, push the commits through the normal completion flow.
