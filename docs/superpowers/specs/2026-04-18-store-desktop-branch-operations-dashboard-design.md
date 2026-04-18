# Store Desktop Branch Operations Dashboard Design

Date: 2026-04-18
Owner: Codex
Status: Approved for implementation

## Goal

Start `V2-007 Reporting + decision support` with a `store-desktop` branch manager dashboard instead of adding manager-facing reporting to `owner-web`.

The first slice should give branch managers a single runtime surface for:

- branch trade posture
- workforce/session posture
- stock-operation exceptions
- runtime/offline health

## Why This Slice

The repo already treats `owner-web` as the owner/back-office shell and `store-desktop` as the branch runtime shell.

Branch managers already fit the runtime-side access model:

- `store_manager` is branch-scoped
- `reports.view` already exists at branch scope
- the branch runtime already loads most of the operational state needed for a first dashboard

So the first dashboard slice should deepen the runtime, not create a second manager-facing back-office product.

## Scope

Included:

- new `StoreBranchOperationsDashboardSection` in `apps/store-desktop`
- runtime summary cards for current branch operations
- manual dashboard refresh action for exception boards
- read-only composition from existing control-plane routes
- test coverage for the new dashboard section
- ledger/worklog update to mark `V2-007` as started

Not included:

- owner-web manager dashboards
- new control-plane reporting authority
- advanced trend analytics
- decision-support recommendations
- charting library adoption
- mobile/tablet reporting surfaces

## Design

### Surface

Add a dedicated section near the top of `StoreRuntimeWorkspace`.

The section should be visible only when a runtime session is active, like the other branch runtime sections.

### Data Sources

Use existing runtime state immediately:

- `sales`
- `activeShiftSession`
- `attendanceSessions`
- `cashierSessions`
- `branchRuntimePolicy`
- `runtimeHeartbeat`
- offline continuity counters and messages

Load exception boards on demand through existing routes:

- `replenishment-board`
- `restock-board`
- `receiving-board`
- `stock-count-board`
- `batch-expiry-report`

This keeps the slice thin and avoids inventing a new backend read model before the runtime dashboard proves its shape.

### Dashboard Groups

#### 1. Branch Trade Posture

- today sales count
- today billed total
- latest invoice number

#### 2. Workforce And Session Posture

- active shift name/status
- open attendance count
- open cashier count
- branch runtime policy summary

#### 3. Stock-Operation Exceptions

- low-stock product count
- open restock count
- receiving ready count
- received-with-variance count
- open stock-count session count
- expiring-soon lot count

Show short preview lists for the first relevant exception records.

#### 4. Runtime And Offline Health

- runtime heartbeat status
- pending offline sale count
- pending runtime mutation count
- offline conflict count
- offline continuity readiness/message
- runtime binding/service state

## UX Posture

The section should be read-only and fast to scan.

It should:

- show immediate posture from already-loaded runtime state
- provide one `Refresh dashboard` action
- update exception summaries after refresh
- avoid blocking checkout or other runtime actions

## Technical Boundaries

To avoid deepening the already-large `useStoreRuntimeWorkspace.ts`, the slice should:

- add a new dashboard section component
- add a small helper/action file for parallel dashboard loading
- keep workspace changes limited to wiring the section into the shell

No new backend schema or route is required in this slice.

## Testing

Add section-focused tests for:

- rendering current branch posture from runtime state
- dashboard refresh loading the exception boards
- stock exception summaries and preview records appearing after refresh

Keep the rest of the runtime suite green without requiring broad mock rewrites.

## Success Criteria

This slice is done when:

- store-desktop shows a branch manager operations dashboard
- branch managers can refresh exception posture from existing control-plane boards
- the dashboard stays runtime-only and read-only
- `V2-007` is started without creating a second reporting authority path
