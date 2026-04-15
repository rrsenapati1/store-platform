# Shelf/Backroom Restock Workflow Design

## Goal

Add the next `V2-004` store-operations slice by giving branch operators an explicit shelf/backroom restock workflow instead of relying on low-stock awareness alone.

## Why This Slice

The current `V2-004` work now covers reviewed receiving, reviewed stock counts, reviewed expiry disposition, and branch replenishment policy. That still leaves a daily operational gap:

- low-stock items can be identified, but there is no explicit restock workflow
- branch operators cannot track what still needs to be picked from backroom stock
- there is no task board showing whether restock work is pending, picked, or completed
- staff have to manage shelf refill work out-of-band instead of inside the control plane

This slice closes that gap without pretending the system already has true shelf/bin sublocation inventory.

## Scope

### Included

- control-plane restock task sessions for a single branch product at a time
- restock task creation from branch low-stock posture
- source posture recording:
  - `BACKROOM_AVAILABLE`
  - `BACKROOM_UNCERTAIN`
- requested quantity and picked quantity tracking
- explicit task lifecycle:
  - `OPEN`
  - `PICKED`
  - `COMPLETED`
  - `CANCELED`
- branch restock board for recent and active task posture
- owner-web workflow for:
  - creating a restock task for a branch product
  - marking a task picked
  - completing or canceling a task

### Explicitly Deferred

- shelf/bin/location inventory modeling
- automatic inventory movements between shelf and backroom
- mobile/tablet restock execution
- multi-operator picking workflows
- route optimization or warehouse orchestration
- procurement automation from restock tasks

## Architecture

### Backend

Do not fake sublocation inventory. The current inventory model still has one authoritative branch `stock_on_hand` number, so the first shelf/backroom slice must be a task workflow rather than a stock-movement workflow.

Add a new `restock_task_sessions` model with:

- `tenant_id`
- `branch_id`
- `product_id`
- `task_number`
- `status`
- `stock_on_hand_snapshot`
- `reorder_point_snapshot`
- `target_stock_snapshot`
- `suggested_quantity_snapshot`
- `requested_quantity`
- `picked_quantity`
- `source_posture`
- `note`
- `completion_note`

The task session is an operational coordination artifact. It does not post inventory ledger movement and it does not change `stock_on_hand`.

### State Model

`restock_task_session.status`

- `OPEN`
- `PICKED`
- `COMPLETED`
- `CANCELED`

Rules:

- `OPEN`
  - task has been raised
  - operator may record pick quantity, or cancel
- `PICKED`
  - task has a picked quantity
  - operator may complete or cancel
- `COMPLETED`
  - immutable
  - signals shelf-restock work is done
- `CANCELED`
  - immutable
  - signals abandoned or invalid task with no inventory impact

Additional guards:

- only one active (`OPEN` or `PICKED`) restock task per branch/product
- `requested_quantity > 0`
- `picked_quantity >= 0`
- `picked_quantity <= requested_quantity`
- completion only from `PICKED`
- cancellation only from `OPEN` or `PICKED`

### Read Model

Add a branch `restock board` derived from:

1. current replenishment board
2. explicit restock task sessions
3. branch product metadata

The board should answer:

- which low-stock items currently have no active task
- which items already have an active restock task
- which tasks are `OPEN`, `PICKED`, `COMPLETED`, or `CANCELED`

It should expose task snapshots rather than recomputing history from later stock changes.

## API Shape

Add new inventory routes:

- `GET /v1/tenants/{tenant_id}/branches/{branch_id}/restock-board`
- `POST /v1/tenants/{tenant_id}/branches/{branch_id}/restock-tasks`
- `POST /v1/tenants/{tenant_id}/branches/{branch_id}/restock-tasks/{task_id}/pick`
- `POST /v1/tenants/{tenant_id}/branches/{branch_id}/restock-tasks/{task_id}/complete`
- `POST /v1/tenants/{tenant_id}/branches/{branch_id}/restock-tasks/{task_id}/cancel`

Create task payload:

- `product_id`
- `requested_quantity`
- `source_posture`
- `note?`

Pick payload:

- `picked_quantity`
- `note?`

Complete payload:

- `completion_note?`

Cancel payload:

- `cancel_note?`

Restock board response:

- branch summary counts by status
- records[]
  - task id / task number
  - product metadata
  - task status
  - stock snapshot
  - replenishment-policy snapshot
  - requested quantity
  - picked quantity
  - source posture
  - whether an active task already exists

## Owner-Web UX

Keep the first slice `owner-web first`, matching the current reviewed-operations pattern.

The new restock section should support:

1. low-stock task creation
- choose the first low-stock branch product from the replenishment board
- enter requested quantity
- choose source posture
- add an optional note

2. active task execution
- show latest active task details
- record picked quantity
- complete or cancel the task

3. restock board visibility
- show status counts
- show task list with product, status, requested quantity, picked quantity, and source posture

This keeps the first restock slice small and operationally useful without widening into mobile execution or location-aware inventory.

## Error Handling

The backend must reject:

- creating a task for an unknown product or branch
- creating a second active task for the same branch/product
- negative or zero requested quantity
- picking more than requested
- completing a non-`PICKED` task
- canceling a `COMPLETED` task

Owner-web should surface the existing control-plane error message directly.

## Testing

### Backend

- create restock task for a low-stock item
- reject duplicate active task for same product
- reject picked quantity greater than requested quantity
- allow `OPEN -> PICKED -> COMPLETED`
- allow `OPEN -> CANCELED` and `PICKED -> CANCELED`
- restock board returns correct status counts and task snapshots
- no restock transition posts any inventory ledger entry

### Owner-Web

- operator can create restock task from low-stock posture
- operator can mark task picked
- operator can complete task
- board reflects task status transitions
- duplicate active-task attempts surface backend error cleanly

## Success Criteria

This slice is done when:

- low-stock products can produce explicit restock tasks
- branch operators can track `OPEN -> PICKED -> COMPLETED/CANCELED`
- restock work is visible on a board instead of living in memory
- the inventory ledger and `stock_on_hand` rules remain unchanged
- backend and owner-web regression suites cover the workflow
