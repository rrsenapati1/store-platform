# Customer-Assigned Voucher Foundation Design

## Goal

Extend the new commercial foundation with `customer-assigned vouchers` so `V2-005` can support single-use fixed-value vouchers tied to one `customer_profile_id`, managed by owners and redeemable during Store Desktop checkout.

This slice gives the platform a first-class personalized voucher lane without collapsing vouchers into shared codes, loyalty points, or store credit.

## Scope

Included:

- customer-assigned voucher campaigns under the existing promotion foundation
- explicit voucher assignment records tied to `customer_profile_id`
- owner-web voucher campaign management and customer-level voucher issuance/cancel
- Store Desktop voucher selection during checkout for a selected customer profile
- backend pricing preview, sale creation, and provider-backed checkout-session support for one voucher
- voucher redemption audit trail and sale snapshot fields

Not included:

- percentage vouchers
- multi-use vouchers
- anonymous voucher redemption
- voucher expiry
- customer self-service voucher wallet
- loyalty-generated vouchers
- stacking multiple vouchers or combining a voucher with a cashier-entered shared code

## Recommended Approach

Use one unified promotions system with a new `ASSIGNED_VOUCHER` trigger mode and a dedicated voucher-assignment record.

Why this is the right boundary:

- the repo already has promotion campaigns, shared codes, and automatic discount rules
- vouchers are still merchant-funded discounts, not money-like liabilities
- customer linkage belongs in an explicit assignment record, not in the generic shared-code table
- billing and pricing preview can stay centralized in the existing commercial engine

## Commercial Rules

### Manual promotion instrument rule

The first voucher slice should allow:

- at most one `shared promotion code`, or
- at most one `customer-assigned voucher`

per sale.

They should be mutually exclusive in the first slice.

Automatic discounts may still coexist with one manual promotion instrument.

### Discount ordering

The pricing order should become:

1. base cart pricing
2. automatic discount
3. one manual promotion instrument
   - shared code or customer-assigned voucher
4. loyalty redemption
5. store credit
6. payment settlement

This preserves the current separation:

- automatic and voucher/code discounts are merchant-funded invoice discounts
- loyalty is a reward instrument
- store credit is a payment source

## Data Model

### Promotion campaign

Extend `promotion_campaigns` with support for:

- `trigger_mode = ASSIGNED_VOUCHER`

Voucher campaigns in this first slice must obey:

- `scope = CART`
- `discount_type = FLAT_AMOUNT`

They are templates for issuance, not directly redeemable by manual code entry.

### Customer voucher assignment

Add a new authoritative table, for example `customer_voucher_assignments`, with fields like:

- `id`
- `tenant_id`
- `campaign_id`
- `customer_profile_id`
- `voucher_code`
- `voucher_name_snapshot`
- `voucher_amount`
- `status`
  - `ACTIVE`
  - `REDEEMED`
  - `CANCELED`
- `issued_note`
- `issued_by_actor_id | null`
- `redeemed_sale_id | null`
- `redeemed_at | null`
- timestamps

Important modeling decisions:

- the assignment stores `voucher_name_snapshot` and `voucher_amount`
- issued vouchers must remain redeemable even if the source campaign is later disabled
- campaign disable blocks new issuance, not redemption of already issued active vouchers

### Sale snapshot

Extend finalized sale records with voucher snapshot fields:

- `customer_voucher_id`
- `customer_voucher_code`
- `customer_voucher_name`
- `customer_voucher_discount_total`

Extend sale lines with:

- `customer_voucher_discount_amount`

This keeps invoice truth and line-level tax allocation auditable.

### Checkout payment session snapshot

Extend checkout payment sessions with:

- `customer_voucher_id`
- `customer_voucher_code`
- `customer_voucher_name`
- `customer_voucher_discount_total`

Voucher redemption should not happen at session creation time. The session only snapshots intended redemption. Actual redemption occurs when the sale is finalized.

## API Surface

### Promotion campaign management

Reuse the existing campaign surface with the new trigger mode:

- `GET /v1/tenants/{tenant_id}/promotion-campaigns`
- `POST /v1/tenants/{tenant_id}/promotion-campaigns`
- `PATCH /v1/tenants/{tenant_id}/promotion-campaigns/{campaign_id}`

Voucher campaigns should reject:

- shared code creation
- automatic item/category targeting
- percentage discount type

### Customer voucher assignment

Add customer-scoped voucher routes:

- `GET /v1/tenants/{tenant_id}/customer-profiles/{customer_profile_id}/vouchers`
- `POST /v1/tenants/{tenant_id}/customer-profiles/{customer_profile_id}/vouchers`
- `POST /v1/tenants/{tenant_id}/customer-profiles/{customer_profile_id}/vouchers/{voucher_id}/cancel`

Issue payload:

- `campaign_id`
- `note?`

### Checkout and pricing

Extend:

- checkout pricing preview
- direct sale creation
- checkout payment session creation

with optional:

- `customer_voucher_id`

Validation rules:

- `customer_profile_id` is required when `customer_voucher_id` is set
- voucher must belong to the same `customer_profile_id`
- voucher must be `ACTIVE`
- shared promotion code and customer voucher cannot both be set
- voucher discount cannot exceed the post-automatic-discount subtotal

## Backend Behavior

### Pricing preview

The pricing preview engine should:

- resolve automatic discounts first
- resolve exactly one manual promotion instrument
- when `customer_voucher_id` is supplied:
  - validate assignment ownership and status
  - use assignment snapshot amount
  - allocate voucher discount across lines proportionally

Preview response should add:

- `customer_voucher`
  - `id`
  - `voucher_code`
  - `voucher_name`
  - `voucher_amount`
- `customer_voucher_discount_total`

### Direct sale creation

On successful sale creation:

- snapshot voucher fields on the sale
- snapshot line-level voucher discount amounts
- mark the voucher assignment `REDEEMED`
- link `redeemed_sale_id`

### Provider-backed checkout

On checkout payment session creation:

- snapshot voucher intent on the payment session
- do not redeem yet

On session finalization:

- create the sale using the snapped voucher intent
- redeem the voucher exactly once

Canceled, expired, or failed sessions must not redeem vouchers.

## Owner Web

### Campaign management

The existing `OwnerPromotionCampaignSection` should support voucher-template campaigns by allowing:

- `ASSIGNED_VOUCHER`
- `CART`
- `FLAT_AMOUNT`

It should make it clear that voucher campaigns do not use shared codes.

### Customer insights

The existing `OwnerCustomerInsightsSection` should gain:

- selected customer voucher list
- voucher issue action
- voucher cancel action

This is the right surface because voucher ownership is customer-specific, not global.

## Store Desktop

Store Desktop checkout should gain customer-voucher posture only when a customer profile is selected.

Expected behavior:

- load active vouchers for the selected customer
- show them in billing
- cashier can apply one active voucher
- applying a voucher clears any typed shared promotion code
- typing a shared promotion code clears any selected voucher
- checkout pricing preview and final sale reflect the selected voucher

The checkout summary should show:

- automatic discount
- shared code discount
- customer voucher discount
- loyalty discount
- store credit used
- remaining payable

Only one of `shared code discount` or `customer voucher discount` should be non-zero in this slice.

## Error Handling

Reject clearly when:

- voucher belongs to another customer
- voucher is already redeemed
- voucher is canceled
- voucher is used without a selected customer profile
- both promotion code and customer voucher are set

Provider-backed payment recovery must preserve the invariant:

- voucher is not consumed until sale finalization

## Testing

Backend:

- voucher campaign create/update validation
- customer voucher issue/cancel
- pricing preview with voucher
- sale creation with voucher redemption
- checkout payment session with voucher snapshot but no redemption until finalization
- rejection for invalid ownership/status and code-plus-voucher conflicts

Owner web:

- voucher campaign create/edit posture
- selected customer voucher issue and cancel

Store Desktop:

- selected customer loads vouchers
- voucher selection updates pricing preview
- voucher and shared code are mutually exclusive
- checkout payload carries `customer_voucher_id`
- provider-backed session payload carries `customer_voucher_id`

## Success Criteria

This slice is done when:

- owner-web can create voucher-template campaigns
- owner-web can assign and cancel active vouchers for a selected customer
- Store Desktop can redeem one active customer voucher during checkout
- billing and provider-backed checkout use centralized pricing authority
- voucher redemption is auditable and replay-safe
