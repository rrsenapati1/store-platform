# Reviewed Stock Count Sessions Design

## Goal

Deepen the current stock-count foundation from an immediate one-step quantity overwrite into a real reviewed workflow for branch operators. The first bounded slice adds blind count entry, review posture, approval, cancellation, and a stock-count board for `apps/owner-web` and the control-plane backend.

## Why This Slice

The existing stock-count path is too thin for serious store operations:

- it posts the variance immediately
- it cannot separate blind counting from supervisory review
- it has no count board or session status
- it does not preserve an auditable approval step before ledger movement

This slice fixes that without widening into multi-operator counting, mobile execution, or full replenishment planning.

## Scope

### Included

- control-plane stock count review sessions for a single product at a time
- blind count creation with expected quantity captured server-side
- reviewed state with expected/count/variance visibility after count entry
- approval that posts the actual `COUNT_VARIANCE` ledger entry
- cancellation before approval
- branch stock-count board for recent session posture
- owner-web workflow for:
  - opening a session
  - recording blind counted quantity
  - reviewing variance
  - approving or canceling the session

### Explicitly Deferred

- multi-product or zone-wide count sheets
- multi-operator counting and recount conflict workflows
- mobile/tablet execution against the new session workflow
- replenishment suggestions
- shelf/backroom task orchestration

## Architecture

### Backend

Keep the existing `stock_count_sessions` table as the approved historical record written by the old foundation route. Add a new reviewed workflow model instead of overloading the existing historical record:

- `stock_count_review_sessions`
  - session header and workflow state
  - captured expected quantity snapshot
  - blind counted quantity once entered
  - computed variance once counted
  - note/review note
  - status timestamps

The approval flow should:

1. validate the session is in `COUNTED`
2. create the existing approved historical stock-count record
3. post `COUNT_VARIANCE` to the append-only inventory ledger only on approval
4. mark the review session `APPROVED`

This preserves the existing inventory authority rule: inventory moves only when an approved operational action is finalized.

### Owner Web

Replace the current direct stock-count write UI with a session-oriented flow:

1. create session
2. enter blind count
3. review expected/count/variance
4. approve or cancel

The owner-web section should expose:

- latest active session
- session board
- blind count input for open sessions
- review details and approval controls for counted sessions
- latest approved historical stock count

## State Model

`stock_count_review_session.status`

- `OPEN`
- `COUNTED`
- `APPROVED`
- `CANCELED`

Rules:

- `OPEN`
  - expected quantity remains server-side only
  - operator can record blind count or cancel
- `COUNTED`
  - expected/count/variance become visible
  - operator can approve or cancel
- `APPROVED`
  - immutable
  - approved historical count exists
  - ledger impact already posted if needed
- `CANCELED`
  - immutable
  - no ledger impact

## API Shape

Add new inventory routes:

- `GET /v1/tenants/{tenant_id}/branches/{branch_id}/stock-count-board`
- `POST /v1/tenants/{tenant_id}/branches/{branch_id}/stock-count-sessions`
- `POST /v1/tenants/{tenant_id}/branches/{branch_id}/stock-count-sessions/{session_id}/record`
- `POST /v1/tenants/{tenant_id}/branches/{branch_id}/stock-count-sessions/{session_id}/approve`
- `POST /v1/tenants/{tenant_id}/branches/{branch_id}/stock-count-sessions/{session_id}/cancel`

Keep the existing `POST /stock-counts` route intact for compatibility, but move owner-web onto the reviewed-session workflow.

## Error Handling

The backend must reject:

- creating a reviewed session for an unknown product or branch
- recording a blind count for non-`OPEN` sessions
- approving non-`COUNTED` sessions
- canceling `APPROVED` sessions
- negative blind counts

Idempotency must stay explicit:

- approval may only succeed once
- repeated approval attempts after success should return a safe error, not duplicate ledger writes

## Testing

### Backend

- policy tests for session transition guards
- flow test proving:
  - create session
  - record blind count
  - inventory snapshot unchanged before approval
  - approve session
  - ledger posts one `COUNT_VARIANCE`
  - inventory snapshot updates after approval
- cancellation test proving canceled sessions never touch ledger

### Owner Web

- UI flow test for:
  - create session
  - record blind count
  - review variance
  - approve session
  - board/status updates

## Success Criteria

This slice is done when:

- control plane supports reviewed stock count sessions with approval-only ledger impact
- owner-web uses the reviewed workflow instead of direct stock-count posting
- the branch can see count-session posture on a board
- backend and owner-web regression suites cover the reviewed flow
