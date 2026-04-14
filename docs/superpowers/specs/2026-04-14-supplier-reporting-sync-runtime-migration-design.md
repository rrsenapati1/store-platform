# Supplier Reporting And Sync Runtime Migration (CP-011E) Design

Date: 2026-04-14  
Owner: Codex  
Status: Draft for user review

## Goal

Migrate the remaining legacy operational support surfaces from the legacy retail API to the control plane, covering:

- supplier reporting
- hub-to-cloud sync runtime
- sync status and monitoring

The target architecture is hub-and-spoke per branch: one primary branch device syncs with the cloud, and branch-local spoke devices sync through that hub.

## RMS Alignment

This slice should mirror the robust posture already established in RMS:

- supplier reporting should be served from materialized snapshot tables rather than expensive live report joins
- sync runtime should use explicit transport telemetry, mutation logging, conflict tracking, and hub health status
- monitoring should expose operational posture to owner and branch staff without making every spoke a cloud client

RMS reference areas reviewed:

- `docs/RMS_CANONICAL_BLUEPRINT.md`
- `app/models/shared.py`
- `app/models/tenant.py`
- `app/modules/sync/service.py`
- `app/modules/sync/router.py`

## Non-Goals

- No attempt to introduce gRPC in this repo during this slice
- No requirement for every branch device to connect directly to the cloud
- No background worker platform rollout in the same slice
- No expansion of human-auth runtime routes into mixed machine-auth and human-auth modules
- No rewrite of existing procurement-finance or print-job modules beyond calling new reporting and sync services

## Scope

### 1. Supplier Reporting Domain

Add a dedicated `supplier_reporting` control-plane domain with modular models, repositories, services, schemas, and routes.

Routes should cover the full remaining supplier reporting surface now owned by the legacy API:

1. `GET /v1/tenants/{tenant_id}/branches/{branch_id}/supplier-payables-report`
2. `GET /v1/tenants/{tenant_id}/branches/{branch_id}/supplier-aging-report`
3. `GET /v1/tenants/{tenant_id}/branches/{branch_id}/supplier-statements`
4. `GET /v1/tenants/{tenant_id}/branches/{branch_id}/supplier-due-schedule`
5. `GET /v1/tenants/{tenant_id}/branches/{branch_id}/supplier-settlement-report`
6. `GET /v1/tenants/{tenant_id}/branches/{branch_id}/supplier-settlement-blockers`
7. `GET /v1/tenants/{tenant_id}/branches/{branch_id}/supplier-exception-report`
8. `GET /v1/tenants/{tenant_id}/branches/{branch_id}/supplier-escalation-report`
9. `GET /v1/tenants/{tenant_id}/branches/{branch_id}/supplier-performance-report`
10. `GET /v1/tenants/{tenant_id}/branches/{branch_id}/supplier-payment-activity`

### 2. Supplier Snapshot Model

Supplier reports should be served from materialized snapshot rows, not live joins over procurement tables.

Suggested storage shape:

- one shared snapshot table keyed by:
  - `tenant_id`
  - `branch_id`
  - `supplier_id`
  - `report_type`
- snapshot metadata:
  - `source_watermark`
  - `refreshed_at`
  - `is_dirty`
- JSON payload for report-specific materialized fields

Alternative if payload sprawl becomes hard to validate:

- dedicated snapshot tables per report family

Initial preference in this repo:

- shared snapshot table for simpler migration and fewer files
- typed schema serializers at the route layer

### 3. Snapshot Refresh Strategy

Because the repo does not yet include a background job runner, use a hybrid refresh model:

- procurement-finance writes mark the branch supplier-report snapshot set dirty
- report reads refresh missing or dirty snapshots inline before returning
- each refresh stamps `refreshed_at` and a deterministic `source_watermark`
- later async refresh can be introduced without changing API contracts

Dirtying events:

- purchase invoice creation
- supplier return creation
- supplier payment creation

Source tables:

- purchase invoices and lines
- supplier returns and lines
- supplier payments
- goods receipts where needed for receipt freshness or dispute timing
- suppliers for identity and payment terms

### 4. Sync Runtime Domain

Add a dedicated `sync_runtime` control-plane domain with modular models, repositories, services, schemas, and routes.

Machine transport routes:

1. `POST /v1/sync/push`
2. `GET /v1/sync/pull`
3. `GET /v1/sync/heartbeat`

These routes are for the branch hub only.

Spoke devices do not talk directly to the cloud in this model.

### 5. Sync Runtime Persistence

Add RMS-style sync primitives:

- `sync_mutation_log`
  - replay-safe, idempotent mutation ledger
- `sync_envelopes`
  - transport telemetry for push and pull activity
- `sync_conflicts`
  - open conflict tracking and conflict diagnostics
- `hub_sync_status`
  - per-branch hub health and monitoring posture

Minimum fields:

- common scope:
  - `id`
  - `tenant_id`
  - `branch_id`
  - `device_id`
  - `created_at`
  - `updated_at`
- mutation log:
  - `idempotency_key`
  - `client_version`
  - `server_version`
  - `mutation_type`
  - `payload`
  - `processed_at`
- envelopes:
  - `direction`
  - `status`
  - `cursor`
  - `last_error`
  - `payload`
- conflicts:
  - `status`
  - `reason`
  - `table_name`
  - `record_id`
  - `version`
  - `source_idempotency_key`
  - `payload`
- hub sync status:
  - `hub_device_id`
  - `last_push_at`
  - `last_pull_at`
  - `last_heartbeat_at`
  - `last_cursor`
  - `pending_mutation_count`
  - `open_conflict_count`
  - `failed_envelope_count`
  - `connected_spoke_count`
  - `oldest_unsynced_mutation_age_seconds`
  - `status`
  - `detail`

### 6. Sync Authentication

Do not reuse human bearer tokens for machine sync transport.

Use branch hub device identity plus a control-plane-issued runtime credential:

- sync payload scope must include `tenant_id`, `branch_id`, and `device_id`
- server must verify:
  - device exists
  - device is active
  - device is the current branch hub device
  - credential matches the device

This keeps human runtime routes and machine sync routes separated.

### 7. Sync Monitoring Routes

Add branch-scoped read routes for owner and branch staff:

1. `GET /v1/tenants/{tenant_id}/branches/{branch_id}/runtime/sync-status`
2. `GET /v1/tenants/{tenant_id}/branches/{branch_id}/runtime/sync-conflicts`
3. `GET /v1/tenants/{tenant_id}/branches/{branch_id}/runtime/sync-envelopes`

Route behavior:

- `sync-status`
  - one branch-level hub view
  - last push/pull/heartbeat timestamps
  - cursor or version lag
  - pending mutations
  - failed envelope count
  - open conflict count
  - connected spoke summary
- `sync-conflicts`
  - open conflicts only
  - includes conflict reason, entity reference, version mismatch data, and timestamps
- `sync-envelopes`
  - recent failed or degraded envelopes only
  - not a full transport log dump

### 8. UI Placement

Keep both applications modular by adding dedicated section components.

`owner-web`:

- `OwnerSupplierReportingSection`
  - placed near procurement finance
  - full supplier reporting visibility
- `OwnerRuntimeSyncSection`
  - placed near device/runtime foundations
  - monitoring-only

`store-desktop`:

- `StoreSupplierReportingSection`
  - read-only
- `StoreRuntimeSyncSection`
  - read-only

Do not grow:

- `useOwnerWorkspace.ts`
- `useStoreRuntimeWorkspace.ts`

Any repeated fetch or transformation logic should move into section-local helpers or client methods.

### 9. Authorization

Supplier reporting:

- owner-web:
  - `reports.view` or `purchase.manage`
- store-desktop:
  - read-only branch access for staff with `reports.view`, `sales.bill`, or `sales.return`

Sync monitoring:

- owner-web:
  - `reports.view`
- store-desktop:
  - read-only branch runtime visibility for staff with `sales.bill` or `sales.return`

Machine sync transport:

- no human capability checks
- device credential enforcement only

### 10. Authority And Cutover

Extend the authority manifest:

- mark `supplier_reporting` as migrated
- mark `sync_runtime` as migrated

Legacy API cutover behavior:

- shadow mode:
  - deprecation headers on migrated write paths
- cutover mode:
  - migrated legacy write paths return `410`

Legacy reporting and sync routes remain readable only until the control-plane replacements are wired into both app surfaces and verification closes.

### 11. Verification

Backend:

- supplier snapshot refresh and invalidation tests
- report endpoint tests for every supplier report surface
- sync push, pull, and heartbeat tests
- sync conflict creation and open-conflict listing tests
- sync status and envelope monitoring tests

Frontend:

- owner-web supplier reporting section tests
- owner-web runtime sync monitoring section tests
- store-desktop read-only supplier reporting section tests
- store-desktop read-only runtime sync monitoring section tests

Cutover:

- legacy authority cutover coverage for migrated supplier reporting and sync-runtime writes

Smoke verification:

- extend the control-plane smoke path to:
  - create supplier finance activity
  - read at least one supplier report snapshot
  - execute hub heartbeat
  - execute hub pull and push
  - validate sync-status counters

## Implementation Notes

- Prefer a new `supplier_reporting.py` service and route pair rather than extending `procurement_finance.py` into a mixed finance-plus-reporting module.
- Prefer a new `sync_runtime.py` service and route pair rather than inflating `runtime.py`, which currently owns branch human runtime flows and print-job orchestration.
- Snapshot and sync models should live in dedicated modules so file size and responsibility stay within the control-plane reset rules.
- Keep PostgreSQL as backend authority. No fallback to SQLite backend persistence is allowed in this slice.
