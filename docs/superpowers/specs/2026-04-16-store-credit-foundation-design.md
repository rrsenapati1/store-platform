# Store Credit Foundation Design

Date: 2026-04-16  
Owner: Codex  
Status: Approved for implementation

## Goal

Add a first-class `store credit` liability model on top of the new customer-profile foundation so `V2-005` can support real issued customer balance, return-to-credit refunds, and partial checkout redemption through control-plane-owned authority.

This slice should make store credit operational immediately:

- owners can issue and adjust customer credit
- approved returns can refund into store credit
- Store Desktop can redeem store credit during checkout

## Scope

This slice establishes `store credit` as a customer-linked financial liability.

Included:

- control-plane customer store-credit account, lot, and ledger authority
- tenant-wide customer credit balance tied to `customer_profile_id`
- manual owner-issued credit and manual owner adjustment
- non-expiring store credit only
- approved sale-return refund method `STORE_CREDIT`
- partial store-credit redemption during Store Desktop checkout
- sale snapshot updates that record redeemed store-credit amount
- owner-web customer credit management inside the existing customer surface
- Store Desktop credit visibility and redemption inside the existing checkout and return surfaces

Not included:

- expiring credit
- promotional vouchers or promo credit
- loyalty points
- gift cards or claim codes
- customer self-service wallet flows
- cross-tenant portability
- mobile or tablet credit redemption
- campaign, discount, or promotion logic

## Recommended Approach

Use a dedicated control-plane `store credit ledger` with issuance lots and redemption allocations.

Why:

- store credit is a real liability, not a UI-only balance
- owner-issued credit, return-issued credit, and redeemed credit need clear source tracking
- later promotional credit can remain separate instead of being confused with customer money-like balance
- partial checkout redemption needs deterministic allocation and auditable replay-safe writes

## Why Credit Must Stay Separate From Promotions

This slice should treat store credit as customer money-like liability, not promotional value.

That means:

- store credit does not expire
- return-issued credit is not mixed with campaign-funded incentives
- later `promotional credit / voucher` can be introduced as a different instrument with its own expiry and funding rules

Mixing the two now would make later `V2-005` commercial features harder:

- operators would confuse refunds and promotions
- accounting would blur customer liability and marketing spend
- customers could see expiring refund balance, which is the wrong product behavior

## Architecture

### Authority Model

Store credit must remain control-plane authority only.

Rules:

- no runtime-local credit balance is authoritative
- no checkout redemption without control-plane validation
- no destructive edits to historical credit activity
- all credit movement is append-only through ledger entries

### Core Model

Add three related models:

1. `customer_credit_accounts`
2. `customer_credit_lots`
3. `customer_credit_ledger_entries`

The account is a summarized read model per tenant and customer profile.  
The lot records issuance buckets and remaining redeemable value.  
The ledger is the append-only source of truth for movement and audit.

## Data Model

### Customer Credit Account

One row per `tenant_id + customer_profile_id`.

Recommended fields:

- `id`
- `tenant_id`
- `customer_profile_id`
- `available_balance`
- `issued_total`
- `redeemed_total`
- `adjusted_total`
- `reversed_total`
- `created_at`
- `updated_at`

This is a convenience summary only. The ledger remains authoritative.

### Customer Credit Lots

Lots track issuance provenance and remaining redeemable balance.

Recommended fields:

- `id`
- `tenant_id`
- `customer_profile_id`
- `source_type`
  - `MANUAL_ISSUE`
  - `RETURN_REFUND`
  - `MANUAL_ADJUSTMENT`
- `source_reference_id`
- `original_amount`
- `remaining_amount`
- `status`
  - `ACTIVE`
  - `DEPLETED`
  - `REVERSED`
- `issued_at`

Even though store credit is non-expiring, lots are still useful because they preserve:

- source tracking
- audit clarity
- deterministic redemption allocation

### Customer Credit Ledger Entries

Ledger entries are append-only.

Recommended fields:

- `id`
- `tenant_id`
- `customer_profile_id`
- `branch_id | null`
- `entry_type`
  - `ISSUED`
  - `REDEEMED`
  - `ADJUSTED`
  - `REVERSED`
- `amount`
- `running_balance`
- `source_type`
- `source_reference_id`
- `note | null`
- `actor_user_id | null`
- `created_at`

## Liability Rules

### Balance Scope

Store credit is `tenant-wide` per customer profile.

That means:

- a credit issued in one branch is redeemable in another branch of the same tenant
- individual ledger entries still record the issuing or redeeming branch for audit

### Expiry

This slice does not support expiry.

Store credit remains redeemable until:

- fully consumed, or
- manually reversed or adjusted under owner authority

### Issuance Sources

Supported sources in this slice:

- manual issue from owner-web
- manual adjustment from owner-web
- approved sale return with refund method `STORE_CREDIT`

### Redemption Allocation

Checkout redemption consumes available lots in deterministic order:

1. oldest `issued_at`
2. stable tie-break by lot id

This avoids ambiguous balance reduction and keeps replay-safe behavior deterministic.

## Checkout Rules

### Eligibility

Store credit may only be used when:

- the sale has a selected `customer_profile_id`
- the customer has sufficient available balance
- requested redemption amount is greater than zero
- requested redemption amount is less than or equal to sale total

Anonymous checkout cannot use store credit.

### Partial Redemption

Partial redemption is supported.

That means:

- cashier can apply part of the sale total from store credit
- the remaining amount is paid through another payment method
- the sale still posts as one authoritative sale with split payment summary

### Sale Snapshot

Sale records should continue to snapshot customer and payment posture.

This slice should extend sale serialization so the sale can show:

- redeemed store-credit amount
- remaining externally paid amount
- payment summary that reflects split settlement

The credit ledger still remains the liability authority.

## Return-To-Credit Rules

Approved sale returns can refund into store credit.

Rules:

- cashier can choose `STORE_CREDIT` as refund method when creating a return
- existing owner approval remains the authority gate
- approval issues a new credit lot linked to the `sale_return_id`
- cash or UPI payout is not performed for that approved return

This makes store credit immediately useful for common retail return flows.

## API Boundary

### Customer Credit Routes

Add dedicated store-credit routes under the customer-profile authority surface:

- `GET /v1/tenants/{tenant_id}/customer-profiles/{customer_profile_id}/store-credit`
- `POST /v1/tenants/{tenant_id}/customer-profiles/{customer_profile_id}/store-credit/issue`
- `POST /v1/tenants/{tenant_id}/customer-profiles/{customer_profile_id}/store-credit/adjust`

The read route should return:

- account summary
- active lots
- recent ledger entries

### Billing Route Changes

Extend sale creation with optional store-credit redemption input, such as:

- `store_credit_amount`

Backend responsibilities:

- require selected `customer_profile_id`
- validate available balance
- allocate redemption across lots
- write redemption ledger entries
- persist sale snapshot with redeemed amount

### Return Route Changes

Extend sale-return creation and approval flow so `refund_method = STORE_CREDIT` is valid.

Approval responsibilities:

- issue new customer credit lot
- write issuance ledger entry
- keep the existing approval audit trail

## UI Boundary

### Owner Web

Extend `apps/owner-web/src/control-plane/OwnerCustomerInsightsSection.tsx`.

Add:

- available balance summary
- recent ledger entries
- active issuance lots
- manual issue form
- manual adjustment form

This keeps customer credit attached to customer management instead of inventing a second finance tool for the first slice.

### Store Desktop Checkout

Extend `apps/store-desktop/src/control-plane/StoreBillingSection.tsx`.

When a customer profile is selected:

- load store-credit summary
- show available balance
- allow cashier to enter store-credit redemption amount
- validate partial redemption posture in the UI
- keep remaining amount payable through the selected payment method

No selected customer profile means:

- no store-credit redemption surface

### Store Desktop Returns

Extend the existing sale-return flow so refund method can be:

- `Cash`
- `UPI`
- `STORE_CREDIT`

This should remain inside the existing desktop return surface, not a separate store-credit return flow.

## Data Flow

### Manual Issue

1. Owner selects a customer profile.
2. Owner issues credit with amount and note.
3. Backend creates or updates the credit account.
4. Backend creates an `ACTIVE` lot.
5. Backend writes an `ISSUED` ledger entry.
6. Owner-web refreshes summary, lots, and ledger.

### Checkout Redemption

1. Cashier selects a customer profile in desktop billing.
2. Desktop loads credit summary.
3. Cashier enters redemption amount.
4. Sale create request includes `customer_profile_id` and `store_credit_amount`.
5. Backend validates balance and allocates lots.
6. Backend writes sale, inventory ledger, and credit redemption ledger entries in one authoritative transaction.
7. Desktop refreshes sale history, inventory, and customer credit posture.

### Return To Credit

1. Cashier creates sale return with `refund_method = STORE_CREDIT`.
2. Owner approves the return.
3. Backend creates a new credit lot sourced from that return.
4. Backend writes an `ISSUED` ledger entry.
5. Customer credit becomes immediately redeemable across the tenant.

## Validation And Error Handling

Backend validation:

- reject store-credit redemption without `customer_profile_id`
- reject redemption amount greater than available balance
- reject redemption amount greater than sale total
- reject issuance or adjustment for archived customer profiles
- reject negative issue amounts
- require explicit signed adjustment semantics for balance changes

UI handling:

- desktop should disable store-credit entry for anonymous checkout
- desktop should show clear insufficient-balance errors
- owner-web should show adjustment and issuance failures explicitly
- no silent fallback from credit redemption to manual payment

## Testing

### Backend

- manual issue creates account, lot, and ledger entry
- manual adjustment updates balance with ledger visibility
- sale create with partial store-credit redemption reduces balance correctly
- sale create rejects redemption beyond available balance
- sale create rejects redemption without customer profile
- approved return with `STORE_CREDIT` issues new balance instead of external refund
- tenant-wide redemption works across branches for the same customer profile
- ledger remains append-only and auditable

### Owner Web

- customer credit summary loads for selected profile
- manual issue works
- manual adjustment works
- ledger and lot visibility update after mutations

### Store Desktop

- selected customer profile loads available credit
- cashier can apply partial credit during checkout
- checkout sends redemption amount with profile linkage
- anonymous checkout cannot apply credit
- return flow can choose `STORE_CREDIT`

## Exit Criteria

This slice is done when:

- customer store credit exists as a first-class control-plane liability model
- owner-web can issue and adjust customer credit
- approved returns can refund to store credit
- Store Desktop can redeem store credit partially during checkout
- store credit remains non-expiring and separate from later promotional credit or voucher work
