# Store Mobile Control-Plane Expiry Design

## Goal

Replace the Android runtime's in-memory reviewed expiry flow with a real control-plane-backed batch expiry workflow using the paired runtime `tenantId` and `branchId`.

## Scope

This slice is limited to reviewed expiry on Store Mobile and Inventory Tablet.

Included:
- control-plane reads for:
  - `batch-expiry-report`
  - `batch-expiry-board`
- control-plane mutations for:
  - create batch expiry review session
  - record reviewed expiry proposal
  - approve reviewed expiry proposal
  - cancel reviewed expiry proposal
- remote Android expiry repository
- Store Mobile wiring swap for expiry only

Not included:
- receiving, stock-count, or restock changes beyond existing work
- standalone direct write-off flow from mobile
- offline fallback for remote expiry

## Backend Boundary

The control plane already exposes the full reviewed expiry workflow:
- `GET /v1/tenants/{tenant_id}/branches/{branch_id}/batch-expiry-report`
- `GET /v1/tenants/{tenant_id}/branches/{branch_id}/batch-expiry-board`
- `POST /v1/tenants/{tenant_id}/branches/{branch_id}/batch-expiry-sessions`
- `POST /v1/tenants/{tenant_id}/branches/{branch_id}/batch-expiry-sessions/{id}/review`
- `POST /v1/tenants/{tenant_id}/branches/{branch_id}/batch-expiry-sessions/{id}/approve`
- `POST /v1/tenants/{tenant_id}/branches/{branch_id}/batch-expiry-sessions/{id}/cancel`

So this slice does not require a new backend route. It should only verify that the existing backend shape is used directly from mobile.

## Mobile Architecture

Extend the existing mobile control-plane client with:
- `getBatchExpiryReport`
- `getBatchExpiryBoard`
- `createBatchExpirySession`
- `recordBatchExpirySessionReview`
- `approveBatchExpirySession`
- `cancelBatchExpirySession`

Then add `RemoteExpiryRepository` that maps control-plane batch-expiry models into the existing Android expiry domain:
- `BatchExpiryReportResponse` -> `ExpiryReport`
- `BatchExpiryBoardResponse` -> `ExpiryBoard`
- reviewed session responses -> `ExpiryReviewSession`
- approval response -> `ExpiryReviewApproval`

The `ExpiryViewModel` and `ExpiryScreen` should remain largely unchanged. This is a repository swap, not a UI redesign.

## Runtime Wiring

`StoreMobileApp` should:
- keep using the paired runtime `branchId`
- build a remote expiry repository when session + paired device context are present
- leave restock on its current repository for now

## Failure Posture

Reviewed expiry becomes truly remote-backed for paired runtimes. If the control plane call fails:
- surface a real error in expiry state
- do not silently fall back to in-memory expiry

## Verification

Required verification:
- targeted backend test proving existing batch-expiry workflow remains green
- targeted Android tests for:
  - control-plane client expiry calls
  - remote expiry repository mapping
  - runtime context helper / repository selection
- full `apps/store-mobile` unit-test run
- `npm run ci:store-mobile`
- `git diff --check`
