# Store Desktop Reviewed Expiry Design

Date: 2026-04-16

## Goal

Replace the desktop runtime's direct batch expiry write-off shortcut with the real reviewed expiry workflow already used by the control plane. Desktop operators should load the branch expiry report, open a review session for a lot, record the proposed write-off quantity and reason, and only approval should mutate inventory.

## Scope

In scope for this slice:

- desktop runtime reviewed expiry UI in `apps/store-desktop`
- control-plane client support for expiry review board and session lifecycle routes
- runtime workspace state for:
  - expiry report
  - expiry review board
  - active reviewed session
  - draft quantity/reason/note inputs
- desktop tests for reviewed expiry behavior

Out of scope:

- owner-web changes
- mobile/tablet changes
- backend schema or lifecycle redesign
- multi-lot bulk review
- disposal vendor workflows

## Existing Gap

Desktop currently exposes a `StoreBatchExpirySection` that:

1. loads the branch expiry report
2. accepts a quantity and reason
3. directly writes off the first expiring lot

That no longer matches the real authority model. The control plane already has the reviewed expiry lifecycle:

- `OPEN`
- `REVIEWED`
- `APPROVED`
- `CANCELED`

Desktop should stop using the shortcut path and move to the same review-session model.

## Client Boundary

Extend the desktop control-plane client with reviewed expiry routes for:

- load batch expiry board
- create batch expiry session
- record reviewed quantity/reason
- approve session
- cancel session

These should reuse the existing control-plane route family rather than inventing a desktop-only API. The desktop client should expose typed responses for:

- `ControlPlaneBatchExpiryBoard`
- `ControlPlaneBatchExpiryReviewSession`
- `ControlPlaneBatchExpiryReviewApproval`

If any of these types are missing or incomplete in `packages/types`, fill only the missing shape required by desktop.

## Runtime State

Extend `useStoreRuntimeWorkspace` with reviewed expiry state for:

- `batchExpiryReport`
- `batchExpiryBoard`
- `activeBatchExpirySession`
- `expiryProposedQuantity`
- `expiryWriteOffReason`
- `expirySessionNote`
- `expiryReviewNote`
- `latestBatchWriteOff`

And actions for:

- load report
- load board
- create session for a selected lot
- record active session review
- approve active session
- cancel active session

Desktop should treat expiry as a real session workflow:

- session create does not mutate inventory
- review record does not mutate inventory
- only approval posts the write-off and refreshes inventory snapshot/report posture
- cancel leaves inventory unchanged

## UI Flow

Upgrade `StoreBatchExpirySection` from a shortcut card into a reviewed workflow surface.

Expected flow:

1. operator loads branch expiry report
2. operator sees the current expiry report and existing reviewed-session board
3. operator selects or opens a review session for a lot
4. operator enters proposed quantity and reason, plus optional notes
5. operator records the review
6. operator approves or cancels the session
7. latest approved write-off is shown only after approval

The UI should show both:

- raw lot/report posture
- reviewed-session posture

This keeps the runtime operationally useful without implying that opening or reviewing a session already changed stock.

## Failure Posture

Desktop should preserve explicit operator errors:

- failed report load
- failed board load
- failed session create
- failed review record
- failed approve
- failed cancel

Do not silently fall back to the old direct write-off shortcut. Once desktop adopts reviewed expiry, that becomes the only runtime path.

## Testing

Required coverage:

- client tests for expiry board/session routes
- workspace tests for:
  - loading report + board
  - creating a session
  - recording a review
  - approving a session
  - canceling a session
- section tests for:
  - selected lot display
  - reviewed-session controls
  - latest approved write-off visibility only after approval

Verification for implementation should include:

- `npm run test --workspace @store/store-desktop`
- `npm run typecheck --workspace @store/store-desktop`
- `npm run build --workspace @store/store-desktop`
- `git diff --check`
