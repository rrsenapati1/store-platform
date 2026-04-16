# Store Mobile Control-Plane Stock Count Design

Date: 2026-04-16

## Goal

Replace the Android runtime's in-memory reviewed stock-count workflow with the first real control-plane-backed branch-operations slice. This should prove that the paired mobile and tablet runtime can execute a real reviewed operation against the control plane without relying on `DEMO_BRANCH_ID` or local-only repository data.

## Scope

In scope for this slice:

- extend the Android runtime session and paired-device context with `tenant_id` and `branch_id`
- stop loading mobile operations against a hardcoded demo branch
- add a bounded mobile control-plane HTTP client for stock-count routes
- add a remote stock-count repository that maps control-plane snapshot, board, and session responses into the existing mobile stock-count UI contract
- switch the mobile stock-count workflow to the remote repository while keeping the current reviewed stock-count screen and view-model boundary stable

Out of scope:

- converting receiving, restock, or expiry to real control-plane APIs
- redesigning the Android auth model beyond using the existing runtime access token as bearer auth
- adding Retrofit, Ktor, or a broader networking framework
- changing the current reviewed stock-count UX shape

## Runtime Context

The current Android pairing/runtime contract only stores device and session-surface information. That forces the app to keep using `DEMO_BRANCH_ID` when loading branch operations. For the first real mobile API slice, the runtime context must become explicit:

- `StoreMobileRuntimeSession` should carry `tenantId` and `branchId`
- `StoreMobilePairedDevice` should persist `tenantId` and `branchId`
- activation redemption should populate those fields
- the fake hub client can still return demo values, but the app must stop depending on local constants for branch identity

This keeps branch execution context aligned with the paired runtime rather than with app-only assumptions.

## Mobile Client Boundary

Add a small mobile control-plane package under `apps/store-mobile/app/src/main/java/com/store/mobile/controlplane/` with a narrow responsibility:

- build authenticated HTTP requests to the control plane using `hubBaseUrl`
- send `Authorization: Bearer <accessToken>`
- expose only the endpoints required for this slice

For this slice, those endpoints are:

- `GET /v1/tenants/{tenant_id}/branches/{branch_id}/inventory-snapshot`
- `GET /v1/tenants/{tenant_id}/branches/{branch_id}/stock-count-board`
- `POST /v1/tenants/{tenant_id}/branches/{branch_id}/stock-count-sessions`
- `POST /v1/tenants/{tenant_id}/branches/{branch_id}/stock-count-sessions/{id}/record`
- `POST /v1/tenants/{tenant_id}/branches/{branch_id}/stock-count-sessions/{id}/approve`
- `POST /v1/tenants/{tenant_id}/branches/{branch_id}/stock-count-sessions/{id}/cancel`

Use standard JDK HTTP for now. The API surface is small and this avoids introducing a full Android networking stack just to prove one real remote workflow.

## Repository Design

Keep `StockCountRepository` as the app-facing domain boundary. Do not rewrite the stock-count screen around transport details.

Add `RemoteStockCountRepository` that:

- accepts a mobile control-plane client plus runtime session context
- loads countable candidates from inventory snapshot
- loads live review-session posture from stock-count board
- creates, records, approves, and cancels review sessions through the control plane
- maps control-plane payloads into the existing mobile domain types:
  - `StockCountContext`
  - `StockCountBoard`
  - `StockCountReviewSession`
  - `StockCountApproval`

`InMemoryStockCountRepository` remains available for fast local tests and previews, but once the real runtime path is selected there should be no silent fallback to in-memory data on failure.

## App Integration

`StoreMobileApp.kt` should resolve branch operations from paired runtime context instead of `DEMO_BRANCH_ID`.

For this slice:

- mobile pairing persists `tenantId` and `branchId`
- the stock-count repository becomes remote-backed
- the rest of the operations can remain local for now, but they should load branch-scoped data using the runtime branch context rather than a hardcoded constant

The stock-count view-model and screen contract should stay mostly intact so this slice remains a repository swap plus runtime-context fix, not another UI rewrite.

## Failure Posture

If control-plane stock-count calls fail:

- show the error in stock-count state
- do not fabricate local fallback data
- leave the current active screen intact so the operator can retry

This is the first real API path, so it needs honest remote-failure semantics.

## Testing

Add coverage for:

- runtime session and paired-device persistence of `tenantId` and `branchId`
- fake hub-client redemption including `tenantId` and `branchId`
- mobile control-plane client request construction and response parsing
- remote stock-count repository mapping and lifecycle behavior using a fake client
- app-level stock-count workflow tests proving the remote path loads and executes from runtime context instead of `DEMO_BRANCH_ID`

Verification should include:

- targeted Android unit tests for runtime context and remote stock-count repo/client
- full `testDebugUnitTest`
- `npm run ci:store-mobile`
