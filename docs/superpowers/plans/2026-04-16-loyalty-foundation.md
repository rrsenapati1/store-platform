# Loyalty Foundation Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a control-plane-owned loyalty program, customer loyalty ledger, owner-web loyalty management, and Store Desktop checkout redemption/earning flow that stays separate from store credit.

**Architecture:** Keep loyalty authority in the control plane with a small tenant program model, customer account summary, and append-only ledger. Reuse the existing customer and billing surfaces in owner-web and desktop, but extract small helper modules for new workspace-side loyalty loading so the already-large runtime workspace file does not absorb another dense async branch inline.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, pytest, TypeScript, React, Vitest, workspace shared types

---

## File Structure

### Backend

- Create: `services/control-plane-api/alembic/versions/20260416_0032_customer_loyalty.py`
  - Loyalty program/account/ledger migration.
- Modify: `services/control-plane-api/store_control_plane/models/customers.py`
  - Add loyalty program/account/ledger ORM models.
- Modify: `services/control-plane-api/store_control_plane/models/__init__.py`
  - Export new loyalty models.
- Modify: `services/control-plane-api/store_control_plane/repositories/customers.py`
  - Add loyalty program/account/ledger repository operations.
- Modify: `services/control-plane-api/store_control_plane/schemas/customers.py`
  - Add loyalty program, loyalty account, and loyalty adjustment schemas.
- Modify: `services/control-plane-api/store_control_plane/schemas/billing.py`
  - Add loyalty redemption/earned fields to request and response shapes.
- Modify: `services/control-plane-api/store_control_plane/routes/customers.py`
  - Add loyalty program and customer loyalty endpoints.
- Modify: `services/control-plane-api/store_control_plane/routes/billing.py`
  - Accept checkout loyalty redemption input.
- Create: `services/control-plane-api/store_control_plane/services/loyalty.py`
  - Loyalty program, summary, manual adjustment, and billing-side ledger helpers.
- Modify: `services/control-plane-api/store_control_plane/services/billing.py`
  - Apply loyalty redemption/earning and return reversal logic.
- Create: `services/control-plane-api/tests/test_loyalty_flow.py`
  - Loyalty program/account/manual adjustment coverage.
- Modify: `services/control-plane-api/tests/test_billing_foundation_flow.py`
  - Loyalty redemption/earning and coexistence with store credit.

### Shared Types

- Modify: `packages/types/src/index.ts`
  - Add loyalty program/account/ledger and sale snapshot fields.

### Owner Web

- Modify: `apps/owner-web/src/control-plane/client.ts`
  - Add loyalty program/account/adjustment requests.
- Modify: `apps/owner-web/src/control-plane/OwnerCustomerInsightsSection.tsx`
  - Add tenant loyalty settings and customer loyalty summary/adjustment UI.
- Modify: `apps/owner-web/src/control-plane/OwnerCustomerInsightsSection.test.tsx`
  - Add loyalty program and customer loyalty behavior coverage.

### Store Desktop

- Modify: `apps/store-desktop/src/control-plane/client.ts`
  - Add loyalty reads and checkout request field.
- Create: `apps/store-desktop/src/control-plane/storeLoyaltyActions.ts`
  - Small client wrappers for workspace loyalty loading to avoid adding more networking noise to `useStoreRuntimeWorkspace.ts`.
- Modify: `apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts`
  - Track selected customer loyalty, redeemable points, and checkout request payload.
- Modify: `apps/store-desktop/src/control-plane/StoreBillingSection.tsx`
  - Render loyalty balance and redemption controls.
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.billing.test.tsx`
  - Cover loyalty redemption and coexistence with store credit/payment methods.
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.customer-profiles.test.tsx`
  - Cover profile selection loading loyalty balance.
- Modify: `apps/store-desktop/src/runtime-cache/storeRuntimeCache.test.ts`
  - Update any sale record fixtures with new loyalty fields if type changes require it.

### Docs

- Modify: `docs/WORKLOG.md`
  - Record the loyalty slice once verification is complete.

## Task 1: Add failing backend loyalty tests

**Files:**
- Create: `services/control-plane-api/tests/test_loyalty_flow.py`
- Modify: `services/control-plane-api/tests/test_billing_foundation_flow.py`

- [ ] **Step 1: Write failing loyalty program/account tests**

Add tests for:
- creating or updating the tenant loyalty program
- reading a customer loyalty account with empty history
- applying a manual loyalty adjustment

- [ ] **Step 2: Run loyalty backend tests to verify they fail**

Run: `python -m pytest services/control-plane-api/tests/test_loyalty_flow.py -q`
Expected: FAIL with missing loyalty routes, services, or models.

- [ ] **Step 3: Write failing billing loyalty tests**

Add billing tests for:
- sale creation with `loyalty_points_to_redeem`
- anonymous loyalty redemption rejection
- coexistence of loyalty redemption and store credit
- approved return reversing earned points and restoring redeemed points

- [ ] **Step 4: Run focused billing tests to verify they fail**

Run: `python -m pytest services/control-plane-api/tests/test_billing_foundation_flow.py -q`
Expected: FAIL with missing loyalty request/response behavior.

- [ ] **Step 5: Commit**

```bash
git add services/control-plane-api/tests/test_loyalty_flow.py services/control-plane-api/tests/test_billing_foundation_flow.py
git commit -m "test: add loyalty backend coverage"
```

## Task 2: Implement backend loyalty authority

**Files:**
- Create: `services/control-plane-api/alembic/versions/20260416_0032_customer_loyalty.py`
- Modify: `services/control-plane-api/store_control_plane/models/customers.py`
- Modify: `services/control-plane-api/store_control_plane/models/__init__.py`
- Modify: `services/control-plane-api/store_control_plane/repositories/customers.py`
- Modify: `services/control-plane-api/store_control_plane/schemas/customers.py`
- Modify: `services/control-plane-api/store_control_plane/schemas/billing.py`
- Modify: `services/control-plane-api/store_control_plane/routes/customers.py`
- Modify: `services/control-plane-api/store_control_plane/routes/billing.py`
- Create: `services/control-plane-api/store_control_plane/services/loyalty.py`
- Modify: `services/control-plane-api/store_control_plane/services/billing.py`

- [ ] **Step 1: Add ORM models and migration**

Implement:
- `TenantLoyaltyProgram`
- `CustomerLoyaltyAccount`
- `CustomerLoyaltyLedgerEntry`

Migration should create tables and indexes for tenant + customer lookups.

- [ ] **Step 2: Add repository and schema support**

Implement repository operations for:
- get or upsert tenant program
- get or create customer account
- list ledger entries
- append adjustment, earn, redeem, and reverse entries

Add schema fields for:
- loyalty program settings
- loyalty account summary
- billing request/response loyalty fields

- [ ] **Step 3: Add loyalty service**

Implement service methods for:
- `get_loyalty_program`
- `update_loyalty_program`
- `get_customer_loyalty`
- `adjust_customer_loyalty`
- billing helpers for redemption validation and earning math

- [ ] **Step 4: Thread loyalty into billing and returns**

Extend sale creation to:
- validate `loyalty_points_to_redeem`
- compute `loyalty_discount_amount`
- reduce eligible spend
- append `REDEEMED` and `EARNED` entries

Extend approved returns to:
- reverse earned points proportionally
- restore redeemed points proportionally

- [ ] **Step 5: Run focused backend tests**

Run:
- `python -m pytest services/control-plane-api/tests/test_loyalty_flow.py -q`
- `python -m pytest services/control-plane-api/tests/test_billing_foundation_flow.py -q`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add services/control-plane-api/alembic/versions/20260416_0032_customer_loyalty.py services/control-plane-api/store_control_plane/models/customers.py services/control-plane-api/store_control_plane/models/__init__.py services/control-plane-api/store_control_plane/repositories/customers.py services/control-plane-api/store_control_plane/schemas/customers.py services/control-plane-api/store_control_plane/schemas/billing.py services/control-plane-api/store_control_plane/routes/customers.py services/control-plane-api/store_control_plane/routes/billing.py services/control-plane-api/store_control_plane/services/loyalty.py services/control-plane-api/store_control_plane/services/billing.py
git commit -m "feat: add loyalty control-plane authority"
```

## Task 3: Add shared types and owner-web loyalty management

**Files:**
- Modify: `packages/types/src/index.ts`
- Modify: `apps/owner-web/src/control-plane/client.ts`
- Modify: `apps/owner-web/src/control-plane/OwnerCustomerInsightsSection.tsx`
- Modify: `apps/owner-web/src/control-plane/OwnerCustomerInsightsSection.test.tsx`

- [ ] **Step 1: Write failing owner-web loyalty tests**

Add tests for:
- loading tenant loyalty settings and customer loyalty summary
- saving loyalty program settings
- applying manual loyalty adjustment

- [ ] **Step 2: Run focused owner-web tests to verify they fail**

Run: `npm run test --workspace @store/owner-web -- OwnerCustomerInsightsSection.test.tsx`
Expected: FAIL with missing client calls or UI controls.

- [ ] **Step 3: Add shared loyalty types and client methods**

Extend shared types with:
- loyalty program
- loyalty account summary
- loyalty ledger entry
- sale summary loyalty fields

Add owner-web client methods for:
- `getLoyaltyProgram`
- `updateLoyaltyProgram`
- `getCustomerLoyalty`
- `adjustCustomerLoyalty`

- [ ] **Step 4: Add owner-web loyalty UI**

Inside `OwnerCustomerInsightsSection.tsx`:
- load tenant loyalty program
- render program settings form
- render selected customer loyalty summary and recent ledger
- add manual adjustment form

- [ ] **Step 5: Run owner-web verification**

Run:
- `npm run test --workspace @store/owner-web -- OwnerCustomerInsightsSection.test.tsx`
- `npm run typecheck --workspace @store/owner-web`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add packages/types/src/index.ts apps/owner-web/src/control-plane/client.ts apps/owner-web/src/control-plane/OwnerCustomerInsightsSection.tsx apps/owner-web/src/control-plane/OwnerCustomerInsightsSection.test.tsx
git commit -m "feat: add owner loyalty management"
```

## Task 4: Add desktop loyalty checkout loading and redemption

**Files:**
- Modify: `apps/store-desktop/src/control-plane/client.ts`
- Create: `apps/store-desktop/src/control-plane/storeLoyaltyActions.ts`
- Modify: `apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts`
- Modify: `apps/store-desktop/src/control-plane/StoreBillingSection.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.billing.test.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.customer-profiles.test.tsx`
- Modify: `apps/store-desktop/src/runtime-cache/storeRuntimeCache.test.ts`

- [ ] **Step 1: Write failing desktop loyalty tests**

Add tests for:
- selected customer loading loyalty summary
- applying valid loyalty points during checkout
- request payload including `loyalty_points_to_redeem`
- coexistence with store credit

- [ ] **Step 2: Run focused desktop tests to verify they fail**

Run:
- `npm run test --workspace @store/store-desktop -- StoreRuntimeWorkspace.customer-profiles.test.tsx`
- `npm run test --workspace @store/store-desktop -- StoreRuntimeWorkspace.billing.test.tsx`

Expected: FAIL with missing loyalty balance or payload fields.

- [ ] **Step 3: Add desktop client and helper action**

Implement:
- `getCustomerLoyalty(...)`
- helper wrappers in `storeLoyaltyActions.ts`

- [ ] **Step 4: Thread loyalty state through workspace**

In `useStoreRuntimeWorkspace.ts`:
- add selected customer loyalty summary state
- add loyalty points redemption input state
- load loyalty alongside customer profile selection
- include `loyalty_points_to_redeem` in sale creation payload

Do not expand the file with raw fetch logic. Keep client calls in the helper module.

- [ ] **Step 5: Add billing UI**

In `StoreBillingSection.tsx`:
- show available points for selected customer
- show configured redemption posture
- add redemption input bound to workspace state
- keep loyalty clearly separate from store credit and payment method controls

- [ ] **Step 6: Run focused desktop verification**

Run:
- `npm run test --workspace @store/store-desktop -- StoreRuntimeWorkspace.customer-profiles.test.tsx`
- `npm run test --workspace @store/store-desktop -- StoreRuntimeWorkspace.billing.test.tsx`
- `npm run typecheck --workspace @store/store-desktop`

Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add apps/store-desktop/src/control-plane/client.ts apps/store-desktop/src/control-plane/storeLoyaltyActions.ts apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts apps/store-desktop/src/control-plane/StoreBillingSection.tsx apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.billing.test.tsx apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.customer-profiles.test.tsx apps/store-desktop/src/runtime-cache/storeRuntimeCache.test.ts
git commit -m "feat: add desktop loyalty checkout flow"
```

## Task 5: Full verification and docs

**Files:**
- Modify: `docs/WORKLOG.md`

- [ ] **Step 1: Record the loyalty slice in the worklog**

Add a short entry covering:
- backend loyalty authority
- owner-web loyalty management
- desktop checkout loyalty redemption

- [ ] **Step 2: Run backend verification**

Run:
- `python -m pytest services/control-plane-api/tests/test_loyalty_flow.py services/control-plane-api/tests/test_billing_foundation_flow.py -q`

Expected: PASS

- [ ] **Step 3: Run owner-web verification**

Run:
- `npm run test --workspace @store/owner-web`
- `npm run typecheck --workspace @store/owner-web`
- `npm run build --workspace @store/owner-web`

Expected: PASS

- [ ] **Step 4: Run desktop verification**

Run:
- `npm run test --workspace @store/store-desktop`
- `npm run typecheck --workspace @store/store-desktop`
- `npm run build --workspace @store/store-desktop`

Expected: PASS

- [ ] **Step 5: Run repository hygiene check**

Run: `git -c core.safecrlf=false diff --check`
Expected: no output

- [ ] **Step 6: Commit**

```bash
git add docs/WORKLOG.md
git commit -m "docs: record loyalty foundation slice"
```
