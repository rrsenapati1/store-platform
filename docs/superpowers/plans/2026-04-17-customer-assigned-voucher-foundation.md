# Customer-Assigned Voucher Foundation Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add single-use fixed-value customer-assigned vouchers on top of the promotion foundation, with owner-web issuance/cancel flows, Store Desktop checkout redemption, and control-plane-owned billing and payment-session behavior.

**Architecture:** Extend the existing promotion system with a new `ASSIGNED_VOUCHER` trigger mode and a dedicated voucher-assignment record tied to `customer_profile_id`. Keep pricing authority centralized in the control plane by extending checkout pricing preview, direct sale creation, and checkout payment-session snapshots to understand one customer voucher as the sole manual promotion instrument alongside automatic discounts. Keep large orchestration files thin by adding focused voucher service and desktop action helpers instead of deepening existing giant files.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, Pydantic, React, TypeScript, Vitest, pytest.

---

## File Map

### Control plane

- Create: `services/control-plane-api/alembic/versions/20260417_0036_customer_assigned_vouchers.py`
- Modify: `services/control-plane-api/store_control_plane/models/promotions.py`
- Modify: `services/control-plane-api/store_control_plane/models/billing.py`
- Modify: `services/control-plane-api/store_control_plane/repositories/promotions.py`
- Modify: `services/control-plane-api/store_control_plane/schemas/promotions.py`
- Modify: `services/control-plane-api/store_control_plane/schemas/billing.py`
- Modify: `services/control-plane-api/store_control_plane/routes/promotions.py`
- Modify: `services/control-plane-api/store_control_plane/services/promotions.py`
- Modify: `services/control-plane-api/store_control_plane/services/checkout_pricing.py`
- Modify: `services/control-plane-api/store_control_plane/services/checkout_payments.py`
- Modify: `services/control-plane-api/store_control_plane/services/billing.py`

### Shared contract

- Modify: `packages/types/src/index.ts`

### Owner web

- Modify: `apps/owner-web/src/control-plane/client.ts`
- Modify: `apps/owner-web/src/control-plane/OwnerPromotionCampaignSection.tsx`
- Modify: `apps/owner-web/src/control-plane/OwnerCustomerInsightsSection.tsx`

### Store Desktop

- Create: `apps/store-desktop/src/control-plane/storeVoucherActions.ts`
- Modify: `apps/store-desktop/src/control-plane/client.ts`
- Modify: `apps/store-desktop/src/control-plane/storePricingPreviewActions.ts`
- Modify: `apps/store-desktop/src/control-plane/useStoreRuntimeCheckoutPayment.ts`
- Modify: `apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts`
- Modify: `apps/store-desktop/src/control-plane/StoreBillingSection.tsx`

### Tests

- Modify: `services/control-plane-api/tests/test_promotions_flow.py`
- Modify: `services/control-plane-api/tests/test_checkout_price_preview_flow.py`
- Modify: `services/control-plane-api/tests/test_billing_foundation_flow.py`
- Modify: `services/control-plane-api/tests/test_checkout_payment_sessions.py`
- Modify: `apps/owner-web/src/control-plane/OwnerPromotionCampaignSection.test.tsx`
- Modify: `apps/owner-web/src/control-plane/OwnerCustomerInsightsSection.test.tsx`
- Modify: `apps/store-desktop/src/control-plane/client.pricing-preview.test.ts`
- Modify: `apps/store-desktop/src/control-plane/StoreBillingSection.pricing-preview.test.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.customer-profiles.test.tsx`
- Create if needed: `apps/store-desktop/src/control-plane/client.vouchers.test.ts`

### Docs

- Modify: `docs/WORKLOG.md`

---

### Task 1: Add failing promotion and voucher backend tests

**Files:**
- Modify: `services/control-plane-api/tests/test_promotions_flow.py`

- [ ] **Step 1: Write failing campaign-validation coverage**

Add tests for:
- creating `ASSIGNED_VOUCHER` campaigns
- rejecting non-`FLAT_AMOUNT` voucher campaigns
- rejecting non-`CART` voucher campaigns
- rejecting shared-code creation for voucher campaigns

- [ ] **Step 2: Write failing voucher-assignment coverage**

Add tests for:
- issuing a voucher to one customer profile
- listing customer vouchers
- canceling an active voucher
- rejecting cancel after redemption

- [ ] **Step 3: Run targeted backend tests to verify RED**

Run: `C:\Users\Nebula\AppData\Local\Python\bin\python.exe -m pytest services/control-plane-api/tests/test_promotions_flow.py -q`
Expected: FAIL on missing voucher campaign and assignment behavior.

- [ ] **Step 4: Commit**

```bash
git add services/control-plane-api/tests/test_promotions_flow.py
git commit -m "test: add customer voucher promotion coverage"
```

### Task 2: Add voucher persistence and promotion service support

**Files:**
- Create: `services/control-plane-api/alembic/versions/20260417_0036_customer_assigned_vouchers.py`
- Modify: `services/control-plane-api/store_control_plane/models/promotions.py`
- Modify: `services/control-plane-api/store_control_plane/repositories/promotions.py`
- Modify: `services/control-plane-api/store_control_plane/schemas/promotions.py`
- Modify: `services/control-plane-api/store_control_plane/routes/promotions.py`
- Modify: `services/control-plane-api/store_control_plane/services/promotions.py`
- Modify: `packages/types/src/index.ts`

- [ ] **Step 1: Add the voucher-assignment migration**

Create the new table and any supporting sale/payment-session snapshot columns that belong in this migration boundary.

- [ ] **Step 2: Add promotion models and repository methods**

Add:
- voucher-assignment model
- customer-scoped list/get/create/cancel repository methods

- [ ] **Step 3: Extend promotion schemas and shared types**

Add:
- voucher campaign trigger mode typing
- customer voucher response models
- customer voucher list response

- [ ] **Step 4: Extend promotion service**

Implement:
- voucher campaign validation
- customer voucher issue/list/cancel behavior
- snapshot serialization for voucher preview and billing use

- [ ] **Step 5: Extend promotion routes**

Add:
- `GET /customer-profiles/{customer_profile_id}/vouchers`
- `POST /customer-profiles/{customer_profile_id}/vouchers`
- `POST /customer-profiles/{customer_profile_id}/vouchers/{voucher_id}/cancel`

- [ ] **Step 6: Run targeted backend tests to verify GREEN**

Run: `C:\Users\Nebula\AppData\Local\Python\bin\python.exe -m pytest services/control-plane-api/tests/test_promotions_flow.py -q`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add services/control-plane-api/alembic/versions/20260417_0036_customer_assigned_vouchers.py services/control-plane-api/store_control_plane/models/promotions.py services/control-plane-api/store_control_plane/repositories/promotions.py services/control-plane-api/store_control_plane/schemas/promotions.py services/control-plane-api/store_control_plane/routes/promotions.py services/control-plane-api/store_control_plane/services/promotions.py packages/types/src/index.ts
git commit -m "feat: add customer voucher promotion authority"
```

### Task 3: Add pricing preview and billing voucher tests first

**Files:**
- Modify: `services/control-plane-api/tests/test_checkout_price_preview_flow.py`
- Modify: `services/control-plane-api/tests/test_billing_foundation_flow.py`
- Modify: `services/control-plane-api/tests/test_checkout_payment_sessions.py`

- [ ] **Step 1: Write failing pricing preview test**

Cover:
- selected customer voucher applies after automatic discount
- voucher and shared code conflict is rejected
- preview returns voucher summary fields

- [ ] **Step 2: Write failing sale-creation test**

Cover:
- sale snapshots voucher fields
- voucher discount allocates across lines
- voucher becomes `REDEEMED`

- [ ] **Step 3: Write failing checkout-session test**

Cover:
- session snapshots voucher intent
- finalization redeems voucher
- failed/canceled session does not redeem voucher

- [ ] **Step 4: Run targeted backend tests to verify RED**

Run: `C:\Users\Nebula\AppData\Local\Python\bin\python.exe -m pytest services/control-plane-api/tests/test_checkout_price_preview_flow.py services/control-plane-api/tests/test_billing_foundation_flow.py services/control-plane-api/tests/test_checkout_payment_sessions.py -q`
Expected: FAIL on missing voucher pricing/billing behavior.

- [ ] **Step 5: Commit**

```bash
git add services/control-plane-api/tests/test_checkout_price_preview_flow.py services/control-plane-api/tests/test_billing_foundation_flow.py services/control-plane-api/tests/test_checkout_payment_sessions.py
git commit -m "test: add voucher pricing and billing coverage"
```

### Task 4: Implement voucher-aware pricing and billing

**Files:**
- Modify: `services/control-plane-api/store_control_plane/models/billing.py`
- Modify: `services/control-plane-api/store_control_plane/schemas/billing.py`
- Modify: `services/control-plane-api/store_control_plane/services/checkout_pricing.py`
- Modify: `services/control-plane-api/store_control_plane/services/checkout_payments.py`
- Modify: `services/control-plane-api/store_control_plane/services/billing.py`
- Modify: `packages/types/src/index.ts`

- [ ] **Step 1: Extend billing models and schemas**

Add voucher snapshot fields to:
- sales
- sale lines
- checkout payment sessions
- pricing preview responses

- [ ] **Step 2: Extend checkout pricing service**

Implement:
- customer voucher validation
- manual-instrument conflict guard with shared code
- voucher line allocation
- preview summary and line response fields

- [ ] **Step 3: Extend direct sale creation**

Implement:
- sale snapshot fields
- voucher redemption on successful sale commit

- [ ] **Step 4: Extend checkout payment sessions**

Implement:
- voucher snapshot on session create
- voucher redemption only during sale finalization
- recovery-safe no-redemption for failed or canceled sessions

- [ ] **Step 5: Run targeted backend tests to verify GREEN**

Run: `C:\Users\Nebula\AppData\Local\Python\bin\python.exe -m pytest services/control-plane-api/tests/test_promotions_flow.py services/control-plane-api/tests/test_checkout_price_preview_flow.py services/control-plane-api/tests/test_billing_foundation_flow.py services/control-plane-api/tests/test_checkout_payment_sessions.py -q`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add services/control-plane-api/store_control_plane/models/billing.py services/control-plane-api/store_control_plane/schemas/billing.py services/control-plane-api/store_control_plane/services/checkout_pricing.py services/control-plane-api/store_control_plane/services/checkout_payments.py services/control-plane-api/store_control_plane/services/billing.py packages/types/src/index.ts
git commit -m "feat: apply customer vouchers in pricing and billing"
```

### Task 5: Add owner-web voucher management tests first

**Files:**
- Modify: `apps/owner-web/src/control-plane/OwnerPromotionCampaignSection.test.tsx`
- Modify: `apps/owner-web/src/control-plane/OwnerCustomerInsightsSection.test.tsx`

- [ ] **Step 1: Write failing voucher campaign UI test**

Cover:
- creating or editing an `ASSIGNED_VOUCHER` campaign
- shared code controls hidden or rejected for voucher campaigns

- [ ] **Step 2: Write failing customer voucher issue/cancel UI test**

Cover:
- issue voucher from selected customer
- voucher appears in selected customer detail
- cancel voucher refreshes posture

- [ ] **Step 3: Run targeted owner-web tests to verify RED**

Run: `npm run test --workspace @store/owner-web -- OwnerPromotionCampaignSection.test.tsx OwnerCustomerInsightsSection.test.tsx`
Expected: FAIL on missing voucher UI/client behavior.

- [ ] **Step 4: Commit**

```bash
git add apps/owner-web/src/control-plane/OwnerPromotionCampaignSection.test.tsx apps/owner-web/src/control-plane/OwnerCustomerInsightsSection.test.tsx
git commit -m "test: add owner voucher workflow coverage"
```

### Task 6: Implement owner-web voucher flows

**Files:**
- Modify: `apps/owner-web/src/control-plane/client.ts`
- Modify: `apps/owner-web/src/control-plane/OwnerPromotionCampaignSection.tsx`
- Modify: `apps/owner-web/src/control-plane/OwnerCustomerInsightsSection.tsx`
- Modify: `packages/types/src/index.ts`

- [ ] **Step 1: Extend owner client**

Add:
- customer voucher list/issue/cancel calls

- [ ] **Step 2: Extend promotion campaign UI**

Add voucher campaign posture and remove shared-code affordance when trigger mode is `ASSIGNED_VOUCHER`.

- [ ] **Step 3: Extend customer insights UI**

Add:
- voucher list
- issue form
- cancel action

- [ ] **Step 4: Run targeted owner-web tests to verify GREEN**

Run: `npm run test --workspace @store/owner-web -- OwnerPromotionCampaignSection.test.tsx OwnerCustomerInsightsSection.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/owner-web/src/control-plane/client.ts apps/owner-web/src/control-plane/OwnerPromotionCampaignSection.tsx apps/owner-web/src/control-plane/OwnerCustomerInsightsSection.tsx packages/types/src/index.ts
git commit -m "feat: add owner customer voucher management"
```

### Task 7: Add desktop voucher checkout tests first

**Files:**
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.customer-profiles.test.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreBillingSection.pricing-preview.test.tsx`
- Modify: `apps/store-desktop/src/control-plane/client.pricing-preview.test.ts`
- Create if needed: `apps/store-desktop/src/control-plane/client.vouchers.test.ts`

- [ ] **Step 1: Write failing desktop client coverage**

Cover:
- load customer vouchers
- pricing preview payload with `customer_voucher_id`

- [ ] **Step 2: Write failing workspace flow coverage**

Cover:
- selected customer loads vouchers
- selecting voucher clears shared code
- typing code clears selected voucher
- sale/payment-session payload includes `customer_voucher_id`

- [ ] **Step 3: Write failing billing section coverage**

Cover:
- voucher list renders
- voucher discount appears in preview summary

- [ ] **Step 4: Run targeted desktop tests to verify RED**

Run: `npm run test --workspace @store/store-desktop -- client.pricing-preview.test.ts StoreBillingSection.pricing-preview.test.tsx StoreRuntimeWorkspace.customer-profiles.test.tsx`
Expected: FAIL on missing voucher desktop behavior.

- [ ] **Step 5: Commit**

```bash
git add apps/store-desktop/src/control-plane/client.pricing-preview.test.ts apps/store-desktop/src/control-plane/StoreBillingSection.pricing-preview.test.tsx apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.customer-profiles.test.tsx
git commit -m "test: add desktop voucher checkout coverage"
```

### Task 8: Implement desktop voucher actions and billing UI

**Files:**
- Create: `apps/store-desktop/src/control-plane/storeVoucherActions.ts`
- Modify: `apps/store-desktop/src/control-plane/client.ts`
- Modify: `apps/store-desktop/src/control-plane/storePricingPreviewActions.ts`
- Modify: `apps/store-desktop/src/control-plane/useStoreRuntimeCheckoutPayment.ts`
- Modify: `apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts`
- Modify: `apps/store-desktop/src/control-plane/StoreBillingSection.tsx`
- Modify: `packages/types/src/index.ts`

- [ ] **Step 1: Add focused voucher action helper**

Create a small helper for:
- loading selected customer vouchers
- normalizing voucher selection state

- [ ] **Step 2: Extend desktop client**

Add:
- customer voucher list route
- pricing preview payload support
- sale and checkout-session payload support

- [ ] **Step 3: Extend workspace orchestration narrowly**

Keep the large workspace hook as orchestration only:
- selected customer voucher state
- mutual exclusion with shared code
- load vouchers when profile changes
- thread `customer_voucher_id` into preview, sale, and payment-session calls

- [ ] **Step 4: Extend billing UI**

Render:
- selected customer voucher list
- apply/clear voucher actions
- voucher discount posture in the summary

- [ ] **Step 5: Run targeted desktop tests to verify GREEN**

Run: `npm run test --workspace @store/store-desktop -- client.pricing-preview.test.ts StoreBillingSection.pricing-preview.test.tsx StoreRuntimeWorkspace.customer-profiles.test.tsx`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add apps/store-desktop/src/control-plane/storeVoucherActions.ts apps/store-desktop/src/control-plane/client.ts apps/store-desktop/src/control-plane/storePricingPreviewActions.ts apps/store-desktop/src/control-plane/useStoreRuntimeCheckoutPayment.ts apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts apps/store-desktop/src/control-plane/StoreBillingSection.tsx packages/types/src/index.ts
git commit -m "feat: add desktop customer voucher checkout"
```

### Task 9: Final verification and docs

**Files:**
- Modify: `docs/WORKLOG.md`

- [ ] **Step 1: Update worklog**

Record the voucher foundation slice and verification commands.

- [ ] **Step 2: Run backend verification**

Run: `C:\Users\Nebula\AppData\Local\Python\bin\python.exe -m pytest services/control-plane-api/tests/test_promotions_flow.py services/control-plane-api/tests/test_checkout_price_preview_flow.py services/control-plane-api/tests/test_billing_foundation_flow.py services/control-plane-api/tests/test_checkout_payment_sessions.py -q`
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

- [ ] **Step 5: Run hygiene check**

Run: `git -c core.safecrlf=false diff --check`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add docs/WORKLOG.md
git commit -m "docs: record customer voucher foundation"
```
