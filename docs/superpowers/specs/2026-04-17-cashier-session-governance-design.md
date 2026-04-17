# Cashier Session Governance Design

Date: 2026-04-17  
Owner: Codex  
Status: Draft for review

## Goal

Start `V2-006` with a first-class `cashier session governance` boundary for live branch billing.

The system already has:

- staff profiles
- branch memberships and role capabilities
- device registration and activation
- store runtime authentication and local unlock posture

What it does not yet have is an explicit operational rule that says:

- which cashier is currently operating a checkout device
- when that terminal session started
- whether billing and returns are currently allowed on that device
- how the session is closed or force-closed

This slice adds that missing authority boundary.

## Why This Is The First V2-006 Slice

`V2-006` includes attendance, shifts, branch/device policies, stronger audit, and cashier controls. The cleanest first slice is cashier-session governance because it directly governs live revenue operations without pulling payroll or scheduling complexity into the first cut.

It is the smallest slice that materially improves branch controls:

- it gates sales and returns behind an explicit branch runtime session
- it links every sale/return to a real cashier session record
- it gives owners operational visibility into active tills/terminals
- it creates a strong base for later shift reconciliation and attendance

Attendance-first would create staff-presence records without yet governing the actual terminal authority that matters most during checkout.

## Product Boundary

Included in this slice:

- control-plane-owned cashier session records
- Store Desktop open-session and close-session flow
- billing and sale-return gating on active cashier session
- sale and return linkage to `cashier_session_id`
- owner-web active-session board and force-close action
- session history and summary visibility
- audit events for session open/close/force-close

Explicitly not included:

- attendance clock-in/clock-out
- shift rosters
- payroll or labor calculations
- cash drawer denomination balancing
- branch policy packs beyond cashier-session requirements
- mobile/tablet cashier session UX

## Core Model

Add `branch_cashier_sessions` as a control-plane authority model.

Recommended fields:

- `id`
- `tenant_id`
- `branch_id`
- `device_registration_id`
- `staff_profile_id`
- `runtime_user_id`
- `opened_by_user_id`
- `closed_by_user_id`
- `status`
  - `OPEN`
  - `CLOSED`
  - `FORCED_CLOSED`
- `session_number`
- `opening_float_amount`
- `closing_note`
- `opening_note`
- `opened_at`
- `closed_at`
- `last_activity_at`
- `force_close_reason`
- audit timestamps

This is an operational session record, not a local cache artifact.

## Authority Rules

1. One active cashier session per device.
   - a device cannot have more than one `OPEN` cashier session

2. One active cashier session per staff profile per branch.
   - for the first slice, a staff profile cannot operate multiple open branch sessions simultaneously in the same branch

3. Billing requires an open cashier session.
   - direct sale creation is rejected if no valid session is attached
   - sale returns are rejected if no valid session is attached
   - checkout payment session creation is rejected if no valid session is attached

4. Session ownership follows the live runtime actor.
   - the runtime actor must match the activated staff/device pair for normal open/close flows

5. Force-close is an owner/manager recovery action.
   - owner-web can close abandoned sessions when a device is stuck, lost, or left signed in

6. Closing a session does not retroactively rewrite billing history.
   - already-posted sales and returns remain linked to the original session

## Billing Integration

Extend sales, returns, and checkout session records with nullable `cashier_session_id`.

Rules:

- checkout payment session creation stores `cashier_session_id`
- finalized sale stores `cashier_session_id`
- pending/approved sale returns store `cashier_session_id`

This gives the system a durable answer to:

- which session created this invoice
- which session initiated this refund
- which device/staff combination was responsible

## Backend API

Add a dedicated branch cashier-session surface.

Recommended routes:

- `GET /v1/tenants/{tenant_id}/branches/{branch_id}/cashier-sessions`
  - optional filters: `status`, `staff_profile_id`, `device_id`
- `POST /v1/tenants/{tenant_id}/branches/{branch_id}/cashier-sessions`
- `GET /v1/tenants/{tenant_id}/branches/{branch_id}/cashier-sessions/{cashier_session_id}`
- `POST /v1/tenants/{tenant_id}/branches/{branch_id}/cashier-sessions/{cashier_session_id}/close`
- `POST /v1/tenants/{tenant_id}/branches/{branch_id}/cashier-sessions/{cashier_session_id}/force-close`

Create payload:

- `device_registration_id`
- `staff_profile_id`
- `opening_float_amount`
- `opening_note`

Close payload:

- `closing_note`

Force-close payload:

- `reason`

The billing service should then require `cashier_session_id` on:

- checkout pricing-session dependent flows where authority matters
- checkout payment session creation
- sale creation
- sale-return creation

The runtime should not fabricate local cashier sessions offline. This remains cloud authority.

## Store Desktop UX

Add a dedicated cashier-session section inside the runtime workspace.

Expected flow:

1. cashier signs into the device runtime
2. if no active cashier session exists, billing surfaces show a blocked posture
3. cashier opens a session:
   - opening float
   - optional opening note
4. runtime shows active session posture:
   - cashier name
   - device name/code
   - opened at
   - opening float
5. billing and returns become available
6. cashier closes the session when done

Billing posture changes:

- if no active cashier session exists:
  - disable invoice creation
  - disable return submission
  - disable provider-backed checkout session creation
  - show explicit reason, not silent disabled state

This should integrate into existing Store Desktop runtime flows instead of creating a second app shell.

## Owner Web UX

Owner web needs an operational oversight surface, not cashier execution controls.

Expected owner actions:

- view active cashier sessions by branch
- inspect who opened each session and on which device
- view recently closed sessions
- force-close abandoned sessions

This can live in the existing workforce/branch control area rather than creating a standalone governance product surface.

## Audit And Reporting Posture

Every session transition should create an audit event:

- `cashier_session.opened`
- `cashier_session.closed`
- `cashier_session.force_closed`

The first slice should also expose minimal session summary fields:

- total linked sales count
- total linked returns count
- gross billed amount during the session

These are sufficient for session governance without yet building full till reconciliation.

## Error Handling

Key failure cases:

- session already open for this device
- session already open for this staff profile in branch
- session closed/force-closed before billing action
- device/staff mismatch on open or close
- force-close on already-closed session
- runtime attempts billing without a valid session

All of these should fail explicitly with operator-usable messages.

## Testing

Backend tests:

- create cashier session
- reject duplicate open session on same device
- reject duplicate open session for same staff in branch
- close session successfully
- force-close session successfully
- billing rejects missing/closed cashier session
- sale and return records store `cashier_session_id`
- session summary fields reflect linked sales/returns

Store Desktop tests:

- blocked billing posture before session open
- open cashier session enables billing
- close cashier session disables billing again
- sale payload carries `cashier_session_id`
- return flow carries `cashier_session_id`

Owner Web tests:

- active-session board loads
- force-close action works
- session history renders open/closed posture

## Rollout

Recommended order:

1. add control-plane cashier-session model, migration, repository, schema, and service
2. add cashier-session routes
3. integrate billing, returns, and checkout payment sessions with `cashier_session_id`
4. add Store Desktop open/close session UX and billing gating
5. add owner-web oversight and force-close UX
6. verify full backend, desktop, and owner-web flows

## Success Criteria

This slice is complete when:

- Store Desktop cannot bill or process returns without an open cashier session
- owners can see and force-close active cashier sessions
- sales and returns are linked to cashier sessions
- session governance is control-plane-owned and auditable
- the slice creates a strong base for later attendance, shifts, and reconciliation
