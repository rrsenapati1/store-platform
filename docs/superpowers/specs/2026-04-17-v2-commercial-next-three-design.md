# V2 Commercial Next Three Slices Design

Date: 2026-04-17  
Owner: Codex  
Status: Approved by standing user authorization for serial implementation without further review stops

## Goal

Implement the next three coherent `V2-005` commercial slices in sequence:

1. `promotion arbitration controls`
2. `price tier foundation`
3. `customer price-tier checkout application`

These three slices extend the current promotion, voucher, loyalty, store-credit, and pricing-preview foundations without opening a new product track.

## Why These Three

The current commercial stack already supports:

- shared promotion codes
- automatic discounts
- customer-assigned vouchers
- store credit
- loyalty
- authoritative checkout pricing preview

The next weakest gaps are:

- no owner-controlled priority when multiple automatic campaigns are eligible
- no configurable rule for whether a manual promotion can stack with an automatic campaign
- no multi-price tier support for branch catalog selling
- no customer-linked commercial price posture beyond loyalty/store-credit/vouchers

These three slices close those gaps in dependency order.

## Slice 1: Promotion Arbitration Controls

### Goal

Make promotion interaction deterministic and operator-configurable instead of relying on the current implicit “best discount plus current stacking assumptions” behavior.

### Scope

Included:

- `priority` on promotion campaigns
- `stacking_rule` on promotion campaigns
- deterministic automatic campaign selection by priority first, discount second
- deterministic arbitration between one automatic campaign and one manual promotion instrument
  - shared code or assigned voucher
- owner-web management of those fields
- pricing preview, sale creation, and checkout-session behavior updated to match the new arbitration rules

Not included:

- stacking multiple automatic campaigns
- stacking multiple manual campaigns
- “best combination” search across many campaigns

### Rules

- still allow at most:
  - one automatic campaign
  - one manual promotion instrument
- if both selected campaigns are `STACKABLE`, both apply
- if either selected campaign is `EXCLUSIVE`, only one survives
- the survivor is chosen by:
  1. higher `priority`
  2. then larger discount amount
  3. then stable deterministic fallback by campaign id

This keeps the rule engine bounded while giving owners real control.

## Slice 2: Price Tier Foundation

### Goal

Add first-class price tiers for branch selling without mutating the inventory ledger or overloading customer tags.

### Scope

Included:

- tenant-owned price tiers
- branch product prices per tier
- owner-web price-tier management
- owner-web branch tier-price assignment for existing catalog items
- control-plane reads that expose available tiers and tier prices

Not included:

- branch-wide default tier switching
- per-invoice manual cashier price override
- tiered wholesale order rules

### Data Model

Add:

- `price_tiers`
  - `id`
  - `tenant_id`
  - `name`
  - `status`
  - `priority`
- `branch_catalog_tier_prices`
  - `id`
  - `tenant_id`
  - `branch_id`
  - `product_id`
  - `price_tier_id`
  - `selling_price`

Current `selling_price` and `selling_price_override` remain the base/default selling posture.

## Slice 3: Customer Price-Tier Checkout Application

### Goal

Let a selected customer profile carry a default commercial price tier that changes checkout pricing automatically and visibly.

### Scope

Included:

- nullable `default_price_tier_id` on customer profiles
- owner-web customer assignment/clear flow
- pricing preview uses the customer default tier price when available
- Store Desktop checkout shows selected price tier posture
- sale and checkout-session snapshots persist tier identity
- desktop orchestration extraction so the huge runtime workspace file does not absorb more mixed commercial logic

Not included:

- cashier manual tier picker
- tier-specific promotions
- tier-specific loyalty rules

### Pricing Rules

- if no customer profile is selected, pricing uses existing base/branch selling price
- if a customer profile has a default active price tier:
  - use the tier price when a branch tier price exists for that product
  - otherwise fall back to the existing branch/base selling price
- all discounts apply on top of the effective tier-adjusted selling price
- sale-line snapshots still store the exact `unit_selling_price` actually charged
- sale and payment-session headers add:
  - `price_tier_id`
  - `price_tier_name`

## Architecture

### Control Plane

Extend the existing commercial authority rather than creating a second pricing subsystem.

- promotions remain the single discount engine
- checkout pricing remains the single commercial calculation boundary
- price tiers become an additional input to checkout pricing
- billing and checkout-payment sessions remain snapshot consumers of pricing output

### Owner Web

Keep management in existing commercial/customer surfaces:

- promotion fields stay in `OwnerPromotionCampaignSection`
- price-tier management gets a dedicated owner section
- customer default price tier stays in `OwnerCustomerInsightsSection`

### Store Desktop

Keep checkout authority in the existing preview-driven flow, but avoid bloating the 2400-line workspace hook.

Required extraction seam:

- move customer-commercial loading and selection behavior into focused helper actions
- keep `useStoreRuntimeWorkspace.ts` as orchestration-only glue for the new fields

## Testing

Backend:

- promotion arbitration scenarios
- price tier create/list/update and branch tier-price upsert
- preview/sale/session behavior with default customer price tiers

Owner Web:

- campaign priority/stacking management
- price tier management and branch tier-price assignment
- customer default price tier assignment

Store Desktop:

- preview reflects selected customer tier
- checkout shows tier posture and resulting unit price
- direct sale and provider-backed checkout send the tier-aware pricing inputs and consume the tier snapshot outputs

## Success Criteria

This three-slice run is complete when:

- owners can control promotion priority and stacking posture
- the commercial engine chooses promotions deterministically
- owners can define price tiers and assign branch product prices to them
- customer profiles can carry a default price tier
- desktop checkout automatically prices selected customers against their tier
- sale/payment snapshots preserve promotion and tier truth
- desktop orchestration grows through focused helper seams instead of deepening the current 2400-line mixed workspace hook
