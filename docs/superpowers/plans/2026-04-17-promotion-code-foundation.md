# Promotion Code Foundation Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add shared cashier-applied promotion codes with control-plane validation, owner-web campaign management, and Store Desktop checkout integration across both direct sale creation and checkout payment sessions.

**Architecture:** Implement promotions as a dedicated control-plane module with campaign and code models, route-owned CRUD and validation, and billing-side discount resolution that runs before loyalty and store credit. Keep owner-web promotion management in a new workspace section, and keep desktop integration inside the existing billing flow with a small helper module so `useStoreRuntimeWorkspace.ts` does not absorb more raw promotion-client logic inline.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, Pydantic, React, TypeScript, Vitest, pytest

---

## File Structure

### Backend

- Create: `services/control-plane-api/alembic/versions/20260417_0033_promotion_code_foundation.py`
  - Adds promotion campaign and promotion code persistence.
- Create: `services/control-plane-api/store_control_plane/models/promotions.py`
  - Promotion campaign and code ORM models.
- Modify: `services/control-plane-api/store_control_plane/models/__init__.py`
  - Export promotion models.
- Create: `services/control-plane-api/store_control_plane/repositories/promotions.py`
  - Promotion campaign and code repository primitives.
- Create: `services/control-plane-api/store_control_plane/schemas/promotions.py`
  - Campaign and code request or response shapes.
- Create: `services/control-plane-api/store_control_plane/services/promotions.py`
  - Promotion CRUD, validation, and discount calculation helpers.
- Create: `services/control-plane-api/store_control_plane/routes/promotions.py`
  - Tenant promotion campaign and code routes.
- Modify: `services/control-plane-api/store_control_plane/routes/__init__.py`
  - Export the promotions router.
- Modify: `services/control-plane-api/store_control_plane/main.py`
  - Include the promotions router.
- Modify: `services/control-plane-api/store_control_plane/services/__init__.py`
  - Export `PromotionService`.
- Modify: `services/control-plane-api/store_control_plane/schemas/billing.py`
  - Add `promotion_code` input and promotion snapshot fields.
- Modify: `services/control-plane-api/store_control_plane/models/billing.py`
  - Persist sale and payment-session promotion snapshot fields if not already modeled.
- Modify: `services/control-plane-api/store_control_plane/repositories/billing.py`
  - Serialize promotion snapshot fields.
- Modify: `services/control-plane-api/store_control_plane/services/billing.py`
  - Resolve promotion codes during sale creation.
- Modify: `services/control-plane-api/store_control_plane/services/checkout_payments.py`
  - Resolve promotion codes during checkout payment-session creation.
- Modify: `services/control-plane-api/store_control_plane/routes/billing.py`
  - Accept promotion code billing payloads.
- Create: `services/control-plane-api/tests/test_promotions_flow.py`
  - Promotion campaign and code backend coverage.
- Modify: `services/control-plane-api/tests/test_billing_foundation_flow.py`
  - Sale creation coverage with promotion codes.
- Modify: `services/control-plane-api/tests/test_checkout_payment_sessions.py`
  - Payment-session coverage with promotion codes.

### Shared Types

- Modify: `packages/types/src/index.ts`
  - Shared campaign, code, and billing promotion types.

### Owner Web

- Modify: `apps/owner-web/src/control-plane/client.ts`
  - Promotion campaign and code client methods.
- Create: `apps/owner-web/src/control-plane/OwnerPromotionCampaignSection.tsx`
  - Tenant promotion management UI.
- Create: `apps/owner-web/src/control-plane/OwnerPromotionCampaignSection.test.tsx`
  - Promotion management UI coverage.
- Modify: `apps/owner-web/src/control-plane/OwnerWorkspace.tsx`
  - Mount the new promotion section in the existing owner workspace.

### Store Desktop

- Modify: `apps/store-desktop/src/control-plane/client.ts`
  - Billing payload support for `promotion_code`.
- Create: `apps/store-desktop/src/control-plane/storePromotionActions.ts`
  - Small helper functions for promotion-code application and clearing.
- Modify: `apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts`
  - Promotion code state, error posture, and payload wiring.
- Modify: `apps/store-desktop/src/control-plane/StoreBillingSection.tsx`
  - Promotion code entry and applied-discount posture.
- Create: `apps/store-desktop/src/control-plane/client.promotion.test.ts`
  - Desktop client promotion payload coverage.
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.billing.test.tsx`
  - Sale creation and invalid-code workspace coverage.
- Modify: `apps/store-desktop/src/control-plane/StoreBillingSection.payment-session.test.tsx`
  - Checkout payment-session payload coverage with promotion code.

### Docs

- Modify: `docs/WORKLOG.md`
  - Record the promotion-code slice and verification commands.
- Modify: `docs/TASK_LEDGER.md`
  - Advance `V2-005` only if this slice changes the ledger state.

## Task 1: Add failing backend promotion tests

**Files:**
- Create: `services/control-plane-api/tests/test_promotions_flow.py`
- Modify: `services/control-plane-api/tests/test_billing_foundation_flow.py`
- Modify: `services/control-plane-api/tests/test_checkout_payment_sessions.py`

- [ ] **Step 1: Write the failing promotion campaign tests**

Add tests in `services/control-plane-api/tests/test_promotions_flow.py` for:
- creating a promotion campaign
- updating a campaign
- disabling and reactivating a campaign
- creating a shared code under a campaign
- rejecting duplicate shared codes

- [ ] **Step 2: Run the new promotion tests to verify they fail**

Run: `python -m pytest services/control-plane-api/tests/test_promotions_flow.py -q`

Expected: FAIL with missing routes, schemas, or promotion persistence.

- [ ] **Step 3: Write failing billing promotion tests**

Extend `services/control-plane-api/tests/test_billing_foundation_flow.py` to cover:
- sale creation with a valid `promotion_code`
- invalid or disabled code rejection
- promotion discount ordering alongside loyalty and store credit

- [ ] **Step 4: Write failing checkout payment-session promotion tests**

Extend `services/control-plane-api/tests/test_checkout_payment_sessions.py` to cover:
- checkout payment-session creation with `promotion_code`
- invalid code rejection before a session is created
- session discount posture matching the resolved promotion

- [ ] **Step 5: Run the focused billing tests to verify they fail**

Run:
- `python -m pytest services/control-plane-api/tests/test_billing_foundation_flow.py -q`
- `python -m pytest services/control-plane-api/tests/test_checkout_payment_sessions.py -q`

Expected: FAIL with missing promotion payload handling or discount behavior.

- [ ] **Step 6: Commit**

```bash
git add services/control-plane-api/tests/test_promotions_flow.py services/control-plane-api/tests/test_billing_foundation_flow.py services/control-plane-api/tests/test_checkout_payment_sessions.py
git commit -m "test: add promotion code backend coverage"
```

## Task 2: Implement control-plane promotion authority

**Files:**
- Create: `services/control-plane-api/alembic/versions/20260417_0033_promotion_code_foundation.py`
- Create: `services/control-plane-api/store_control_plane/models/promotions.py`
- Modify: `services/control-plane-api/store_control_plane/models/__init__.py`
- Create: `services/control-plane-api/store_control_plane/repositories/promotions.py`
- Create: `services/control-plane-api/store_control_plane/schemas/promotions.py`
- Create: `services/control-plane-api/store_control_plane/services/promotions.py`
- Create: `services/control-plane-api/store_control_plane/routes/promotions.py`
- Modify: `services/control-plane-api/store_control_plane/routes/__init__.py`
- Modify: `services/control-plane-api/store_control_plane/main.py`
- Modify: `services/control-plane-api/store_control_plane/services/__init__.py`

- [ ] **Step 1: Add the migration**

Create `services/control-plane-api/alembic/versions/20260417_0033_promotion_code_foundation.py` to add:
- `promotion_campaigns`
- `promotion_codes`

Include:
- tenant foreign keys
- campaign status and discount fields
- code status and redemption counters
- indexes on `tenant_id`, `status`, and `code`
- uniqueness for `tenant_id + code`

- [ ] **Step 2: Add ORM models**

Create `services/control-plane-api/store_control_plane/models/promotions.py` with:
- `PromotionCampaign`
- `PromotionCode`

Keep campaign and code responsibility separate from billing snapshots.

- [ ] **Step 3: Register models**

Update `services/control-plane-api/store_control_plane/models/__init__.py` so the new promotion models are exported and picked up by metadata bootstrap.

- [ ] **Step 4: Add repository primitives**

Create `services/control-plane-api/store_control_plane/repositories/promotions.py` with repository methods for:
- listing campaigns by tenant
- loading a campaign by id
- loading a code by raw code string
- creating or updating campaigns
- creating codes
- incrementing redemption counters

- [ ] **Step 5: Add schemas**

Create `services/control-plane-api/store_control_plane/schemas/promotions.py` with:
- campaign create and update payloads
- campaign response
- code create payload
- code response

Keep the first slice to flat and percentage discounts plus the approved limit fields only.

- [ ] **Step 6: Add promotion service**

Create `services/control-plane-api/store_control_plane/services/promotions.py` with service methods for:
- list campaigns
- create campaign
- update campaign
- disable or reactivate campaign
- create code
- validate a promotion code against a sale subtotal
- compute discount amount from a campaign and code

- [ ] **Step 7: Add promotion routes**

Create `services/control-plane-api/store_control_plane/routes/promotions.py` with:
- `GET /v1/tenants/{tenant_id}/promotion-campaigns`
- `POST /v1/tenants/{tenant_id}/promotion-campaigns`
- `GET /v1/tenants/{tenant_id}/promotion-campaigns/{campaign_id}`
- `PATCH /v1/tenants/{tenant_id}/promotion-campaigns/{campaign_id}`
- `POST /v1/tenants/{tenant_id}/promotion-campaigns/{campaign_id}/codes`
- `POST /v1/tenants/{tenant_id}/promotion-campaigns/{campaign_id}/disable`
- `POST /v1/tenants/{tenant_id}/promotion-campaigns/{campaign_id}/reactivate`

- [ ] **Step 8: Wire the router and service exports**

Update:
- `services/control-plane-api/store_control_plane/routes/__init__.py`
- `services/control-plane-api/store_control_plane/main.py`
- `services/control-plane-api/store_control_plane/services/__init__.py`

so promotions are available through the app and service barrel.

- [ ] **Step 9: Run focused promotion backend tests**

Run: `python -m pytest services/control-plane-api/tests/test_promotions_flow.py -q`

Expected: PASS

- [ ] **Step 10: Commit**

```bash
git add services/control-plane-api/alembic/versions/20260417_0033_promotion_code_foundation.py services/control-plane-api/store_control_plane/models/promotions.py services/control-plane-api/store_control_plane/models/__init__.py services/control-plane-api/store_control_plane/repositories/promotions.py services/control-plane-api/store_control_plane/schemas/promotions.py services/control-plane-api/store_control_plane/services/promotions.py services/control-plane-api/store_control_plane/routes/promotions.py services/control-plane-api/store_control_plane/routes/__init__.py services/control-plane-api/store_control_plane/main.py services/control-plane-api/store_control_plane/services/__init__.py
git commit -m "feat: add promotion campaign authority"
```

## Task 3: Integrate promotion codes into billing and checkout sessions

**Files:**
- Modify: `services/control-plane-api/store_control_plane/schemas/billing.py`
- Modify: `services/control-plane-api/store_control_plane/models/billing.py`
- Modify: `services/control-plane-api/store_control_plane/repositories/billing.py`
- Modify: `services/control-plane-api/store_control_plane/services/billing.py`
- Modify: `services/control-plane-api/store_control_plane/services/checkout_payments.py`
- Modify: `services/control-plane-api/store_control_plane/routes/billing.py`
- Modify: `packages/types/src/index.ts`
- Modify: `services/control-plane-api/tests/test_billing_foundation_flow.py`
- Modify: `services/control-plane-api/tests/test_checkout_payment_sessions.py`

- [ ] **Step 1: Extend billing schemas**

Update `services/control-plane-api/store_control_plane/schemas/billing.py` to add:
- optional `promotion_code` on sale creation
- optional `promotion_code` on checkout payment-session creation
- promotion snapshot fields on sale and payment-session responses

- [ ] **Step 2: Add billing snapshot fields**

Update `services/control-plane-api/store_control_plane/models/billing.py` and `services/control-plane-api/store_control_plane/repositories/billing.py` to persist and serialize:
- `promotion_campaign_id`
- `promotion_code_id`
- `promotion_code`
- `promotion_discount_amount`

- [ ] **Step 3: Apply promotion resolution in sale creation**

Update `services/control-plane-api/store_control_plane/services/billing.py` so sale creation:
- resolves `promotion_code`
- validates the code through `PromotionService`
- computes `promotion_discount_amount`
- applies that discount before loyalty and store credit
- snapshots the resolved campaign and code fields
- increments redemption counters on successful finalization only

- [ ] **Step 4: Apply promotion resolution in checkout payment sessions**

Update `services/control-plane-api/store_control_plane/services/checkout_payments.py` and `services/control-plane-api/store_control_plane/routes/billing.py` so checkout payment sessions:
- accept `promotion_code`
- run the same validation path as direct sale creation
- preserve the resolved promotion posture on the session

- [ ] **Step 5: Update shared types**

Extend `packages/types/src/index.ts` with:
- promotion campaign and code shapes
- sale promotion snapshot fields
- payment-session promotion fields

- [ ] **Step 6: Re-run the targeted backend tests**

Run:
- `python -m pytest services/control-plane-api/tests/test_billing_foundation_flow.py -q`
- `python -m pytest services/control-plane-api/tests/test_checkout_payment_sessions.py -q`

Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add services/control-plane-api/store_control_plane/schemas/billing.py services/control-plane-api/store_control_plane/models/billing.py services/control-plane-api/store_control_plane/repositories/billing.py services/control-plane-api/store_control_plane/services/billing.py services/control-plane-api/store_control_plane/services/checkout_payments.py services/control-plane-api/store_control_plane/routes/billing.py packages/types/src/index.ts services/control-plane-api/tests/test_billing_foundation_flow.py services/control-plane-api/tests/test_checkout_payment_sessions.py
git commit -m "feat: apply promotion codes in billing"
```

## Task 4: Add owner-web promotion campaign management

**Files:**
- Modify: `apps/owner-web/src/control-plane/client.ts`
- Create: `apps/owner-web/src/control-plane/OwnerPromotionCampaignSection.tsx`
- Create: `apps/owner-web/src/control-plane/OwnerPromotionCampaignSection.test.tsx`
- Modify: `apps/owner-web/src/control-plane/OwnerWorkspace.tsx`
- Modify: `packages/types/src/index.ts`

- [ ] **Step 1: Write the failing owner-web promotion tests**

Create `apps/owner-web/src/control-plane/OwnerPromotionCampaignSection.test.tsx` to cover:
- campaign list load
- campaign create and edit
- shared code creation
- disable and reactivate campaign posture

- [ ] **Step 2: Run the focused owner-web tests to verify they fail**

Run: `npm run test --workspace @store/owner-web -- OwnerPromotionCampaignSection.test.tsx`

Expected: FAIL with missing client methods or missing section component.

- [ ] **Step 3: Add owner-web client methods**

Update `apps/owner-web/src/control-plane/client.ts` with:
- `listPromotionCampaigns`
- `createPromotionCampaign`
- `updatePromotionCampaign`
- `createPromotionCode`
- `disablePromotionCampaign`
- `reactivatePromotionCampaign`

- [ ] **Step 4: Build the owner-web promotion section**

Create `apps/owner-web/src/control-plane/OwnerPromotionCampaignSection.tsx` to render:
- campaign list
- selected campaign detail
- create or edit campaign form
- shared code creation form
- redemption counters

- [ ] **Step 5: Mount the section in the owner workspace**

Update `apps/owner-web/src/control-plane/OwnerWorkspace.tsx` to render `OwnerPromotionCampaignSection` inside the existing owner workspace layout.

- [ ] **Step 6: Re-run the focused owner-web tests**

Run:
- `npm run test --workspace @store/owner-web -- OwnerPromotionCampaignSection.test.tsx`
- `npm run typecheck --workspace @store/owner-web`

Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add apps/owner-web/src/control-plane/client.ts apps/owner-web/src/control-plane/OwnerPromotionCampaignSection.tsx apps/owner-web/src/control-plane/OwnerPromotionCampaignSection.test.tsx apps/owner-web/src/control-plane/OwnerWorkspace.tsx packages/types/src/index.ts
git commit -m "feat: add owner promotion campaign management"
```

## Task 5: Add Store Desktop promotion-code checkout flow

**Files:**
- Modify: `apps/store-desktop/src/control-plane/client.ts`
- Create: `apps/store-desktop/src/control-plane/storePromotionActions.ts`
- Modify: `apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts`
- Modify: `apps/store-desktop/src/control-plane/StoreBillingSection.tsx`
- Create: `apps/store-desktop/src/control-plane/client.promotion.test.ts`
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.billing.test.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreBillingSection.payment-session.test.tsx`

- [ ] **Step 1: Write the failing desktop promotion tests**

Add tests for:
- entering a promotion code
- valid-code discount posture in direct sale flow
- invalid-code error posture
- payment-session payload including `promotion_code`

- [ ] **Step 2: Run the focused desktop tests to verify they fail**

Run:
- `npm run test --workspace @store/store-desktop -- client.promotion.test.ts`
- `npm run test --workspace @store/store-desktop -- StoreRuntimeWorkspace.billing.test.tsx`
- `npm run test --workspace @store/store-desktop -- StoreBillingSection.payment-session.test.tsx`

Expected: FAIL with missing client payloads, workspace state, or billing UI.

- [ ] **Step 3: Extend the desktop client**

Update `apps/store-desktop/src/control-plane/client.ts` to:
- send `promotion_code` in sale creation
- send `promotion_code` in checkout payment-session creation
- parse promotion snapshot fields from responses

- [ ] **Step 4: Add promotion helper actions**

Create `apps/store-desktop/src/control-plane/storePromotionActions.ts` with small helpers for:
- applying a typed promotion code
- clearing a code
- normalizing promotion error posture

- [ ] **Step 5: Thread promotion state through the runtime workspace**

Update `apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts` with:
- `promotionCode` input state
- applied promotion snapshot state
- promotion validation error state
- payload wiring for both direct sale and payment-session creation

Keep raw promotion request details out of the UI component.

- [ ] **Step 6: Extend the billing UI**

Update `apps/store-desktop/src/control-plane/StoreBillingSection.tsx` to render:
- manual `Promotion code` input
- applied promotion code posture
- promotion discount amount
- updated payable posture alongside loyalty and store credit

- [ ] **Step 7: Re-run the focused desktop tests**

Run:
- `npm run test --workspace @store/store-desktop -- client.promotion.test.ts`
- `npm run test --workspace @store/store-desktop -- StoreRuntimeWorkspace.billing.test.tsx`
- `npm run test --workspace @store/store-desktop -- StoreBillingSection.payment-session.test.tsx`
- `npm run typecheck --workspace @store/store-desktop`

Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add apps/store-desktop/src/control-plane/client.ts apps/store-desktop/src/control-plane/storePromotionActions.ts apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts apps/store-desktop/src/control-plane/StoreBillingSection.tsx apps/store-desktop/src/control-plane/client.promotion.test.ts apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.billing.test.tsx apps/store-desktop/src/control-plane/StoreBillingSection.payment-session.test.tsx
git commit -m "feat: add desktop promotion code checkout"
```

## Task 6: Run full verification and update docs

**Files:**
- Modify: `docs/WORKLOG.md`
- Modify: `docs/TASK_LEDGER.md`

- [ ] **Step 1: Update the worklog and ledger**

Record the promotion-code slice in `docs/WORKLOG.md`, and update `docs/TASK_LEDGER.md` only if this slice changes the visible `V2-005` status.

- [ ] **Step 2: Run backend verification**

Run:
`python -m pytest services/control-plane-api/tests/test_promotions_flow.py services/control-plane-api/tests/test_billing_foundation_flow.py services/control-plane-api/tests/test_checkout_payment_sessions.py -q`

Expected: PASS

- [ ] **Step 3: Run owner-web verification**

Run:
- `npm run test --workspace @store/owner-web`
- `npm run typecheck --workspace @store/owner-web`
- `npm run build --workspace @store/owner-web`

Expected: PASS

- [ ] **Step 4: Run Store Desktop verification**

Run:
- `npm run test --workspace @store/store-desktop`
- `npm run typecheck --workspace @store/store-desktop`
- `npm run build --workspace @store/store-desktop`

Expected: PASS

- [ ] **Step 5: Run repository hygiene verification**

Run: `git -c core.safecrlf=false diff --check`

Expected: no output

- [ ] **Step 6: Commit**

```bash
git add docs/WORKLOG.md docs/TASK_LEDGER.md
git commit -m "docs: record promotion code foundation slice"
```
