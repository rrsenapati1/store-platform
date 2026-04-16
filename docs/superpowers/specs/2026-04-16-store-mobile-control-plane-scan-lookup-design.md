# Store Mobile Control-Plane Scan Lookup Design

## Goal

Replace the Android runtime's in-memory barcode scan lookup with a real control-plane-backed branch scan lookup that also carries replenishment policy needed by the mobile restock workflow.

## Scope

This slice is limited to barcode scan lookup on Store Mobile and Inventory Tablet.

Included:
- enrich the control-plane branch barcode scan response with:
  - `reorder_point`
  - `target_stock`
- remote Android scan lookup repository
- Store Mobile wiring swap for scan lookup only

Not included:
- changes to stock-count, receiving, expiry, or restock beyond repository dependencies
- scan UI redesign
- offline fallback for paired remote scan lookup

## Backend Boundary

The control plane already exposes:
- `GET /v1/tenants/{tenant_id}/branches/{branch_id}/catalog-scan/{barcode}`

This slice should extend that existing response model rather than introduce a second scan-enrichment route.

`BarcodeScanLookupResponse` should return:
- `product_id`
- `product_name`
- `sku_code`
- `barcode`
- `selling_price`
- `stock_on_hand`
- `availability_status`
- `reorder_point`
- `target_stock`

The backend service should source `reorder_point` and `target_stock` from the branch catalog item so the branch scan endpoint remains the single read model for "what does this barcode mean here right now?"

## Mobile Architecture

Keep the existing Android scan domain contract:
- `ScanLookupRepository`
- `ScanLookupRecord`

Add `RemoteScanLookupRepository` under the mobile scan package. It should:
- call the control-plane `catalog-scan` endpoint using runtime `tenantId`, `branchId`, and `accessToken`
- map enriched control-plane scan responses into `ScanLookupRecord`
- preserve `reorderPoint` and `targetStock` so `ScanLookupViewModel` and the restock flow continue to work without UI contract churn

The `ScanLookupViewModel` and scan screen should remain largely unchanged. This is a repository swap, not a scan UX rewrite.

## Runtime Wiring

`StoreMobileApp` should:
- build a remote scan lookup repository when session + paired device context are present
- keep in-memory scan lookup only for unpaired/demo mode
- stop relying on fake scan data for paired mobile/tablet flows

## Failure Posture

Scan lookup becomes truly remote-backed for paired runtimes. If the control plane call fails:
- surface a real lookup error
- do not silently fall back to in-memory scan data

Not found remains a valid branch outcome and should keep using the existing "no catalog match found" posture.

## Verification

Required verification:
- targeted backend barcode tests proving enriched scan lookup remains correct
- targeted Android tests for:
  - control-plane client scan mapping
  - remote scan lookup repository mapping
  - runtime context helper / repository selection
  - existing scan lookup view-model behavior
- full `apps/store-mobile` unit-test run
- `npm run ci:store-mobile`
- `git diff --check`
