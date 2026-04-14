# SaaS Commerce And Tenant Lifecycle Design

## Context

`CP-023` is the first public-release SaaS commerce slice for Store. The control plane already owns:

- tenant onboarding,
- owner-web auth,
- packaged desktop auth and activation,
- packaged runtime continuity,
- branch-hub offline runtime continuity,
- Windows packaging and update channels.

What it does not own yet is the commercial lifecycle required for a public multi-tenant launch:

- billing plans,
- recurring subscription state,
- free-trial posture,
- entitlement enforcement,
- tenant suspension and reactivation under canonical control-plane authority.

The legacy side has a notion of suspended tenants, but the new Store control plane does not yet model subscription-backed lifecycle state. That gap is unacceptable for public release because owner-web and store-desktop can still act as though every tenant is commercially active.

## Chosen Approach

Use one tenant-level subscription contract with:

1. platform-admin-managed billing plans,
2. a free trial before paid billing begins,
3. Cashfree and Razorpay recurring subscription providers behind a common adapter,
4. a canonical tenant entitlement record derived from subscription state,
5. a grace window before hard suspension,
6. consistent entitlement enforcement across owner-web and store-desktop.

This keeps payment-provider detail at the control-plane boundary and prevents owner-web, packaged runtime auth, and offline continuity from inventing separate commercial rules.

## Scope

Included in `CP-023`:

- billing plan catalog for platform admins,
- tenant subscription records with provider linkage,
- canonical tenant entitlement records,
- free-trial issuance on onboarding,
- recurring subscription bootstrap for Cashfree and Razorpay,
- webhook ingestion and canonical subscription-state refresh,
- platform-admin tenant lifecycle controls and visibility,
- owner-facing billing and renewal posture,
- entitlement enforcement across owner-web, device activation, and packaged runtime unlock,
- suspension and reactivation flows.

Out of scope for this slice:

- coupons, discounts, and promo campaigns,
- branch-by-branch billing,
- device-by-device paid add-ons,
- customer invoicing for Store SaaS charges,
- email dunning automation,
- revenue recognition or finance accounting exports,
- payment settlement dashboards beyond bounded operator visibility.

## Commercial Model

### 1. Tenant-Level Commercial Contract

Each Store tenant has one commercial subscription. Plans do not attach independently to branches or devices. Instead, the active plan defines tenant-wide limits and flags such as:

- `branch_limit`
- `device_limit`
- `offline_runtime_hours`
- `grace_window_days`
- feature flags

This avoids ambiguous entitlement combinations across owner-web, packaged desktop activation, and branch-hub continuity.

### 2. Trial And Paid Lifecycle

New tenants start in a fixed free-trial state. Trial posture is part of the canonical entitlement model, not a frontend-only banner.

Lifecycle states:

- `TRIALING`
- `ACTIVE`
- `GRACE`
- `SUSPENDED`
- `CANCELED`

Rules:

- onboarding creates a tenant with a trial entitlement,
- owner sets up a recurring mandate or subscription through Cashfree or Razorpay before trial expiry,
- successful billing moves or keeps the tenant in `ACTIVE`,
- failed renewal moves the tenant into `GRACE`,
- grace expiry moves the tenant to `SUSPENDED`,
- successful recovery reactivates the tenant to `ACTIVE`.

### 3. Provider Boundary

Store should expose one provider abstraction with two initial implementations:

- `CashfreeSubscriptionProvider`
- `RazorpaySubscriptionProvider`

Provider adapters handle:

- customer or subscriber creation,
- recurring mandate or subscription bootstrap,
- provider reference capture,
- webhook verification,
- provider-event normalization.

The rest of the control plane must consume only canonical subscription and entitlement state, not provider-specific payload shape.

## Architecture

### 1. Canonical Billing Models

Add the following control-plane persistence:

- `billing_plans`
  - plan code, display name, cadence, currency, amount, trial days, branch limit, device limit, offline runtime hours, grace window days, feature flags, status
- `tenant_subscriptions`
  - tenant id, billing plan id, provider name, provider customer id, provider subscription id, lifecycle status, trial start, trial end, current period start, current period end, grace until, canceled at, last provider event id, last provider event at
- `tenant_entitlements`
  - tenant id, active plan code, lifecycle status, branch limit, device limit, offline runtime hours, grace until, suspend at, feature flags, override metadata, last policy change
- `subscription_webhook_events`
  - provider, event id, tenant id when resolved, event type, payload, processed status, received at, processed at, error

Optional and bounded:

- `tenant_billing_overrides`
  - platform-admin-only temporary overrides with expiry and reason

### 2. Control-Plane Services

Add a billing-lifecycle service that owns:

- billing plan CRUD and versioning,
- tenant subscription creation or mutation,
- trial issuance,
- provider bootstrap flow,
- webhook dedupe and event replay safety,
- entitlement recalculation,
- tenant suspension or reactivation decisions.

This service becomes the canonical owner of tenant lifecycle instead of leaving suspension semantics scattered across legacy-only code.

### 3. Platform-Admin Surface

Platform admin expands from onboarding-only into lifecycle control:

- billing plan list and creation,
- tenant subscription summary,
- tenant lifecycle status,
- grace or suspension reason,
- provider linkage visibility,
- manual suspend, reactivate, or expiring override actions.

Overrides must be explicit, bounded, and audited. They are not a second default billing system.

### 4. Owner-Web Surface

Owner web gains billing recovery and subscription posture:

- active plan visibility,
- trial days remaining,
- renewal status,
- renewal setup action for Cashfree or Razorpay,
- grace warning,
- suspension recovery posture.

Owner web must not infer entitlement locally. It should read canonical control-plane state and block operational or expansion actions accordingly.

### 5. Runtime Enforcement

Packaged runtime enforcement must use entitlement state, not a separate local billing rule.

Behavior by state:

- `TRIALING` or `ACTIVE`
  - normal access within plan limits
- `GRACE`
  - existing approved runtime can continue with bounded continuity
  - no new device activation or entitlement-increasing operations
- `SUSPENDED`
  - no new activation or unlock
  - no indefinite offline bypass; continuity windows must respect entitlement expiry

This means auth, store-desktop activation, and offline continuity must all consult canonical entitlement state before issuing or refreshing access.

## Enforcement Rules

### 1. Owner-Web

- `TRIALING` and `ACTIVE`
  - normal use within limits
- `GRACE`
  - billing and recovery surfaces remain available
  - expansion actions that exceed plan limits are blocked
- `SUSPENDED`
  - operational access is blocked and recovery posture is shown

### 2. Packaged Runtime

- no new device approval or activation beyond `device_limit`
- no new branch additions beyond `branch_limit`
- offline continuity window is capped by entitlement policy
- suspended tenants cannot unlock or refresh runtime access

### 3. Plan Limits

Plan limits must be enforced at the control-plane write boundary:

- branch creation,
- device registration or approval,
- desktop activation,
- runtime lease or unlock,
- optional feature routes gated by feature flags.

## Error Handling

The lifecycle system must fail closed and visibly:

- missing subscription after trial expiry:
  - tenant moves to `SUSPENDED` once grace policy is exhausted
- invalid or duplicate webhook:
  - event is recorded and not double-applied
- provider transport failure during bootstrap:
  - no local fake entitlement is granted
- unresolved provider event:
  - tenant remains on prior canonical state until explicit transition succeeds
- expired override:
  - entitlement recalculates back to subscription-backed posture automatically

## Testing Strategy

Backend:

- billing plan CRUD and versioning,
- onboarding trial issuance,
- provider bootstrap request generation for Cashfree and Razorpay,
- webhook dedupe and idempotent lifecycle transitions,
- renewal success to `ACTIVE`,
- renewal failure to `GRACE`,
- grace expiry to `SUSPENDED`,
- successful recovery to `ACTIVE`,
- plan-limit enforcement on branch and device actions.

App surfaces:

- platform-admin billing plan and tenant lifecycle views,
- owner subscription and grace posture,
- owner suspension blocking,
- packaged runtime activation or unlock blocked for suspended tenants.

## Rollout

This slice makes the control plane the source of truth for Store SaaS lifecycle:

- payment providers remain external rails,
- the control plane owns subscription and entitlement truth,
- platform admin owns plan and lifecycle operations,
- owner-web and packaged runtime consume one canonical enforcement model.

Later work can extend this with richer revenue operations, coupons, dunning, or CI-driven provider automation without changing the core entitlement boundary.
