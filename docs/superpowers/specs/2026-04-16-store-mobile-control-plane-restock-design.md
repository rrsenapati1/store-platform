# Store Mobile Control-Plane Restock Design

## Goal

Replace the Android runtime's in-memory assisted restock flow with a real control-plane-backed shelf/backroom restock workflow using the paired runtime `tenantId` and `branchId`.

## Scope

This slice is limited to assisted restock on Store Mobile and Inventory Tablet.

Included:
- control-plane reads for:
  - `restock-board`
- control-plane mutations for:
  - create restock task
  - pick restock task
  - complete restock task
  - cancel restock task
- remote Android restock repository
- Store Mobile wiring swap for restock only

Not included:
- receiving, stock-count, or expiry changes beyond existing work
- shelf/bin/location inventory modeling
- offline fallback for remote restock

## Backend Boundary

The control plane already exposes the full reviewed restock workflow:
- `GET /v1/tenants/{tenant_id}/branches/{branch_id}/restock-board`
- `POST /v1/tenants/{tenant_id}/branches/{branch_id}/restock-tasks`
- `POST /v1/tenants/{tenant_id}/branches/{branch_id}/restock-tasks/{id}/pick`
- `POST /v1/tenants/{tenant_id}/branches/{branch_id}/restock-tasks/{id}/complete`
- `POST /v1/tenants/{tenant_id}/branches/{branch_id}/restock-tasks/{id}/cancel`

So this slice does not require a new backend route. It should verify that the existing backend shape is used directly from mobile.

## Mobile Architecture

Extend the existing mobile control-plane client with:
- `getRestockBoard`
- `createRestockTask`
- `pickRestockTask`
- `completeRestockTask`
- `cancelRestockTask`

Then add `RemoteRestockRepository` that maps control-plane restock models into the existing Android restock domain:
- `RestockBoardResponse` -> `RestockBoard`
- `RestockTaskResponse` -> `RestockTask`

The `RestockViewModel` and `RestockScreen` should remain largely unchanged. This is a repository swap, not a UI redesign.

## Runtime Wiring

`StoreMobileApp` should:
- keep using the paired runtime `branchId`
- build a remote restock repository when session + paired device context are present
- keep the current scanned-product-driven task creation path

## Failure Posture

Restock becomes truly remote-backed for paired runtimes. If the control plane call fails:
- surface a real error in restock state
- do not silently fall back to in-memory restock

## Verification

Required verification:
- targeted backend test proving existing restock workflow remains green
- targeted Android tests for:
  - control-plane client restock calls
  - remote restock repository mapping
  - runtime context helper / repository selection
- full `apps/store-mobile` unit-test run
- `npm run ci:store-mobile`
- `git diff --check`
