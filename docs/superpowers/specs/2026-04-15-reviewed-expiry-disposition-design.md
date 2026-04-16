# Reviewed Expiry Disposition Design

Date: 2026-04-15

## Goal

Deepen the existing batch-expiry foundation into a reviewed operator workflow. Expiry write-offs should no longer be only a direct one-step mutation from the owner surface. Operators should open an expiry disposition session for a lot, record the proposed write-off quantity and reason, and only approval should post the inventory ledger mutation.

## Scope

In scope for this slice:

- control-plane expiry disposition session persistence
- explicit session lifecycle: `OPEN`, `REVIEWED`, `APPROVED`, `CANCELED`
- branch expiry board for operator visibility
- owner-web reviewed expiry workflow
- append-only `EXPIRY_WRITE_OFF` posting only on approval

Out of scope:

- automatic replenishment or purchase suggestions
- multi-lot batch actions
- mobile/tablet expiry execution
- disposal vendor workflows

## Backend Shape

Add a `batch_expiry_review_sessions` table keyed by tenant, branch, batch lot, and product. Each session stores:

- session number
- status
- lot remaining quantity snapshot at open time
- proposed write-off quantity
- write-off reason
- operator note and review note

Add bounded routes for:

- create session
- record reviewed quantity/reason
- approve session
- cancel session
- read expiry board

Approval must re-check current remaining quantity before posting a real write-off. Approved or canceled sessions remain historical; they are not deleted.

## Owner Workflow

The owner expiry surface should move from “write off first expiring lot” to:

1. load branch expiry report
2. open an expiry review session for the first available expiring lot
3. record proposed write-off quantity and reason
4. approve or cancel the reviewed session
5. on approval, refresh expiry report, inventory ledger, and inventory snapshot

The UI should not imply that opening a session changes inventory. Only approval does that.

## Testing

Backend coverage should prove:

- review sessions can be opened and recorded
- approved sessions post exactly one `EXPIRY_WRITE_OFF`
- canceled sessions do not mutate inventory
- approval fails if remaining quantity has fallen below the proposed write-off

Owner-web coverage should prove:

- operators can open, review, and approve an expiry session
- latest session and board state are visible
- inventory snapshot and ledger refresh after approval
