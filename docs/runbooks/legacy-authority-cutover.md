# Legacy Authority Cutover Runbook

Updated: 2026-04-14

## Purpose

This runbook defines the point where `services/api/store_api/` stops being authoritative for the domains that have already migrated to the control plane.

## Cutover Contract

Control-plane authority is published at:

- `GET /v1/system/authority-boundary`

Current migrated domains:

- `onboarding`
- `workforce`
- `catalog`
- `barcode_foundation`
- `purchasing`
- `inventory`
- `batch_tracking`
- `billing`
- `compliance_exports`
- `customer_reporting`
- `supplier_reporting`
- `runtime_print`
- `sync_runtime`

Current legacy-only domains:

- none

## Legacy Modes

The legacy retail API supports two write modes:

1. `shadow`
   - migrated-domain writes still execute
   - responses carry:
     - `X-Store-Legacy-Authority-Status: deprecated`
     - `X-Store-Legacy-Domain`
     - `X-Store-Authority-Owner: control-plane`
2. `cutover`
   - migrated-domain writes return `410`
   - the same authority headers are returned with `X-Store-Legacy-Authority-Status: cutover`
   - legacy reads may remain temporarily during operator cutover validation, but no legacy-only operational domains remain

## Preconditions

1. The control-plane verifier passes on Postgres.
2. Platform-admin, owner-web, and store-desktop are using the control-plane routes for the migrated domains.
3. The authority manifest reports an empty legacy-only domain list.

## Enable Cutover

Set the legacy retail API write mode:

```powershell
$env:STORE_LEGACY_WRITE_MODE = "cutover"
```

Restart the legacy retail API after changing the environment.

## Expected Behavior After Cutover

- `POST /v1/platform/tenants` on the legacy API returns `410`
- other migrated legacy write routes return `410`
- responses include authority headers pointing operators to the control-plane ownership boundary
- no legacy-only operational domains remain on the legacy API

## Shutdown Sequence

1. Enable `cutover` mode on the legacy retail API.
2. Verify migrated legacy writes fail with authority headers.
3. Remove residual read traffic from the legacy API after operator validation.
4. Retire the legacy retail API after the final residual read dependencies are replaced.
