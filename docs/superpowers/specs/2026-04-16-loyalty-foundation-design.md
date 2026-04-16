# Loyalty Foundation Design

Date: 2026-04-16  
Owner: Codex  
Status: Approved for implementation

## Goal

Add a first-class `loyalty points` foundation on top of the new customer-profile and store-credit foundations so `V2-005` can support customer-linked earning and redemption without mixing loyalty value with money-like store credit.

This slice should make loyalty operational immediately:

- owners can configure one tenant loyalty program
- owners can review customer loyalty posture and apply manual point adjustments
- Store Desktop can load customer point balance during checkout
- finalized sales can earn points
- checkout can redeem allowed points as a bounded discount

## Scope

This slice establishes `loyalty points` as a non-cash customer rewards ledger.

Included:

- control-plane loyalty program, loyalty account, and loyalty ledger authority
- one active tenant-wide loyalty program for the first slice
- customer loyalty balances tied to `customer_profile_id`
- basic earn-rate and redeem-step configuration
- owner-web loyalty program management
- owner-web customer loyalty summary and manual point adjustment
- Store Desktop loyalty balance visibility during checkout
- checkout redemption through configured step rules
- loyalty earning on finalized sales
- loyalty reversal and restoration behavior on approved sale returns
- sale snapshot fields that record loyalty redemption and earning results

Not included:

- promotional vouchers or promotional credit
- point expiry
- tiering, segmentation, or campaign automation
- referral logic
- customer self-service loyalty portals
- mobile or tablet loyalty redemption
- omnichannel loyalty behavior
- multi-program support per tenant

## Recommended Approach

Use a dedicated control-plane `loyalty points ledger` with one tenant program, one customer account summary, and append-only ledger entries.

Why:

- loyalty points are not money and should not reuse the store-credit model
- customer balance, redemption, and reversal logic need durable authority and replay-safe writes
- owner-facing configuration is small enough to keep this slice bounded
- later promotions can compose with loyalty instead of being conflated with it

## Why Loyalty Must Stay Separate From Store Credit

Loyalty points should remain a rewards instrument, not a liability balance.

That means:

- loyalty points are not cash-equivalent
- redemption applies as a discount, not as a payment tender
- store credit remains tenant liability
- future promotional vouchers remain a separate instrument with their own rules

Mixing these systems now would make later commercial controls harder:

- accounting and rewards logic would blur
- cash-like customer balances would be confused with points
- later promotions and expiring vouchers would inherit the wrong semantics

## Architecture

### Authority Model

Loyalty must remain control-plane authority only.

Rules:

- no runtime-local loyalty balance is authoritative
- no earning or redemption without control-plane validation
- no destructive edits to historical loyalty activity
- all point movement is append-only through ledger entries

### Core Model

Add three related models:

1. `tenant_loyalty_programs`
2. `customer_loyalty_accounts`
3. `customer_loyalty_ledger_entries`

The program stores tenant rules.  
The account stores a summarized balance per tenant and customer profile.  
The ledger is the append-only source of truth for earning, redemption, adjustment, and reversal.

## Data Model

### Tenant Loyalty Program

One active program per tenant for this slice.

Recommended fields:

- `id`
- `tenant_id`
- `status`
  - `ACTIVE`
  - `DISABLED`
- `earn_points_per_currency_unit`
- `redeem_step_points`
- `redeem_value_per_step`
- `minimum_redeem_points`
- `created_at`
- `updated_at`

This model intentionally stays small. The first slice should not add tiers, categories, or campaign scoping.

### Customer Loyalty Account

One row per `tenant_id + customer_profile_id`.

Recommended fields:

- `id`
- `tenant_id`
- `customer_profile_id`
- `available_points`
- `earned_total`
- `redeemed_total`
- `adjusted_total`
- `reversed_total`
- `created_at`
- `updated_at`

This is a convenience summary only. The ledger remains authoritative.

### Customer Loyalty Ledger Entries

Ledger entries are append-only.

Recommended fields:

- `id`
- `tenant_id`
- `customer_profile_id`
- `branch_id | null`
- `entry_type`
  - `EARNED`
  - `REDEEMED`
  - `ADJUSTED`
  - `REVERSED`
- `points_delta`
- `balance_after`
- `source_type`
  - `SALE`
  - `SALE_RETURN`
  - `MANUAL_ADJUSTMENT`
- `source_reference_id`
- `note | null`
- `actor_user_id | null`
- `created_at`

## Loyalty Rules

### Program Scope

The first slice uses a tenant-wide program.

That means:

- one configured earn and redeem rule applies across all branches
- branch-level differences are deferred
- ledger entries still record branch context for audit when relevant

### Customer Eligibility

Only selected `customer_profile_id` checkouts can earn or redeem loyalty.

That means:

- anonymous checkout cannot earn points
- anonymous checkout cannot redeem points
- customer linkage must be explicit before finalization

### Earning

Points are earned only after the sale becomes authoritative.

Recommended rule:

- calculate eligible spend after all applied loyalty discount
- optionally after store-credit redemption if the implementation uses net payable as the rewards basis
- convert eligible spend to points using the tenant earn rate
- round deterministically at the backend

The backend owns this math entirely.

### Redemption

Redemption uses configured step rules, not free-form rupee entry.

Rules:

- customer must have at least `minimum_redeem_points`
- redemption must be in multiples of `redeem_step_points`
- redemption value is derived from `redeem_value_per_step`
- backend caps redemption so it never exceeds sale total or configured eligibility

This keeps cashier behavior simple and backend validation deterministic.

### Discount Semantics

Loyalty redemption is a discount instrument, not a payment method.

That means:

- loyalty reduces payable amount
- loyalty does not replace cash, UPI, Cashfree, or store credit as a tender type
- checkout can still combine loyalty discount with store credit and payment-method settlement

### Returns

Approved sale returns must reconcile loyalty effects on the backend.

Rules:

- reverse points earned from the returned sale proportionally
- restore redeemed points proportionally if the original sale used loyalty redemption
- use append-only reversal or restore entries instead of mutating historical records

## API Boundary

### Loyalty Program

Add a tenant loyalty surface:

- `GET /v1/tenants/{tenant_id}/loyalty-program`
- `PUT /v1/tenants/{tenant_id}/loyalty-program`

### Customer Loyalty

Add customer loyalty read and adjustment:

- `GET /v1/tenants/{tenant_id}/customer-profiles/{customer_profile_id}/loyalty`
- `POST /v1/tenants/{tenant_id}/customer-profiles/{customer_profile_id}/loyalty/adjust`

### Billing

Extend sale creation with optional:

- `loyalty_points_to_redeem`

The backend computes:

- maximum allowed redemption
- loyalty discount amount
- earned points on finalized sale

The sale response should include:

- `loyalty_points_redeemed`
- `loyalty_discount_amount`
- `loyalty_points_earned`

### Returns

Approved sale-return flow should trigger loyalty reversal and restore logic automatically.

No separate cashier-side loyalty return API is needed in this slice.

## UI Boundary

### Owner Web

Use the existing customer and commercial surfaces, not a separate loyalty app.

Add:

- tenant loyalty rule editor
- customer loyalty summary
- customer loyalty ledger visibility
- manual point adjustment

The first slice should not add tier visualization, campaign editing, or segmentation tools.

### Store Desktop

Extend the existing billing surface in `apps/store-desktop/src/control-plane/StoreBillingSection.tsx`.

When a customer profile is selected:

- load current loyalty balance
- show configured redemption posture
- show maximum redeemable points for current cart
- let cashier apply allowed points in configured steps
- show the resulting discount before finalizing the sale

The desktop flow should remain fast:

- no separate CRM screen
- no free-form point math in the UI
- no anonymous loyalty behavior

## Error Handling

The backend should reject:

- redemption for anonymous checkout
- redemption above available balance
- redemption below minimum threshold
- redemption not aligned to configured step size
- redemption that would exceed allowed sale discount

Desktop should surface these as ordinary checkout validation errors, not silently retry or downgrade.

Owner-web should reject invalid program rules such as:

- zero or negative step values
- zero or negative step points
- negative earn rate
- invalid minimum relative to step size when business rules require multiples

## Testing Strategy

### Backend Tests

- loyalty program create and update
- disabled program behavior
- customer account read with and without history
- manual adjustment updates balance through append-only ledger entries
- sale creation with `loyalty_points_to_redeem`
  - rejects anonymous checkout
  - rejects over-redemption
  - enforces minimum and step rules
  - computes loyalty discount correctly
  - posts `REDEEMED` and `EARNED` entries correctly
- approved return reverses earned points and restores redeemed points correctly
- loyalty and store credit can coexist on the same sale without breaking totals

### Owner Web Tests

- loyalty program loads and saves
- customer loyalty summary and ledger render correctly
- manual point adjustment works and refreshes balance

### Store Desktop Tests

- selected customer loads loyalty balance
- checkout shows allowed redemption posture
- cashier can apply valid points and see the discount reflected
- invalid redemption is blocked cleanly
- sale request includes `loyalty_points_to_redeem`
- loyalty works alongside store credit and provider-backed payment flows

## Rollout Order

1. add control-plane loyalty models, migration, schemas, services, and routes
2. extend sale creation and return approval with loyalty effects
3. add owner-web loyalty program and customer loyalty management
4. add desktop loyalty balance and redemption flow in checkout
5. run targeted backend, owner-web, and desktop verification
6. update `WORKLOG.md` and advance the ledger

## Success Criteria

This slice is complete when:

- loyalty is first-class and separate from store credit
- points are earned and redeemed only through control-plane authority
- desktop checkout can use loyalty with selected customer profiles
- owner-web can manage the loyalty program and customer point posture
- the implementation creates a clean base for later promotions and vouchers without semantic overlap
