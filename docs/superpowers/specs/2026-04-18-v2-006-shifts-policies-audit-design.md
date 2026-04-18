# V2-006 Shift Controls, Branch Policies, And Workforce Audit Design

## Goal

Complete `V2-006` by extending the current attendance and cashier-session governance with:

- first-class branch shift sessions
- owner-managed branch runtime policies that gate live operator behavior
- stronger workforce audit visibility and CSV export posture

The slice must stay aligned with the current authority model: the control plane owns the records, Store Desktop enforces runtime posture, and owner-web manages branch governance.

## Why These Are The Remaining Slices

`V2-006` now already covers:

- cashier session governance
- attendance foundation
- cashier-session linkage through offline sale replay

The remaining exit-criteria gaps are:

- shift controls
- branch and device policy controls
- stronger audit and export posture

Those three pieces fit together operationally. A shift is the highest-level operator governance boundary. Attendance and cashier sessions belong inside a shift. Branch policies determine whether a branch requires those boundaries and whether degraded runtime behavior is allowed. Audit export turns that governance posture into something operators can inspect and share.

## Recommended Approach

Use one workforce-governance extension inside the existing `workforce` domain instead of creating separate scheduling, device-policy, and reporting subsystems.

This means:

- extend `workforce` models, repository, service, routes, and schemas
- extend Store Desktop runtime governance UI
- extend owner-web branch operations governance UI
- extend the existing audit event foundation with filtering and CSV export rather than inventing a new report store

## Scope

Included:

- branch shift sessions
- attendance linked to shifts
- cashier sessions linked to shifts through attendance
- branch runtime policy settings
- Store Desktop enforcement of branch runtime policies
- owner-web shift board, policy management, and workforce audit export
- CSV export for workforce governance events

Not included:

- payroll
- rota planning or future schedules
- break tracking
- biometric presence
- labor-cost analytics
- general-purpose audit export for every domain in the platform

## Architecture

### 1. Branch Shift Sessions

Add a new control-plane model: `branch_shift_sessions`.

Each shift session is a live branch-operations envelope that attendance sessions can join.

Core fields:

- `tenant_id`
- `branch_id`
- `shift_name`
- `shift_number`
- `status`
  - `OPEN`
  - `CLOSED`
  - `FORCED_CLOSED`
- `opened_by_user_id`
- `closed_by_user_id`
- `opening_note`
- `closing_note`
- `force_close_reason`
- `opened_at`
- `closed_at`
- `last_activity_at`

Attendance sessions gain:

- `shift_session_id`

That keeps the layering explicit:

- shift session = branch-wide operational window
- attendance session = staff presence on a device during a shift
- cashier session = billing authority nested under attendance

### 2. Branch Runtime Policy

Add one branch-owned policy record: `branch_runtime_policies`.

One record per branch. The policy is intentionally narrow and only covers controls that the current runtime can enforce immediately.

Recommended fields:

- `tenant_id`
- `branch_id`
- `require_shift_for_attendance`
- `require_attendance_for_cashier`
- `require_assigned_staff_for_device`
- `allow_offline_sales`
- `max_pending_offline_sales`
- `updated_by_user_id`
- `updated_at`

Defaults should preserve current behavior:

- `require_shift_for_attendance = false`
- `require_attendance_for_cashier = true`
- `require_assigned_staff_for_device = true`
- `allow_offline_sales = true`
- `max_pending_offline_sales = 25`

### 3. Workforce Audit Read And Export

Extend the audit event layer with branch and action filtering plus a CSV export read model for workforce-governance events.

The export should cover:

- shift open/close/force-close
- attendance open/close/force-close
- cashier open/close/force-close
- device registration
- branch runtime policy updates

That keeps the export meaningful for `V2-006` without pretending to solve all platform-wide audit export in one slice.

## Control-Plane API

### Shift Sessions

Routes:

- `GET /v1/tenants/{tenant_id}/branches/{branch_id}/shift-sessions`
- `POST /v1/tenants/{tenant_id}/branches/{branch_id}/shift-sessions`
- `POST /v1/tenants/{tenant_id}/branches/{branch_id}/shift-sessions/{shift_session_id}/close`
- `POST /v1/tenants/{tenant_id}/branches/{branch_id}/shift-sessions/{shift_session_id}/force-close`

Rules:

- only one open shift per branch
- attendance cannot open against a closed or forced-closed shift
- an open shift cannot be closed while it still has open attendance or open cashier activity underneath it

### Branch Runtime Policy

Routes:

- `GET /v1/tenants/{tenant_id}/branches/{branch_id}/runtime-policy`
- `PUT /v1/tenants/{tenant_id}/branches/{branch_id}/runtime-policy`

Rules:

- owner-web manages policy
- Store Desktop only reads policy
- policy updates generate audit events

### Workforce Audit Export

Routes:

- `GET /v1/tenants/{tenant_id}/branches/{branch_id}/workforce-audit-events`
- `GET /v1/tenants/{tenant_id}/branches/{branch_id}/workforce-audit-export`

The list route returns filtered JSON records. The export route returns a structured CSV payload:

- `filename`
- `content_type`
- `content`

Returning the CSV as a payload instead of forcing a browser download keeps the current React client simple and testable.

## Store Desktop Flow

### Shift-First Governance

Add a dedicated `StoreShiftSection`.

Operator flow:

1. open shift
2. clock in to attendance
3. open cashier session
4. bill or return as normal
5. close cashier session
6. clock out attendance
7. close shift

If policy does not require shift for attendance, the shift step becomes optional, but the UI should still show the current branch shift posture.

### Policy-Aware Runtime Behavior

Store Desktop should load branch runtime policy with the rest of the governance state and enforce:

- if `require_shift_for_attendance` is true, block attendance open when no shift is active
- if `require_attendance_for_cashier` is true, keep current cashier-session gating
- if `require_assigned_staff_for_device` is true, keep current device-to-staff enforcement
- if `allow_offline_sales` is false, disable offline sale queueing and surface a clear message
- if pending offline sales exceed `max_pending_offline_sales`, block further offline sale staging

This is the first real branch policy layer because the desktop runtime will actually change behavior from it.

## Owner-Web Flow

Add two new governance surfaces:

- `OwnerShiftSessionSection`
- `OwnerBranchRuntimePolicySection`

Extend governance visibility with:

- active shift board
- shift history
- force-close shift action
- runtime policy editor
- workforce audit event board
- workforce audit CSV export

These should sit alongside the existing attendance and cashier governance sections in the branch-operations area.

## Data And Snapshot Rules

- sales and returns continue to link to `cashier_session_id`
- cashier sessions continue to link to `attendance_session_id`
- attendance sessions now link to `shift_session_id`
- no sale or return needs a direct `shift_session_id` because the lineage already exists through cashier and attendance

This avoids redundant billing snapshots while preserving governance traceability.

## Error Handling

Store Desktop must surface policy failures clearly.

Examples:

- `Open a shift before clocking in on this branch.`
- `Offline sale continuity is disabled by branch policy.`
- `Pending offline sales limit reached for this branch policy.`
- `Close linked attendance and cashier sessions before closing this shift.`

Owner-web force-close actions should remain explicit and reason-bearing. No silent closures.

## Testing

Backend:

- shift open, close, force-close lifecycle
- attendance blocked when shift is required but absent
- attendance allowed without shift when policy disables the requirement
- policy update persistence and audit logging
- offline continuity blocked when branch policy disables it
- offline continuity blocked when pending-count limit is exceeded
- workforce audit list filters correctly
- workforce audit export returns CSV with expected rows

Store Desktop:

- shift must open before attendance when branch policy requires it
- attendance can open without shift when policy allows it
- offline sale queueing is blocked by branch policy
- offline sale queueing is blocked at policy limit
- cashier and attendance flows still work when policy allows them

Owner Web:

- shift board loads and force-close works
- branch runtime policy loads and saves
- workforce audit list loads
- workforce audit export returns previewable CSV payload

## Completion Criteria

`V2-006` is complete when:

- shift sessions exist and govern attendance posture
- branch runtime policies control real Store Desktop behavior
- owner-web can manage branch runtime policy and shift governance
- workforce governance events can be listed and exported
- the ledger can move `V2-006` from `In Progress` to `Done`
