# Automatic Discount Foundation Design

Date: 2026-04-17  
Owner: Codex  
Status: Approved for implementation

## Goal

Extend the new `promotion code foundation` into a unified `automatic discount` foundation so `V2-005` can support:

- automatic cart-wide discounts
- automatic item/category-targeted discounts
- transparent scan-time and cart-time pricing posture
- authoritative sale-line and sale-header pricing snapshots

This slice should make commercial pricing clearer and more operationally credible:

- barcode scan should immediately show `MRP` and `current selling price`
- checkout should show line discounts, total discounts, taxes, invoice total, store credit used, final payable, and paid sources
- item/category-specific discounts should be supported through the same promotion authority as coupon codes

## Scope

This slice expands the existing promotion foundation from `code-only` campaigns into a unified rule model with `automatic` campaigns.

Included:

- automatic cart-wide discount campaigns
- automatic item/category-targeted discount campaigns
- one best automatic campaign per sale in the first slice
- coexistence with one optional cashier-entered promotion code
- centralized pricing preview for desktop checkout
- line-level and header-level pricing snapshots on finalized sales
- owner-web campaign management for automatic rules
- Store Desktop commercial breakdown for scan/cart/checkout posture

Not included:

- manual cashier price override
- stacked multi-automatic campaigns
- multiple promotion codes on one sale
- best-of-many complex promo arbitration
- customer-assigned vouchers
- mobile/tablet automatic promotion UX
- promotional wallets or expiring promotional balances
- scan-event writes into the inventory ledger

## Recommended Approach

Use one unified `promotion campaign` system with two trigger modes:

- `CODE`
- `AUTOMATIC`

Why:

- promotion authority remains in one place
- sale creation, payment session creation, and pricing preview stay consistent
- owner-web does not need a second promotions product area
- later extensions like customer-assigned vouchers or more advanced rule composition can build on the same campaign model

## Why Price Must Be Split Across Live Source And Historical Snapshot

Barcode scan should immediately show the item's commercial posture, but that does not mean every scan belongs in the ledger.

Recommended model:

- `live price source`
  - branch lookup resolves product identity
  - returns `MRP`, `current selling price`, and eligible discount posture
- `sale snapshot`
  - persists the exact pricing that was actually charged

What should not happen:

- barcode scan should not post inventory ledger entries
- pricing lookup should not pollute the stock-movement ledger

The inventory ledger stays stock-only.  
Pricing truth belongs in commercial price sources and finalized billing snapshots.

## Architecture

### Authority Model

Automatic discount evaluation must remain control-plane authority only.

Rules:

- desktop must not compute final automatic discount math on its own
- item/category targeting must be resolved on the backend
- direct sale creation and payment-session creation must use the same evaluation logic
- checkout preview must use that same evaluation logic
- historical invoices must preserve the exact applied pricing truth even if campaign rules change later

### Promotion Engine Boundary

The promotion engine should evaluate two lanes:

1. `automatic campaign`
2. `cashier-entered promotion code`

For this first slice:

- at most one best automatic campaign applies
- at most one code campaign applies
- backend computes both in a fixed order
- both are snapshotted explicitly

This keeps the system understandable while still covering the real store need for item/category-specific discounts.

## Data Model

### Promotion Campaigns

Extend the existing `promotion_campaigns` model with:

- `trigger_mode`
  - `CODE`
  - `AUTOMATIC`
- `scope`
  - `CART`
  - `ITEM_CATEGORY`
- `target_product_ids | null`
- `target_category_codes | null`

Existing fields continue to matter:

- `status`
- `discount_type`
- `discount_value`
- `minimum_order_amount`
- `maximum_discount_amount`
- `redemption_limit_total`
- `redemption_count`

Rules:

- `CODE` campaigns continue using shared codes
- `AUTOMATIC` campaigns do not need a code
- `CART` campaigns target the whole order
- `ITEM_CATEGORY` campaigns target only eligible lines

### Sale Line Snapshot

Finalized sale lines should store:

- `mrp`
- `unit_selling_price`
- `quantity`
- `promotion_discount_amount`
- `promotion_discount_source`
- `taxable_amount`
- `tax_amount`
- `line_total`

This preserves the exact line-level pricing truth.

### Sale Header Snapshot

Finalized sale headers should store:

- `mrp_total`
- `selling_price_subtotal`
- `automatic_discount_total`
- `promotion_code_discount_total`
- `loyalty_discount_total`
- `total_discount`
- `tax_total`
- `invoice_total`
- `store_credit_amount`
- paid-source summary

This creates a transparent commercial audit trail.

## Pricing Rules

### Scan-Time And Cart-Time Visibility

When an item barcode is scanned, the UI should immediately show:

- `MRP`
- `current selling price`
- whether an automatic item/category discount is eligible

When the item is in cart, the UI should show:

- MRP
- selling price
- quantity
- line discount
- tax
- final line total

### Automatic Cart Rule

Example:

- `5% off orders above 1000`

This is evaluated against the cart as a whole.

### Automatic Item/Category Rule

Examples:

- `10% off all tea items`
- `50 off this SKU`

This is evaluated only against eligible lines.

### Fixed Ordering

Recommended order:

1. base selling price and line tax posture
2. automatic discount
3. cashier-entered promotion code discount
4. loyalty discount
5. store credit redemption
6. remaining payment settlement

Why:

- automatic and code discounts are invoice discounts
- loyalty remains a separate rewards discount instrument
- store credit remains money-like tender and must not be modeled as a discount

### First-Slice Constraint Set

To avoid discount chaos in the first slice:

- one best automatic campaign maximum
- one code campaign maximum
- no stacked automatic campaigns
- no multiple codes
- no manual cashier override

## API Boundary

### Promotion Campaign Management

Extend the existing promotion campaign surface so owner-web can manage:

- code-based cart campaigns
- automatic cart campaigns
- automatic item/category campaigns

The route family can stay under:

- `GET /v1/tenants/{tenant_id}/promotion-campaigns`
- `POST /v1/tenants/{tenant_id}/promotion-campaigns`
- `PATCH /v1/tenants/{tenant_id}/promotion-campaigns/{campaign_id}`
- nested code routes where applicable

### Pricing Preview

Add a centralized checkout preview route:

- `POST /v1/tenants/{tenant_id}/branches/{branch_id}/checkout-price-preview`

Input:

- lines
- optional `customer_profile_id`
- optional `promotion_code`

Output:

- line pricing breakdown
- cart summary breakdown
- applied automatic campaign snapshot
- applied code campaign snapshot
- invoice total before payment settlement
- final payable after loyalty and store-credit posture if those are included in preview scope

This route keeps React from duplicating pricing logic.

### Billing And Checkout Sessions

Sale creation and checkout payment session creation should continue accepting:

- lines
- optional `customer_profile_id`
- optional `promotion_code`

Backend responsibilities:

- evaluate automatic rules
- evaluate the optional code
- compute line and header snapshots
- persist promotion snapshots
- keep payment-session amount aligned with preview amount

## Owner Web Surface

Owner web should extend the existing promotion-management area rather than inventing a separate pricing app.

Owners should be able to create and manage:

- code cart campaigns
- automatic cart campaigns
- automatic item/category campaigns

The UI should expose:

- trigger mode
- scope
- item/category targeting inputs
- discount type/value
- minimum order and cap fields
- status and redemption posture

## Store Desktop Surface

Store Desktop should continue using the existing checkout surface.

When an item is scanned or selected, desktop should show:

- `MRP`
- `selling price`
- any active automatic discount posture

When the item is in cart, desktop should consume pricing preview and show:

- line-level breakdown
- automatic discount
- code discount
- loyalty discount
- total discount
- tax
- invoice total
- store credit used
- remaining payable
- paid sources

This should work for:

- direct sale creation
- Cashfree checkout session creation

## Reporting And Audit Expectations

The finalized invoice should preserve exact pricing truth, not just the final grand total.

That means commercial reporting can later answer:

- what was the MRP
- what selling price was used
- which automatic campaign applied
- which code applied
- how much discount came from each lane
- how much was reduced by loyalty
- how much was settled through store credit
- what remaining amount was paid by tender

## Testing Expectations

Backend tests should prove:

- automatic cart rule application
- automatic item/category rule application
- automatic and code coexistence with fixed ordering
- stable line allocations
- payment-session amount equals preview amount
- finalized sales persist line/header pricing truth

Store Desktop tests should prove:

- scan/cart posture shows MRP and selling price
- pricing preview updates totals
- code entry changes the commercial breakdown
- loyalty and store credit remain distinct from invoice discounts

Owner-web tests should prove:

- automatic cart campaign creation
- automatic item/category campaign creation
- existing code campaign management still works

## Exit Criteria

This slice is complete when:

- stores can define automatic cart discounts
- stores can define automatic item/category discounts
- barcode/cart flow shows transparent commercial pricing posture
- sale lines and sale headers persist exact pricing truth
- store credit remains a payment source, not a discount
- the control plane remains the only pricing authority
