# Customer Profile Foundation Design

Date: 2026-04-16  
Owner: Codex  
Status: Approved for implementation

## Goal

Add a first-class tenant-scoped customer profile model to the control plane and use it in checkout, customer history, and customer management flows so `V2-005` starts from explicit customer identity instead of inferred sales-only reporting records.

## Scope

This slice establishes the first real customer write model.

Included:

- control-plane `customer_profiles` persistence and routes
- optional `customer_profile_id` linkage on checkout payment sessions and sales
- snapshot copy from profile into sale/customer-facing billing records
- owner-web customer profile list, edit, archive, and reactivate flow
- store-desktop customer search, select, clear, and inline create inside billing
- compatibility updates so customer directory and history prefer profile-backed identity for newly linked sales

Not included:

- loyalty points
- promotions or discount rules
- store credit or gift cards
- segmentation or campaign tooling
- multi-price tiers
- mandatory customer linkage for every sale

## Recommended Approach

Use an explicit control-plane `customer_profiles` model and keep sale records snapshot-based.

Why:

- later `V2-005` features such as loyalty and store credit need durable customer ownership
- sales invoices and payment records still need historical snapshots that do not drift when a customer profile is edited later
- anonymous or walk-in billing must remain valid, so profile linkage must stay optional

## Architecture

### Control-Plane Model

Add `customer_profiles` with tenant-scoped identity and lightweight CRM fields:

- `id`
- `tenant_id`
- `full_name`
- `phone`
- `email`
- `gstin`
- `default_note`
- `tags`
- `status`
  - `ACTIVE`
  - `ARCHIVED`

Recommended rules:

- `gstin` remains optional
- `phone` and `email` remain optional
- archived profiles stay readable in history but are excluded from default active search unless explicitly requested
- `gstin` should be unique per tenant when present

### Billing Linkage

Extend billing and checkout payment models with nullable `customer_profile_id`.

Authority rules:

- `customer_profile_id` is the live identity reference
- `customer_name` and `customer_gstin` on sale/payment records remain immutable snapshots
- sale creation and provider-backed payment session creation accept either:
  - selected `customer_profile_id`, or
  - anonymous/manual customer fields with no profile

When a profile is selected:

- backend copies `full_name` and `gstin` from the profile into the billing snapshot by default
- desktop may still allow explicit manual override of snapshot fields before posting the sale if needed

### Reporting Compatibility

Existing customer directory and history are currently derived from sales.

This slice should move them to a hybrid model:

- if a sale has `customer_profile_id`, customer reporting uses that profile identity
- if a historical sale has no linked profile, reporting falls back to existing derived name or GSTIN matching behavior

That preserves continuity for prior data while making all new activity profile-backed when linked.

## API Boundary

### Customer Profile Routes

Add customer-profile write routes alongside the current customer reporting reads:

- `GET /v1/tenants/{tenant_id}/customer-profiles`
- `POST /v1/tenants/{tenant_id}/customer-profiles`
- `GET /v1/tenants/{tenant_id}/customer-profiles/{customer_profile_id}`
- `PATCH /v1/tenants/{tenant_id}/customer-profiles/{customer_profile_id}`
- `POST /v1/tenants/{tenant_id}/customer-profiles/{customer_profile_id}/archive`
- `POST /v1/tenants/{tenant_id}/customer-profiles/{customer_profile_id}/reactivate`

Search should support:

- name
- phone
- email
- GSTIN
- optional status filter

### Billing Route Changes

Extend billing and checkout-payment inputs with optional `customer_profile_id`.

The backend remains responsible for:

- resolving the profile
- copying profile fields into the invoice/payment snapshot when linked
- allowing anonymous/manual sales when no profile is provided

### Reporting Route Changes

Current reporting routes stay in place:

- `GET /v1/tenants/{tenant_id}/customers`
- `GET /v1/tenants/{tenant_id}/customers/{customer_id}/history`
- `GET /v1/tenants/{tenant_id}/branches/{branch_id}/customer-report`

Their internal read model changes:

- prefer profile-backed identity for linked sales
- preserve fallback grouping for legacy unlinked records

No new reporting route family is needed in this slice.

## UI Boundary

### Store Desktop

Keep customer selection inside `apps/store-desktop/src/control-plane/StoreBillingSection.tsx`.

Add:

- customer search field
- matching profile list
- quick select action
- clear selection action
- inline customer create action for no-match cases
- linked-customer posture near billing fields

Desktop flow:

1. cashier searches for a customer
2. cashier selects an existing profile or creates a new one inline
3. desktop hydrates checkout fields from the profile
4. cashier may continue with the selected profile or clear back to anonymous/manual mode
5. checkout posts optional `customer_profile_id` plus frozen snapshot fields

The billing surface remains fast:

- no separate customer-management screen on desktop
- no mandatory profile selection before billing

### Owner Web

Extend the existing customer insights area into profile-aware management instead of introducing a second customer surface.

Add:

- profile list/search
- profile detail read
- basic edit
- archive/reactivate controls
- existing history visibility for the selected profile

This keeps the owner surface aligned with the already-landed customer-reporting area while upgrading it from read-only reporting into lightweight customer administration.

## Data Flow

### Desktop Checkout

1. Desktop loads matching profiles from customer-profile search.
2. Cashier selects a profile or creates one inline.
3. Desktop stores:
   - selected `customer_profile_id`
   - hydrated `customerName`
   - hydrated `customerGstin`
4. Cashier creates a manual or provider-backed checkout flow.
5. Backend resolves the profile, validates tenant scope, and writes:
   - `customer_profile_id`
   - immutable `customer_name` snapshot
   - immutable `customer_gstin` snapshot
6. Later customer reporting and history link the sale to the selected profile.

### Owner Profile Management

1. Owner searches profiles.
2. Owner selects one profile.
3. Owner edits fields or archives/reactivates the profile.
4. History continues to load through the existing history read route, now profile-aware for linked sales.

## Validation And Error Handling

Backend validation:

- tenant-scoped access only
- reject unknown or archived profiles for new checkout linkage
- enforce unique tenant `gstin` when present
- normalize phone/email/GSTIN consistently

Desktop and owner-web validation:

- clear empty inline create payloads before submit
- require `full_name` for profile creation
- surface duplicate GSTIN or validation failures explicitly
- do not silently fall back from linked to anonymous checkout if profile resolution fails

## Testing

### Backend

- create, update, archive, and reactivate customer profiles
- search by name, phone, email, and GSTIN
- duplicate GSTIN rejection when GSTIN is present
- sale creation with linked `customer_profile_id`
- anonymous sale creation without profile
- customer directory/history prefer profile-backed identity for linked sales while preserving legacy compatibility

### Store Desktop

- customer profile search/select flow inside billing
- inline create and immediate selection
- clear selection back to anonymous/manual mode
- checkout payload includes `customer_profile_id` when linked
- checkout payload omits `customer_profile_id` when cleared

### Owner Web

- profile list/search
- profile edit
- archive/reactivate
- history render for selected profile

## Exit Criteria

This slice is done when:

- control-plane customer profiles exist as a first-class write model
- store-desktop can select or create a customer profile during checkout
- owner-web can manage customer profiles directly
- sales and payment sessions can optionally link a profile while preserving immutable customer snapshots
- customer reporting/history use profile-backed identity for new linked activity without losing legacy historical visibility
