# Store Desktop Reviewed Stock Count Design

Date: 2026-04-16
Status: Draft
Task: V2-004

## Goal

Add a real reviewed stock-count workflow to `apps/store-desktop` so branch operators can run desktop count sessions through the same `OPEN -> COUNTED -> APPROVED/CANCELED` lifecycle already used by the control plane, owner-web, and mobile or tablet operations.

The desktop flow must stop relying on any shortcut-style count action and instead use the reviewed session model as the only authoritative stock-count path.

## Why This Slice

`V2-004` is already deepening day-to-day store operations across owner-web, mobile, and tablet. Desktop now has reviewed expiry and assisted restock, while reviewed stock count remains missing as a first-class runtime workflow.

That leaves desktop behind the other operator surfaces in one of the core inventory-control jobs. This slice closes that gap without redesigning the backend lifecycle or adding a second count authority model.

## Scope

### In Scope

- add a dedicated desktop `StoreStockCountSection`
- load the branch stock-count board from the control plane
- let the operator select a product from a board-driven list
- create a reviewed stock-count session for that product
- record a blind counted quantity while the session is `OPEN`
- approve or cancel the session after it becomes `COUNTED`
- surface the latest approved count result after approval
- keep desktop behavior aligned with the existing control-plane reviewed-session lifecycle

### Out of Scope

- scan-first counting
- mobile or tablet changes
- owner-web changes
- backend schema or lifecycle redesign
- a generic abstraction shared with reviewed expiry
- a one-step direct stock-count shortcut

## Existing Foundations

The control plane already exposes the required routes and schemas:

- `GET /v1/tenants/{tenant_id}/branches/{branch_id}/stock-count-board`
- `POST /v1/tenants/{tenant_id}/branches/{branch_id}/stock-count-sessions`
- `POST /v1/tenants/{tenant_id}/branches/{branch_id}/stock-count-sessions/{id}/record`
- `POST /v1/tenants/{tenant_id}/branches/{branch_id}/stock-count-sessions/{id}/approve`
- `POST /v1/tenants/{tenant_id}/branches/{branch_id}/stock-count-sessions/{id}/cancel`

Owner-web and mobile already use the reviewed lifecycle. Desktop should reuse those same response shapes and state transitions instead of inventing new route contracts or desktop-only payloads.

## Recommended Approach

Add a dedicated `StoreStockCountSection` and wire it directly into the existing desktop workspace state.

This is preferred over a scan-first or shared reviewed-workflow abstraction because:

- it is the smallest bounded desktop slice
- it follows the current control-plane lifecycle exactly
- it avoids mixing barcode lookup concerns into reviewed counting
- it avoids premature abstraction between stock count and expiry

## Architecture

### Desktop Boundary

The implementation lives entirely inside `apps/store-desktop`:

- `StoreStockCountSection.tsx` renders the workflow
- `useStoreRuntimeWorkspace.ts` owns state and actions
- `StoreRuntimeWorkspace.tsx` mounts the new section
- `client.ts` is extended only if any stock-count client helper is missing

No new backend behavior is introduced in this slice. The desktop runtime is only becoming a real consumer of the already-established reviewed stock-count authority.

### Authority Model

Desktop remains a client of the control plane:

- creating a session does not change stock
- recording a blind count does not change stock
- approving the session posts the authoritative stock-count effect
- canceling the session leaves authoritative stock unchanged

This preserves the control plane as the only source of truth and keeps desktop within the current branch-runtime authority boundary.

## State Model

Add the following workspace state:

- `stockCountBoard`
- `activeStockCountSession`
- `latestApprovedStockCount`
- `selectedStockCountProductId`
- `stockCountNote`
- `blindCountedQuantity`
- `stockCountReviewNote`

### Meaning

- `stockCountBoard` is the control-plane board read model for the branch
- `selectedStockCountProductId` identifies which product the operator wants to count
- `activeStockCountSession` is the currently relevant `OPEN` or `COUNTED` reviewed session
- `latestApprovedStockCount` stores the most recent approved count response for operator visibility
- `stockCountNote` is used during session creation and blind-count recording
- `blindCountedQuantity` is the operator-entered count while the session is still blind
- `stockCountReviewNote` is used during approve or cancel actions

## UI Flow

### Board-Driven Count Flow

1. Operator opens the desktop stock-count section.
2. Operator loads the stock-count board.
3. Desktop shows board records with:
   - session number
   - product name
   - SKU
   - session status
   - expected quantity only when the session is no longer blind
   - counted quantity and variance when available
4. Operator selects a product from the board-driven product list.
5. Operator opens a reviewed stock-count session.
6. While the session is `OPEN`, desktop only exposes:
   - blind counted quantity input
   - count note
   - record blind count action
7. After recording, the session becomes `COUNTED` and desktop reveals:
   - expected quantity
   - counted quantity
   - variance
   - review note input
   - approve action
   - cancel action
8. Approval updates:
   - `latestApprovedStockCount`
   - `stockCountBoard`
   - inventory snapshot, if the existing workspace contract already refreshes it as part of the count lifecycle
9. Cancel updates:
   - `activeStockCountSession`
   - `stockCountBoard`
   - no stock mutation output

## Blind-Count Rules

Blind count must stay blind until the `record` step succeeds.

Desktop must not reveal expected quantity while the session is still `OPEN`. The operator should only see expected quantity, counted quantity, and variance once the session has transitioned to `COUNTED` or `APPROVED`.

This keeps the desktop workflow aligned with the purpose of reviewed blind counts and avoids turning the reviewed session into a visible expected-vs-counted shortcut.

## Error Handling

### Request Failures

If board or session requests fail:

- show the existing desktop error surface through `workspace.errorMessage`
- do not silently fall back to a local or fake count path
- preserve current state until a successful reload or action completes

### Invalid State

Desktop actions should respect the reviewed lifecycle:

- `record` only when session is `OPEN`
- `approve` only when session is `COUNTED`
- `cancel` only when session is `OPEN` or `COUNTED`

The UI should disable or hide actions that are invalid for the current session state rather than relying on backend rejection for normal operator flow.

## Testing

### Client Coverage

Add or extend desktop client tests if stock-count client helpers are not already covered:

- board load helper
- create session helper
- record session helper
- approve session helper
- cancel session helper

### Workspace Flow Coverage

Add a desktop workspace flow test that verifies:

- board load
- product selection
- reviewed session creation
- blind count recording
- approval
- cancel

### Section Coverage

Add a section test that verifies:

- blind state hides expected quantity
- counted state reveals expected quantity and variance
- latest approved count only appears after approval

## Success Criteria

This slice is complete when:

- desktop can run reviewed stock-count sessions end-to-end
- blind count remains blind until record
- only approval posts authoritative stock change
- desktop stock-count behavior matches owner-web and mobile lifecycle semantics
- no one-step direct stock-count shortcut remains as the primary desktop path

