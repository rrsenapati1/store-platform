# Offline Branch Operations Design (CP-018)

Date: 2026-04-14  
Owner: Codex  
Status: Ready for user review

## Goal

Extend Store runtime continuity from non-authoritative outbox replay into bounded branch-local business continuity so checkout-critical branch operations can continue during cloud loss and reconcile safely when connectivity returns.

This design must:

- keep the first authoritative offline slice narrow
- preserve explicit audit and replay semantics
- keep control-plane Postgres as the final system of record
- avoid granting standalone offline authority to every device
- protect inventory, invoice, and GST invariants during reconciliation

## Product Decision

The first `CP-018` slice is:

- `offline sale checkout only`

The first slice does not include:

- returns
- exchanges
- stock adjustments
- purchase receipt or receiving
- refund authority
- credit-note issuance

This is intentional. Checkout continuity is the highest-value outage path and the smallest offline authority boundary that still proves the architecture.

## Current Context

Store already has:

- control-plane-authoritative sales, returns, exchanges, inventory, and print
- approved packaged desktop auth with bounded offline re-entry
- runtime cache hydration behind a non-authoritative local adapter
- replay-safe local outbox continuity for:
  - device heartbeats
  - invoice print requests
  - credit-note print requests
- branch hub runtime and spoke relay posture through `CP-017`

Store explicitly does not yet have:

- authoritative offline sale issuance
- local invoice continuity series
- local authoritative stock decrement during outage
- replay of branch-local business writes into the control plane
- conflict review posture for offline business reconciliation

## Non-Goals

`CP-018` will not:

- make every packaged desktop independently authoritative offline
- reuse the current runtime cache as the authority store for offline sales
- introduce offline returns, exchanges, or refunds in the first slice
- support arbitrary offline price or tax editing
- treat the hub as a permanent replacement for cloud authority
- silently mutate branch stock on replay conflicts

## Authority Boundary

### Final Authority

Control-plane Postgres remains the final system of record for:

- branch inventory
- sales history
- invoice history
- GST reporting posture
- branch conflict state

### Temporary Branch Authority

During cloud loss, one approved `branch_hub` may hold bounded temporary branch authority for:

- sale draft creation
- tax computation using last-known branch pricing and GST data
- local continuity invoice reservation
- local stock decrement against a branch-local snapshot plus mutation ledger
- local print emission

This temporary authority is valid only when all of these are true:

- the device is an approved `branch_hub`
- staff auth is still within the offline-valid window
- the hub has a valid local continuity store
- branch continuity mode is enabled by policy
- the hub has a sufficiently fresh branch data baseline

### Spoke Boundary

`desktop_spoke` and future `mobile_store_spoke` devices do not become independent offline authorities.

Spokes may:

- build checkout intents
- submit those intents to the hub
- display offline checkout posture

Only the hub may:

- finalize offline sale issuance
- reserve continuity invoice numbers
- decrement authoritative local branch stock during outage
- replay offline sales to the control plane

## Local Persistence Boundary

The existing runtime cache remains cache-only and non-authoritative.

`CP-018` requires a separate local continuity persistence boundary so authoritative outage writes are not mixed with cache hydration data.

Recommended local store:

- dedicated SQLite file in runtime home
- example: `store-runtime-continuity.sqlite3`

Recommended local structures:

- `continuity_inventory_snapshot`
  - last known branch stock position per product or batch
- `continuity_invoice_counter`
  - branch-local continuity invoice sequence
- `offline_sales`
  - append-only offline sale header records
- `offline_sale_lines`
  - line-level detail for each offline sale
- `offline_stock_mutations`
  - local authoritative stock deltas caused by offline checkout
- `offline_replay_queue`
  - pending replay jobs with idempotency keys and status
- `offline_conflicts`
  - explicit replay failures requiring operator review

The continuity store must not be silently rewritten by background cache hydration.

## Offline Sale Contract

Each offline sale must contain:

- `continuity_sale_id`
- `continuity_invoice_number`
- `branch_id`
- `hub_device_id`
- `staff_actor_id`
- `issued_offline_at`
- `idempotency_key`
- `sale_mode = OFFLINE_CONTINUITY`
- customer summary fields as allowed by the sale flow
- payment summary
- line details
- tax totals
- reconciliation state

Recommended reconciliation states:

- `PENDING_REPLAY`
- `REPLAYING`
- `RECONCILED`
- `CONFLICT`
- `REJECTED`

Recommended payment support for the first slice:

- cash
- UPI as operator-declared receipt

Deferred from the first slice:

- split payments
- store credit
- refunds
- customer account settlement

## Continuity Invoice Policy

Offline sales must not consume the ordinary cloud invoice-numbering path directly.

Instead, the hub should use a branch-local continuity series that is:

- clearly distinguishable
- monotonic within the branch continuity store
- auditable against replayed sales

Recommended rule:

- continuity invoice numbers are reserved locally during outage
- replay preserves the continuity identifier as audit metadata
- the control plane may:
  - preserve the displayed continuity number as an external reference
  - map the final authoritative sale into the main invoice sequence
  - or preserve a dedicated continuity sequence if required by product policy

This policy decision must stay explicit in implementation and not be left to accidental numbering behavior.

## Operator Flow

1. Staff signs into an approved desktop or spoke through the existing device and PIN flow.
2. Cloud becomes unavailable, but the approved branch hub remains healthy.
3. The runtime enters `offline continuity mode`.
4. Staff creates a checkout using the last-known branch catalog and inventory snapshot.
5. The hub:
   - validates local readiness
   - reserves a continuity invoice number
   - computes totals and GST
   - records the offline sale
   - decrements local stock
   - queues the sale for reconciliation
   - prints locally if needed
6. The sale appears in runtime history as `Offline` and `Pending reconciliation`.
7. When cloud returns, the hub replays pending offline sales to the control plane.
8. Each sale moves to `Reconciled` or `Conflict review required`.

## Restrictions And Safety Rules

To keep this slice bounded and defensible:

- no offline authority without a valid hub
- no offline authority after local auth expiry
- no offline sale if no valid inventory snapshot exists
- no manual tax-line editing
- no unbounded price override behavior
- no hidden replay; reconciliation state must always remain visible
- no silent stock correction after replay divergence
- no generic “offline mode” that quietly covers unsupported flows

If local readiness cannot be proven, checkout must stop instead of pretending continuity exists.

## Reconciliation Contract

Replay into the control plane must be explicit and idempotent.

Recommended replay endpoint posture:

- sync-authenticated machine path
- hub submits one offline sale payload plus:
  - `continuity_sale_id`
  - `continuity_invoice_number`
  - `idempotency_key`
  - `issued_offline_at`
  - `hub_device_id`
  - `staff_actor_id`

The control plane must respond with one of these outcomes:

- `accepted`
- `accepted_with_adjustment_metadata`
- `conflict_review_required`
- `rejected_invalid`

### Acceptance

If accepted:

- authoritative sale is written once
- branch inventory is updated once
- replay metadata preserves continuity identifiers
- local record transitions to `RECONCILED`

### Conflict

If replay detects divergence such as:

- stock mismatch
- invalid product reference
- branch policy violation
- already-replayed payload with conflicting shape

the control plane must create an explicit conflict record and return a conflict result. The local hub record transitions to `CONFLICT`.

### Duplicate Replay

If the same idempotency key is replayed again, the control plane must return the prior accepted result rather than double-writing the sale.

## Inventory Rule

During outage:

- local hub inventory becomes the branch-local operational authority
- stock is decremented immediately when an offline sale is committed

After reconnect:

- control-plane inventory becomes final again
- replay does not silently overwrite divergence
- any mismatch becomes an explicit branch conflict

The implementation must favor visibility over convenience.

## Runtime UX

The operator must never be unclear about continuity posture.

Recommended runtime UI:

- persistent banner:
  - `Cloud unavailable. Branch continuity mode is active.`
- visible counters:
  - pending offline sales
  - last successful replay
  - unresolved conflicts
- history badges:
  - `Offline`
  - `Pending reconciliation`
  - `Reconciled`
  - `Conflict`
- dedicated review section for replay outcomes and operator follow-up

## Testing Strategy

### Backend

- replay accepts an offline sale exactly once
- duplicate replay returns prior result
- invalid replay becomes explicit rejection
- stock divergence becomes explicit conflict
- continuity identifiers remain preserved in replay metadata

### Desktop

- hub enters offline continuity mode only when readiness checks pass
- offline sale decrements local stock and queues replay
- replay transitions sale to reconciled or conflict
- spokes cannot finalize offline sale without hub authority

### Native

- continuity store persists across restart
- continuity invoice numbers remain monotonic
- replay queue survives process restart
- local conflict records remain durable

### End-To-End

- sell online
- lose cloud
- sell offline through hub
- restore cloud
- replay and verify final branch stock, sale history, and reconciliation state

## Rollout Order

1. Add dedicated local continuity storage and offline sale ledger.
2. Add continuity-mode readiness checks and explicit UI posture.
3. Allow offline sale creation on the hub only.
4. Add replay queue and backend reconciliation endpoint.
5. Add conflict recording and review UI.
6. Only after this slice stabilizes, consider offline spoke checkout assistance and later returns or exchanges.

## First Implementation Slice

The first implementation slice should include:

- local continuity store
- continuity invoice numbering
- offline sale creation on the packaged hub UI
- pending reconciliation list
- replay endpoint and reconciliation result states

The first implementation slice should defer:

- offline returns
- offline exchanges
- offline refunds
- split payments
- store credit settlement
- deeper operator override policy

## Success Criteria

`CP-018` is successful when:

- approved branch hubs can continue sale checkout during cloud loss
- offline sales are durably recorded locally
- local stock decreases are visible immediately
- replay into the control plane is idempotent and explicit
- conflict outcomes are visible and auditable
- the product does not blur cache continuity with authoritative offline business state
