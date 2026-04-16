# Automatic Discount Foundation Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the promotion foundation with automatic cart-wide and item/category-targeted discounts, centralized checkout pricing preview, MRP-aware scan lookup, and authoritative commercial pricing snapshots for direct sales and checkout payment sessions.

**Architecture:** Add a dedicated control-plane commercial pricing seam instead of pushing more discount logic into the already large `billing.py`. The backend should own three things: catalog commercial identity (`mrp`, `category_code`, branch selling price), promotion rule evaluation (`CODE` plus `AUTOMATIC`), and a reusable pricing preview/snapshot engine that direct sale creation and checkout payment sessions both call. Preserve the current single-line Store Desktop billing posture in this slice; the preview API accepts multiple lines, but the desktop UI consumes it through the existing one-line checkout flow until a real cart builder lands later.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, Pydantic, React, TypeScript, Vitest, pytest

---

## File Structure

### Large-file governance

- `services/control-plane-api/store_control_plane/services/billing.py`
  - Classification: `mixed-responsibility`
  - Threshold: `1057` lines (`>800`)
  - Rule: do not inline automatic-discount evaluation or preview math here; extract pricing logic into a focused service and pure policy helpers.
- `apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts`
  - Classification: `mixed-responsibility`
  - Threshold: `2377` lines (`>2000`)
  - Rule: do not bolt preview-fetch orchestration and pricing transforms directly into this file; keep new behavior behind small helper actions and thin workspace state wiring.

### Backend

- Create: `services/control-plane-api/alembic/versions/20260417_0035_automatic_discount_foundation.py`
  - Adds catalog `mrp` and `category_code`, extends promotion campaigns for automatic rules, and adds commercial pricing snapshot columns to sales and sale lines.
- Modify: `services/control-plane-api/store_control_plane/models/catalog.py`
  - Persist `mrp` and `category_code` on catalog products.
- Modify: `services/control-plane-api/store_control_plane/repositories/catalog.py`
  - Create/list products with `mrp` and `category_code`.
- Modify: `services/control-plane-api/store_control_plane/schemas/catalog.py`
  - Require `mrp` on product creation, expose `mrp` and `category_code` in product and branch-item responses.
- Modify: `services/control-plane-api/store_control_plane/services/catalog.py`
  - Enforce `mrp >= selling_price`, return commercial identity in catalog reads.
- Modify: `services/control-plane-api/store_control_plane/routes/catalog.py`
  - Accept the expanded catalog payload.
- Modify: `services/control-plane-api/store_control_plane/models/promotions.py`
  - Add `trigger_mode`, `scope`, `target_product_ids`, and `target_category_codes`.
- Modify: `services/control-plane-api/store_control_plane/repositories/promotions.py`
  - Load active automatic campaigns and persist the expanded rule fields.
- Modify: `services/control-plane-api/store_control_plane/schemas/promotions.py`
  - Accept automatic cart and item/category campaign fields.
- Modify: `services/control-plane-api/store_control_plane/services/promotions.py`
  - Normalize and validate automatic campaign inputs and reject code creation for automatic campaigns.
- Create: `services/control-plane-api/store_control_plane/services/commercial_pricing_policy.py`
  - Pure pricing and allocation helpers: choose the best automatic campaign, allocate automatic and code discounts to lines, and compute stable header totals.
- Create: `services/control-plane-api/store_control_plane/services/commercial_pricing.py`
  - Orchestration service that loads branch catalog context, resolves promotions, and returns reusable preview/snapshot payloads.
- Modify: `services/control-plane-api/store_control_plane/services/__init__.py`
  - Export the new commercial pricing service.
- Modify: `services/control-plane-api/store_control_plane/models/billing.py`
  - Persist sale header and sale-line commercial snapshot fields for MRP, selling price, automatic discount, code discount, and discount source.
- Modify: `services/control-plane-api/store_control_plane/repositories/billing.py`
  - Write and serialize the expanded commercial snapshot fields.
- Modify: `services/control-plane-api/store_control_plane/schemas/billing.py`
  - Add checkout price preview request/response models and expanded sale/payment-session pricing snapshots.
- Modify: `services/control-plane-api/store_control_plane/services/billing.py`
  - Use `CommercialPricingService` for direct sale creation instead of recomputing promotion math inline.
- Modify: `services/control-plane-api/store_control_plane/services/checkout_payments.py`
  - Use `CommercialPricingService` for checkout payment-session pricing and align provider order amounts with preview.
- Modify: `services/control-plane-api/store_control_plane/routes/billing.py`
  - Add `POST /checkout-price-preview` and pass the new pricing inputs through direct-sale and checkout-session routes.
- Modify: `services/control-plane-api/store_control_plane/services/barcode.py`
  - Return `mrp`, `current selling price`, and automatic-discount-eligible posture on scan lookup.
- Modify: `services/control-plane-api/store_control_plane/schemas/barcode.py`
  - Expose `mrp` and any previewed discount posture fields in barcode lookup responses.

### Shared Types

- Modify: `packages/types/src/index.ts`
  - Add `mrp`, `category_code`, automatic promotion rule fields, checkout price preview types, and expanded sale/line/session pricing snapshot types.

### Owner Web

- Modify: `apps/owner-web/src/control-plane/client.ts`
  - Send and receive catalog `mrp/category_code`, automatic promotion fields, and campaign targeting fields.
- Modify: `apps/owner-web/src/control-plane/catalogBarcodeActions.ts`
  - Build the expanded catalog product payload.
- Modify: `apps/owner-web/src/control-plane/useOwnerWorkspace.ts`
  - Hold MRP/category draft state and route it through existing catalog creation actions.
- Modify: `apps/owner-web/src/control-plane/OwnerWorkspace.tsx`
  - Add catalog MRP/category inputs and render the new product commercial identity.
- Modify: `apps/owner-web/src/control-plane/OwnerPromotionCampaignSection.tsx`
  - Support `trigger_mode`, `scope`, product targets, and category targets for automatic campaigns.
- Modify: `apps/owner-web/src/control-plane/OwnerWorkspace.catalog.test.tsx`
  - Cover MRP/category catalog creation flow.
- Modify: `apps/owner-web/src/control-plane/OwnerWorkspace.barcode.test.tsx`
  - Cover MRP-aware barcode lookup posture.
- Modify: `apps/owner-web/src/control-plane/OwnerPromotionCampaignSection.test.tsx`
  - Cover automatic cart and item/category campaign management.

### Store Desktop

- Modify: `apps/store-desktop/src/control-plane/client.ts`
  - Add `checkoutPricePreview` client support and extend checkout payment sessions with `store_credit_amount` so preview and provider-backed checkout stay aligned.
- Create: `apps/store-desktop/src/control-plane/storePricingPreviewActions.ts`
  - Normalize pricing preview inputs and keep preview fetch logic out of `useStoreRuntimeWorkspace.ts`.
- Modify: `apps/store-desktop/src/control-plane/storePromotionActions.ts`
  - Keep promotion-code parsing compatible with preview and final sale/session payloads.
- Modify: `apps/store-desktop/src/control-plane/useStoreRuntimeCheckoutPayment.ts`
  - Include `store_credit_amount` and preview-aligned pricing inputs in checkout payment-session creation.
- Modify: `apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts`
  - Track preview result state, call the preview helper when quantity/customer/promotion/loyalty/store-credit inputs change, and thread the snapshot into direct sale creation.
- Modify: `apps/store-desktop/src/control-plane/StoreBarcodeLookupSection.tsx`
  - Show `MRP`, `selling price`, and automatic discount posture in the scan lookup surface.
- Modify: `apps/store-desktop/src/control-plane/StoreBillingSection.tsx`
  - Render line-level and summary-level commercial breakdown using preview data, while preserving the current single-line checkout UX.
- Create: `apps/store-desktop/src/control-plane/client.pricing-preview.test.ts`
  - Client coverage for the preview route and `store_credit_amount` checkout-session payloads.
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.barcode.test.tsx`
  - Cover MRP-aware scan lookup.
- Modify: `apps/store-desktop/src/control-plane/StoreBarcodeLookupSection.test.tsx`
  - Cover scan-time MRP and selling-price rendering.
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.billing.test.tsx`
  - Cover preview-driven automatic discounts, code discounts, loyalty/store-credit ordering, and parity between preview and sale/session payloads.
- Create: `apps/store-desktop/src/control-plane/StoreBillingSection.pricing-preview.test.tsx`
  - Focused UI coverage for the checkout pricing summary.
- Modify: `apps/store-desktop/src/control-plane/StoreBillingSection.payment-session.test.tsx`
  - Cover provider-backed checkout posture with preview-aligned totals.

### Tests

- Create: `services/control-plane-api/tests/test_checkout_price_preview_flow.py`
  - Focused backend route and pricing-engine coverage for automatic rules and preview totals.
- Modify: `services/control-plane-api/tests/test_promotions_flow.py`
  - Cover automatic campaign CRUD and targeting validation.
- Modify: `services/control-plane-api/tests/test_billing_foundation_flow.py`
  - Cover sale snapshots for automatic discounts, code discounts, loyalty, and store credit.
- Modify: `services/control-plane-api/tests/test_checkout_payment_sessions.py`
  - Cover preview/session amount parity and provider-backed store-credit coexistence.
- Modify: `services/control-plane-api/tests/test_barcode_foundation_flow.py`
  - Cover MRP-aware branch scan lookup.

### Docs

- Modify: `docs/WORKLOG.md`
  - Record the automatic-discount slice and verification commands.
- Modify: `docs/TASK_LEDGER.md`
  - Advance `V2-005` only if this slice changes the ledger state.

## Task 1: Add failing backend and scan-pricing tests

**Files:**
- Create: `services/control-plane-api/tests/test_checkout_price_preview_flow.py`
- Modify: `services/control-plane-api/tests/test_promotions_flow.py`
- Modify: `services/control-plane-api/tests/test_billing_foundation_flow.py`
- Modify: `services/control-plane-api/tests/test_checkout_payment_sessions.py`
- Modify: `services/control-plane-api/tests/test_barcode_foundation_flow.py`

- [ ] **Step 1: Write failing automatic-campaign tests**

Extend `services/control-plane-api/tests/test_promotions_flow.py` to cover:
- creating an `AUTOMATIC + CART` campaign
- creating an `AUTOMATIC + ITEM_CATEGORY` campaign with product targets
- rejecting automatic campaigns that omit both product and category targets for `ITEM_CATEGORY`
- rejecting shared-code creation on an automatic campaign

- [ ] **Step 2: Write the failing pricing-preview route tests**

Create `services/control-plane-api/tests/test_checkout_price_preview_flow.py` to cover:
- automatic cart discount at subtotal threshold
- automatic item-target discount on eligible lines only
- automatic category-target discount on eligible category codes only
- code plus automatic coexistence with fixed ordering
- preview response exposing line and header commercial breakdown

- [ ] **Step 3: Write failing billing and checkout-session parity tests**

Extend:
- `services/control-plane-api/tests/test_billing_foundation_flow.py`
- `services/control-plane-api/tests/test_checkout_payment_sessions.py`

Add coverage for:
- finalized sale snapshots persisting automatic and code discounts separately
- checkout payment-session amount matching preview amount
- provider-backed checkout honoring `store_credit_amount` after invoice discounts and loyalty

- [ ] **Step 4: Write the failing barcode MRP test**

Extend `services/control-plane-api/tests/test_barcode_foundation_flow.py` to assert branch scan lookup returns:
- `mrp`
- current `selling_price`
- automatic-discount eligibility posture when the scanned item is targetable

- [ ] **Step 5: Run the focused backend tests to verify they fail**

Run:
- `python -m pytest services/control-plane-api/tests/test_promotions_flow.py -q`
- `python -m pytest services/control-plane-api/tests/test_checkout_price_preview_flow.py -q`
- `python -m pytest services/control-plane-api/tests/test_billing_foundation_flow.py -q`
- `python -m pytest services/control-plane-api/tests/test_checkout_payment_sessions.py -q`
- `python -m pytest services/control-plane-api/tests/test_barcode_foundation_flow.py -q`

Expected: FAIL with missing automatic rule fields, missing preview route, missing snapshot fields, and missing `mrp` scan data.

- [ ] **Step 6: Commit**

```bash
git add services/control-plane-api/tests/test_promotions_flow.py services/control-plane-api/tests/test_checkout_price_preview_flow.py services/control-plane-api/tests/test_billing_foundation_flow.py services/control-plane-api/tests/test_checkout_payment_sessions.py services/control-plane-api/tests/test_barcode_foundation_flow.py
git commit -m "test: add automatic discount backend coverage"
```

## Task 2: Add catalog commercial identity and automatic promotion rule fields

**Files:**
- Create: `services/control-plane-api/alembic/versions/20260417_0035_automatic_discount_foundation.py`
- Modify: `services/control-plane-api/store_control_plane/models/catalog.py`
- Modify: `services/control-plane-api/store_control_plane/repositories/catalog.py`
- Modify: `services/control-plane-api/store_control_plane/schemas/catalog.py`
- Modify: `services/control-plane-api/store_control_plane/services/catalog.py`
- Modify: `services/control-plane-api/store_control_plane/routes/catalog.py`
- Modify: `services/control-plane-api/store_control_plane/models/promotions.py`
- Modify: `services/control-plane-api/store_control_plane/repositories/promotions.py`
- Modify: `services/control-plane-api/store_control_plane/schemas/promotions.py`
- Modify: `services/control-plane-api/store_control_plane/services/promotions.py`

- [ ] **Step 1: Add the migration**

Create `services/control-plane-api/alembic/versions/20260417_0035_automatic_discount_foundation.py` to:
- add `mrp` and optional `category_code` to `catalog_products`
- backfill `mrp = selling_price` for existing rows
- add `trigger_mode`, `scope`, `target_product_ids`, and `target_category_codes` to `promotion_campaigns`
- add commercial snapshot columns to `sales` and `sale_lines`

Use JSON columns for target arrays to keep the first rule engine slice simple.

- [ ] **Step 2: Extend catalog product authority**

Update:
- `models/catalog.py`
- `repositories/catalog.py`
- `schemas/catalog.py`
- `services/catalog.py`
- `routes/catalog.py`

Add:
- `mrp`
- optional `category_code`

Enforce:
- `mrp > 0`
- `selling_price > 0`
- `mrp >= selling_price`

- [ ] **Step 3: Extend promotion campaign authority**

Update:
- `models/promotions.py`
- `repositories/promotions.py`
- `schemas/promotions.py`
- `services/promotions.py`

Add:
- `trigger_mode = CODE | AUTOMATIC`
- `scope = CART | ITEM_CATEGORY`
- `target_product_ids`
- `target_category_codes`

Normalize target codes to trimmed uppercase strings and reject empty automatic targeting.

- [ ] **Step 4: Re-run the focused authority tests**

Run:
- `python -m pytest services/control-plane-api/tests/test_promotions_flow.py -q`

Expected: PASS for automatic campaign CRUD and targeting validation. `test_checkout_price_preview_flow.py` should still fail because the pricing engine and route do not exist yet.

- [ ] **Step 5: Commit**

```bash
git add services/control-plane-api/alembic/versions/20260417_0035_automatic_discount_foundation.py services/control-plane-api/store_control_plane/models/catalog.py services/control-plane-api/store_control_plane/repositories/catalog.py services/control-plane-api/store_control_plane/schemas/catalog.py services/control-plane-api/store_control_plane/services/catalog.py services/control-plane-api/store_control_plane/routes/catalog.py services/control-plane-api/store_control_plane/models/promotions.py services/control-plane-api/store_control_plane/repositories/promotions.py services/control-plane-api/store_control_plane/schemas/promotions.py services/control-plane-api/store_control_plane/services/promotions.py
git commit -m "feat: add automatic promotion and catalog pricing fields"
```

## Task 3: Implement reusable commercial pricing preview and snapshots

**Files:**
- Create: `services/control-plane-api/store_control_plane/services/commercial_pricing_policy.py`
- Create: `services/control-plane-api/store_control_plane/services/commercial_pricing.py`
- Modify: `services/control-plane-api/store_control_plane/services/__init__.py`
- Modify: `services/control-plane-api/store_control_plane/schemas/billing.py`
- Modify: `services/control-plane-api/store_control_plane/services/barcode.py`
- Modify: `services/control-plane-api/store_control_plane/schemas/barcode.py`
- Create: `services/control-plane-api/tests/test_checkout_price_preview_flow.py`
- Modify: `services/control-plane-api/tests/test_barcode_foundation_flow.py`

- [ ] **Step 1: Build pure pricing-policy helpers**

Create `services/control-plane-api/store_control_plane/services/commercial_pricing_policy.py` with pure helpers for:
- selecting the best eligible automatic campaign
- allocating automatic cart discounts proportionally across eligible lines
- applying item/category-target discounts line-by-line
- allocating code discounts after automatic discounts with stable rounding and last-line remainder handling
- computing line snapshots:
  - `mrp`
  - `unit_selling_price`
  - `automatic_discount_amount`
  - `promotion_code_discount_amount`
  - `promotion_discount_source`
  - `taxable_amount`
  - `tax_amount`
  - `line_total`
- computing header totals:
  - `mrp_total`
  - `selling_price_subtotal`
  - `automatic_discount_total`
  - `promotion_code_discount_total`
  - `total_discount`
  - `tax_total`
  - `invoice_total`

- [ ] **Step 2: Build the orchestration service**

Create `services/control-plane-api/store_control_plane/services/commercial_pricing.py` to:
- load branch catalog products and branch-item selling posture
- load active automatic campaigns
- resolve optional code campaigns through `PromotionService`
- call the pure pricing helpers
- optionally apply loyalty and store-credit posture for preview final-payable output
- return a reusable preview object for direct sale creation and checkout sessions

- [ ] **Step 3: Add billing preview schemas**

Extend `services/control-plane-api/store_control_plane/schemas/billing.py` with:
- `CheckoutPricePreviewRequest`
- `CheckoutPricePreviewLineResponse`
- `CheckoutPricePreviewSummaryResponse`
- `CheckoutPricePreviewResponse`

Include preview fields for:
- applied automatic campaign snapshot
- applied code campaign snapshot
- loyalty/store-credit posture
- final payable amount

- [ ] **Step 4: Extend scan lookup to expose commercial posture**

Update:
- `services/control-plane-api/store_control_plane/services/barcode.py`
- `services/control-plane-api/store_control_plane/schemas/barcode.py`

Return:
- `mrp`
- current `selling_price`
- optional automatic-discount preview posture for the scanned SKU

- [ ] **Step 5: Re-run the preview and barcode tests**

Run:
- `python -m pytest services/control-plane-api/tests/test_checkout_price_preview_flow.py -q`
- `python -m pytest services/control-plane-api/tests/test_barcode_foundation_flow.py -q`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add services/control-plane-api/store_control_plane/services/commercial_pricing_policy.py services/control-plane-api/store_control_plane/services/commercial_pricing.py services/control-plane-api/store_control_plane/services/__init__.py services/control-plane-api/store_control_plane/schemas/billing.py services/control-plane-api/store_control_plane/services/barcode.py services/control-plane-api/store_control_plane/schemas/barcode.py services/control-plane-api/tests/test_checkout_price_preview_flow.py services/control-plane-api/tests/test_barcode_foundation_flow.py
git commit -m "feat: add checkout commercial pricing preview"
```

## Task 4: Integrate commercial pricing into direct sales and checkout payment sessions

**Files:**
- Modify: `services/control-plane-api/store_control_plane/models/billing.py`
- Modify: `services/control-plane-api/store_control_plane/repositories/billing.py`
- Modify: `services/control-plane-api/store_control_plane/services/billing.py`
- Modify: `services/control-plane-api/store_control_plane/services/checkout_payments.py`
- Modify: `services/control-plane-api/store_control_plane/routes/billing.py`
- Modify: `services/control-plane-api/tests/test_billing_foundation_flow.py`
- Modify: `services/control-plane-api/tests/test_checkout_payment_sessions.py`
- Modify: `packages/types/src/index.ts`

- [ ] **Step 1: Add sale and sale-line commercial snapshot fields**

Update `models/billing.py` and `repositories/billing.py` so sales persist:
- `automatic_campaign_id`
- `automatic_campaign_name`
- `automatic_discount_total`
- `promotion_code_discount_total`
- `mrp_total`
- `selling_price_subtotal`
- `total_discount`
- `invoice_total`

And sale lines persist:
- `mrp`
- `unit_selling_price`
- `automatic_discount_amount`
- `promotion_code_discount_amount`
- `promotion_discount_source`
- `taxable_amount`
- `tax_amount`
- `line_total`

- [ ] **Step 2: Replace inline sale discount math with pricing preview output**

Update `services/control-plane-api/store_control_plane/services/billing.py` so direct sale creation:
- calls `CommercialPricingService`
- persists the previewed line and header snapshots
- applies loyalty after invoice discounts
- applies store credit after loyalty
- keeps payment rows and inventory posting behavior unchanged otherwise

- [ ] **Step 3: Align checkout payment sessions with preview**

Update:
- `services/control-plane-api/store_control_plane/services/checkout_payments.py`
- `services/control-plane-api/store_control_plane/routes/billing.py`
- `services/control-plane-api/store_control_plane/schemas/billing.py`

So checkout payment-session creation:
- accepts `store_credit_amount`
- calls the same pricing preview service
- stores the commercial breakdown in `cart_snapshot`
- sets `order_amount` to the previewed final payable amount

- [ ] **Step 4: Add the preview route**

In `services/control-plane-api/store_control_plane/routes/billing.py`, add:
- `POST /v1/tenants/{tenant_id}/branches/{branch_id}/checkout-price-preview`

The handler should only call `CommercialPricingService` and return the preview response; it should not mutate sales, payments, or inventory.

- [ ] **Step 5: Extend shared TypeScript contracts**

Update `packages/types/src/index.ts` with:
- catalog `mrp` and `category_code`
- automatic campaign trigger/scope/targets
- checkout price preview types
- sale and checkout-session commercial snapshot fields

- [ ] **Step 6: Re-run focused billing and payment-session tests**

Run:
- `python -m pytest services/control-plane-api/tests/test_billing_foundation_flow.py -q`
- `python -m pytest services/control-plane-api/tests/test_checkout_payment_sessions.py -q`

Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add services/control-plane-api/store_control_plane/models/billing.py services/control-plane-api/store_control_plane/repositories/billing.py services/control-plane-api/store_control_plane/services/billing.py services/control-plane-api/store_control_plane/services/checkout_payments.py services/control-plane-api/store_control_plane/routes/billing.py services/control-plane-api/store_control_plane/schemas/billing.py services/control-plane-api/tests/test_billing_foundation_flow.py services/control-plane-api/tests/test_checkout_payment_sessions.py packages/types/src/index.ts
git commit -m "feat: apply automatic discounts in billing"
```

## Task 5: Extend owner-web catalog and promotion management for the new pricing model

**Files:**
- Modify: `apps/owner-web/src/control-plane/client.ts`
- Modify: `apps/owner-web/src/control-plane/catalogBarcodeActions.ts`
- Modify: `apps/owner-web/src/control-plane/useOwnerWorkspace.ts`
- Modify: `apps/owner-web/src/control-plane/OwnerWorkspace.tsx`
- Modify: `apps/owner-web/src/control-plane/OwnerPromotionCampaignSection.tsx`
- Modify: `apps/owner-web/src/control-plane/OwnerWorkspace.catalog.test.tsx`
- Modify: `apps/owner-web/src/control-plane/OwnerWorkspace.barcode.test.tsx`
- Modify: `apps/owner-web/src/control-plane/OwnerPromotionCampaignSection.test.tsx`

- [ ] **Step 1: Write failing owner-web tests**

Update:
- `OwnerWorkspace.catalog.test.tsx`
- `OwnerWorkspace.barcode.test.tsx`
- `OwnerPromotionCampaignSection.test.tsx`

Cover:
- creating a catalog product with `mrp` and optional `category_code`
- rendering MRP-aware barcode lookup posture
- creating automatic cart campaigns
- creating automatic item/category campaigns

- [ ] **Step 2: Run the focused owner-web tests to verify they fail**

Run:
- `npm run test --workspace @store/owner-web -- OwnerWorkspace.catalog.test.tsx`
- `npm run test --workspace @store/owner-web -- OwnerWorkspace.barcode.test.tsx`
- `npm run test --workspace @store/owner-web -- OwnerPromotionCampaignSection.test.tsx`

Expected: FAIL with missing client fields, missing UI inputs, or missing automatic campaign controls.

- [ ] **Step 3: Extend catalog product creation**

Update:
- `apps/owner-web/src/control-plane/client.ts`
- `apps/owner-web/src/control-plane/catalogBarcodeActions.ts`
- `apps/owner-web/src/control-plane/useOwnerWorkspace.ts`
- `apps/owner-web/src/control-plane/OwnerWorkspace.tsx`

Add owner inputs for:
- `MRP`
- optional `category_code`

Display the new commercial identity in:
- latest catalog product
- latest branch catalog item where useful

- [ ] **Step 4: Extend promotion management**

Update `OwnerPromotionCampaignSection.tsx` and `client.ts` to handle:
- `trigger_mode`
- `scope`
- `target_product_ids`
- `target_category_codes`

Keep the first slice simple by using text inputs for comma-separated ids/codes rather than a richer product picker.

- [ ] **Step 5: Re-run focused owner-web tests and typecheck**

Run:
- `npm run test --workspace @store/owner-web -- OwnerWorkspace.catalog.test.tsx`
- `npm run test --workspace @store/owner-web -- OwnerWorkspace.barcode.test.tsx`
- `npm run test --workspace @store/owner-web -- OwnerPromotionCampaignSection.test.tsx`
- `npm run typecheck --workspace @store/owner-web`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add apps/owner-web/src/control-plane/client.ts apps/owner-web/src/control-plane/catalogBarcodeActions.ts apps/owner-web/src/control-plane/useOwnerWorkspace.ts apps/owner-web/src/control-plane/OwnerWorkspace.tsx apps/owner-web/src/control-plane/OwnerPromotionCampaignSection.tsx apps/owner-web/src/control-plane/OwnerWorkspace.catalog.test.tsx apps/owner-web/src/control-plane/OwnerWorkspace.barcode.test.tsx apps/owner-web/src/control-plane/OwnerPromotionCampaignSection.test.tsx
git commit -m "feat: add owner automatic discount management"
```

## Task 6: Add Store Desktop scan-time and checkout-time pricing preview

**Files:**
- Modify: `apps/store-desktop/src/control-plane/client.ts`
- Create: `apps/store-desktop/src/control-plane/storePricingPreviewActions.ts`
- Modify: `apps/store-desktop/src/control-plane/storePromotionActions.ts`
- Modify: `apps/store-desktop/src/control-plane/useStoreRuntimeCheckoutPayment.ts`
- Modify: `apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts`
- Modify: `apps/store-desktop/src/control-plane/StoreBarcodeLookupSection.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreBillingSection.tsx`
- Create: `apps/store-desktop/src/control-plane/client.pricing-preview.test.ts`
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.barcode.test.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreBarcodeLookupSection.test.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.billing.test.tsx`
- Create: `apps/store-desktop/src/control-plane/StoreBillingSection.pricing-preview.test.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreBillingSection.payment-session.test.tsx`

- [ ] **Step 1: Write failing desktop pricing tests**

Add or extend tests for:
- scan lookup showing `MRP` and `selling price`
- preview response driving automatic discounts in the billing summary
- promotion-code changes refreshing the preview
- provider-backed checkout using preview-aligned totals with `store_credit_amount`

- [ ] **Step 2: Run the focused desktop tests to verify they fail**

Run:
- `npm run test --workspace @store/store-desktop -- client.pricing-preview.test.ts`
- `npm run test --workspace @store/store-desktop -- StoreRuntimeWorkspace.barcode.test.tsx`
- `npm run test --workspace @store/store-desktop -- StoreBarcodeLookupSection.test.tsx`
- `npm run test --workspace @store/store-desktop -- StoreRuntimeWorkspace.billing.test.tsx`
- `npm run test --workspace @store/store-desktop -- StoreBillingSection.pricing-preview.test.tsx`
- `npm run test --workspace @store/store-desktop -- StoreBillingSection.payment-session.test.tsx`

Expected: FAIL with missing preview client support, missing MRP rendering, or missing pricing summary state.

- [ ] **Step 3: Add the preview client and helper actions**

Update `client.ts` to add:
- `checkoutPricePreview(...)`
- `store_credit_amount` on checkout payment-session creation

Create `storePricingPreviewActions.ts` to:
- build preview payloads from the existing single-line desktop checkout state
- normalize preview errors
- keep preview fetch timing out of `useStoreRuntimeWorkspace.ts`

- [ ] **Step 4: Wire preview state into the runtime workspace**

Update `useStoreRuntimeWorkspace.ts` to:
- hold latest preview result
- refresh preview when quantity, customer, promotion code, loyalty points, or store credit changes
- reuse preview output when building direct-sale payloads
- keep the current one-line checkout posture instead of building a new cart system

- [ ] **Step 5: Extend scan lookup and billing UI**

Update:
- `StoreBarcodeLookupSection.tsx`
- `StoreBillingSection.tsx`

Render:
- scan-time `MRP`
- scan-time current `selling price`
- applied automatic campaign name if present
- line-level discount/tax/line-total posture
- summary:
  - MRP total
  - selling subtotal
  - automatic discount
  - code discount
  - loyalty discount
  - total discount
  - tax
  - invoice total
  - store credit used
  - remaining payable
  - paid-source posture once sale/session exists

- [ ] **Step 6: Re-run focused desktop tests and typecheck**

Run:
- `npm run test --workspace @store/store-desktop -- client.pricing-preview.test.ts`
- `npm run test --workspace @store/store-desktop -- StoreRuntimeWorkspace.barcode.test.tsx`
- `npm run test --workspace @store/store-desktop -- StoreBarcodeLookupSection.test.tsx`
- `npm run test --workspace @store/store-desktop -- StoreRuntimeWorkspace.billing.test.tsx`
- `npm run test --workspace @store/store-desktop -- StoreBillingSection.pricing-preview.test.tsx`
- `npm run test --workspace @store/store-desktop -- StoreBillingSection.payment-session.test.tsx`
- `npm run typecheck --workspace @store/store-desktop`

Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add apps/store-desktop/src/control-plane/client.ts apps/store-desktop/src/control-plane/storePricingPreviewActions.ts apps/store-desktop/src/control-plane/storePromotionActions.ts apps/store-desktop/src/control-plane/useStoreRuntimeCheckoutPayment.ts apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts apps/store-desktop/src/control-plane/StoreBarcodeLookupSection.tsx apps/store-desktop/src/control-plane/StoreBillingSection.tsx apps/store-desktop/src/control-plane/client.pricing-preview.test.ts apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.barcode.test.tsx apps/store-desktop/src/control-plane/StoreBarcodeLookupSection.test.tsx apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.billing.test.tsx apps/store-desktop/src/control-plane/StoreBillingSection.pricing-preview.test.tsx apps/store-desktop/src/control-plane/StoreBillingSection.payment-session.test.tsx
git commit -m "feat: add desktop automatic discount preview"
```

## Task 7: Run full verification and update docs

**Files:**
- Modify: `docs/WORKLOG.md`
- Modify: `docs/TASK_LEDGER.md`

- [ ] **Step 1: Update worklog and ledger**

Record the automatic-discount slice in `docs/WORKLOG.md`, and update `docs/TASK_LEDGER.md` only if this slice changes the visible `V2-005` status.

- [ ] **Step 2: Run backend verification**

Run:
`python -m pytest services/control-plane-api/tests/test_promotions_flow.py services/control-plane-api/tests/test_checkout_price_preview_flow.py services/control-plane-api/tests/test_billing_foundation_flow.py services/control-plane-api/tests/test_checkout_payment_sessions.py services/control-plane-api/tests/test_barcode_foundation_flow.py -q`

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

Run:
`git -c core.safecrlf=false diff --check`

Expected: no output

- [ ] **Step 6: Commit**

```bash
git add docs/WORKLOG.md docs/TASK_LEDGER.md
git commit -m "docs: record automatic discount foundation slice"
```
