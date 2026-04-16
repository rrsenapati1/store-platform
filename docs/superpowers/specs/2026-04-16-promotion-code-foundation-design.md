# Promotion Code Foundation Design

Date: 2026-04-16  
Owner: Codex  
Status: Approved for implementation

## Goal

Add a first-class `promotion code` foundation on top of the customer-profile, store-credit, and loyalty foundations so `V2-005` can support shared cashier-applied voucher and coupon codes during checkout.

This slice should make promotions operational immediately:

- owners can create and manage promotion campaigns
- owners can create shared codes under those campaigns
- Store Desktop can apply one cashier-entered code during checkout
- the control plane can validate the code and compute authoritative discount amount
- finalized sales can snapshot promotion usage for audit and reporting

## Scope

This slice establishes `shared promotion codes` as a control-plane-owned discount instrument.

Included:

- control-plane promotion campaign and promotion code authority
- shared campaign codes such as `DIWALI100` or `WELCOME5`
- one promotion code per sale in the first slice
- flat-amount and percentage discounts
- minimum order amount support
- optional maximum discount amount support for percentage campaigns
- optional campaign and per-code redemption limits
- owner-web campaign and code management
- Store Desktop manual promotion-code entry during checkout
- promotion validation for both direct sale creation and checkout payment session creation
- sale snapshot fields for campaign, code, and discount amount

Not included:

- customer-specific assigned vouchers
- automatic cart rules without a code
- stacked or combinable promotions
- mobile or tablet promotion redemption
- loyalty-generated coupons
- expiring promotional credit balances
- “best promo” auto-selection
- promotion browsing or search on desktop

## Recommended Approach

Use a dedicated control-plane `promotion campaign + promotion code` model and treat promotion redemption as backend-validated discount authority.

Why:

- discount validity needs one source of truth
- checkout and hosted payment session creation both need the same validation and math
- owner-web can manage campaign lifecycle without inventing a second promotions product
- later customer-assigned vouchers and automatic promotion rules can extend the same foundation cleanly

## Why Promotions Must Stay Separate

This slice should keep promotion codes separate from both store credit and loyalty.

That means:

- promotion codes are merchant-funded discounts
- loyalty points remain a rewards ledger
- store credit remains a money-like customer liability

If these are blurred together now, later commercial features get harder:

- accounting mixes liability with discounting
- operators lose clarity about what reduces payable amount versus what spends customer balance
- future customer-assigned vouchers and automatic campaigns inherit the wrong semantics

## Architecture

### Authority Model

Promotion validation and discount computation must remain control-plane authority only.

Rules:

- desktop must not compute the final discount on its own
- invalid or disabled codes must fail visibly
- checkout payment session creation and direct sale creation must use the same validation path
- historical sales must keep their promotion snapshot even if a campaign changes later

### Core Model

Add two related models:

1. `promotion_campaigns`
2. `promotion_codes`

Campaigns define discount behavior and redemption constraints.  
Codes are shared redeemable entry points under those campaigns.

Sales and checkout payment sessions should snapshot resolved promotion usage, but not become the source of truth for promotion rules.

## Data Model

### Promotion Campaigns

Recommended fields:

- `id`
- `tenant_id`
- `name`
- `status`
  - `ACTIVE`
  - `DISABLED`
  - `ARCHIVED`
- `discount_type`
  - `FLAT_AMOUNT`
  - `PERCENTAGE`
- `discount_value`
- `minimum_order_amount | null`
- `maximum_discount_amount | null`
- `redemption_limit_total | null`
- `redemption_count`
- `created_at`
- `updated_at`

This first slice should keep campaign rules intentionally small and explicit.

### Promotion Codes

Recommended fields:

- `id`
- `tenant_id`
- `campaign_id`
- `code`
- `status`
  - `ACTIVE`
  - `DISABLED`
- `redemption_limit_per_code | null`
- `redemption_count`
- `created_at`
- `updated_at`

Codes are shared. They are not assigned to individual customers in this slice.

### Sale Snapshot

Finalized sales should record:

- `promotion_campaign_id | null`
- `promotion_code_id | null`
- `promotion_code | null`
- `promotion_discount_amount`

This preserves invoice truth even after campaigns or codes are edited, disabled, or archived.

## Promotion Rules

### Shared Code Model

The first slice supports only shared campaign codes.

That means:

- any eligible checkout can use the code
- per-customer ownership or assignment is deferred
- customer profile may still matter indirectly through loyalty and store-credit posture, but not for promotion-code ownership

### Validation

For a code to apply successfully:

- the code must exist
- the code must be active
- the campaign must be active
- the cart must meet `minimum_order_amount` if configured
- campaign redemption cap must not be exceeded
- per-code redemption cap must not be exceeded

### Discount Semantics

Promotion codes are discount instruments, not payment methods.

That means:

- a promotion lowers the sale total
- it does not behave like tender
- it should coexist with loyalty redemption and store-credit redemption later in the same checkout posture

### One-Code Rule

The first slice supports one applied code maximum per sale.

This keeps:

- cashier behavior simple
- backend validation deterministic
- snapshot and payment-session behavior easy to reason about

### Calculation Order

Recommended checkout calculation order:

1. base cart subtotal and tax posture
2. promotion discount
3. loyalty redemption discount
4. store-credit redemption
5. remaining payment-method settlement

Why:

- promotions are merchant-funded discount logic
- loyalty is a separate rewards discount layer
- store credit is money-like balance and should apply after discounts

## API Boundary

### Campaign Routes

Add a tenant promotions surface:

- `GET /v1/tenants/{tenant_id}/promotion-campaigns`
- `POST /v1/tenants/{tenant_id}/promotion-campaigns`
- `GET /v1/tenants/{tenant_id}/promotion-campaigns/{campaign_id}`
- `PATCH /v1/tenants/{tenant_id}/promotion-campaigns/{campaign_id}`
- `POST /v1/tenants/{tenant_id}/promotion-campaigns/{campaign_id}/disable`
- `POST /v1/tenants/{tenant_id}/promotion-campaigns/{campaign_id}/reactivate`

### Code Routes

Add shared-code management under campaigns:

- `POST /v1/tenants/{tenant_id}/promotion-campaigns/{campaign_id}/codes`
- optionally `PATCH /v1/tenants/{tenant_id}/promotion-campaigns/{campaign_id}/codes/{code_id}` if enable/disable is modeled per code update

The route shape may be simplified if the existing control-plane patterns favor direct nested create plus patch/update.

### Billing Route Changes

Extend sale creation with optional:

- `promotion_code`

Backend responsibilities:

- resolve the submitted code
- validate campaign and code posture
- compute `promotion_discount_amount`
- apply that discount before loyalty and store-credit logic
- persist sale snapshot fields

### Checkout Payment Session Changes

Extend checkout payment session creation with optional:

- `promotion_code`

Backend responsibilities:

- run the same validation and discount logic used for direct sale creation
- persist promotion posture on the payment session so customer-visible totals stay aligned
- ensure finalization cannot drift from the validated session posture

## UI Boundary

### Owner Web

Use the existing commercial and customer administration area, not a separate promotions app.

Add:

- campaign list
- create and edit campaign
- shared code creation under a campaign
- enable and disable campaign posture
- code-level redemption visibility

The first slice should not add:

- customer-specific assignment
- campaign segmentation UI
- automatic discount authoring

### Store Desktop

Extend `apps/store-desktop/src/control-plane/StoreBillingSection.tsx`.

Add:

- manual `Promotion code` entry field
- visible applied-code posture
- visible promotion discount amount
- updated payable posture alongside loyalty and store credit

Desktop behavior should stay bounded:

- cashier types one code
- backend validates it
- UI shows discount or error
- no local “best code” logic
- no promo browsing workflow

## Data Flow

### Owner Creates Campaign

1. Owner creates a promotion campaign.
2. Owner configures discount type and limits.
3. Owner creates one or more shared codes under that campaign.
4. Owner-web refreshes campaign and code list with redemption posture.

### Desktop Checkout With Promotion Code

1. Cashier builds the cart.
2. Cashier enters one promotion code.
3. Desktop includes `promotion_code` in checkout create or payment-session create request.
4. Backend validates the code and computes discount.
5. Desktop shows the applied discount and updated payable posture.
6. Sale finalization snapshots promotion usage.

### Invalid Code

1. Cashier enters a code.
2. Backend rejects it because the code or campaign is invalid, disabled, below minimum order, or at redemption cap.
3. Desktop surfaces the error clearly.
4. Checkout remains editable; no silent fallback occurs.

## Validation And Error Handling

Backend validation should reject:

- unknown code
- disabled code
- disabled or archived campaign
- order below minimum threshold
- campaign redemption cap exceeded
- code redemption cap exceeded
- percentage discount without a valid percentage rule
- discount amount that would exceed the pre-payment sale total

Desktop behavior:

- show a normal checkout validation error
- keep the code field editable
- do not keep a stale applied-discount posture after rejection

Owner-web behavior:

- reject invalid campaign values such as negative discounts
- reject invalid caps or malformed code values
- surface duplicate code conflicts clearly

## Testing Strategy

### Backend Tests

- campaign create, update, disable, and reactivate
- shared code creation and validation
- flat discount application
- percentage discount with max cap
- minimum-order rejection
- total and per-code redemption-limit rejection
- sale creation with valid `promotion_code`
- checkout payment session with valid `promotion_code`
- invalid or disabled code rejection
- promotion, loyalty, and store-credit ordering correctness

### Owner Web Tests

- campaign list loads
- create and edit campaign works
- shared code creation works
- disable and reactivate posture renders and updates
- redemption counts render correctly

### Store Desktop Tests

- cashier can enter a promotion code
- valid code discount shows in checkout posture
- invalid code surfaces a clear error
- sale payload includes `promotion_code`
- Cashfree session payload includes `promotion_code`
- promotion coexists correctly with loyalty and store credit

## Rollout Order

1. add control-plane promotion models, migration, schemas, services, and routes
2. integrate promotion-code validation into billing and checkout payment session creation
3. add owner-web campaign and code management
4. add desktop promotion-code entry and discount visibility
5. run targeted backend, owner-web, and desktop verification
6. update `WORKLOG.md` and advance the ledger

## Success Criteria

This slice is complete when:

- shared promotion codes are first-class control-plane authority
- owner-web can manage campaigns and shared codes
- Store Desktop can apply one validated promotion code during checkout
- promotion discount snapshots are preserved on finalized sales
- promotion logic remains distinct from loyalty and store credit
- the implementation creates a clean base for later customer-assigned vouchers and automatic cart rules
