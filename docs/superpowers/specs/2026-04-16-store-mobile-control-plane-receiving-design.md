# Store Mobile Control-Plane Receiving Design

## Goal

Replace the Android runtime's in-memory reviewed receiving flow with a real control-plane-backed receiving workflow using the paired runtime `tenantId` and `branchId`.

## Scope

This slice is limited to reviewed receiving on Store Mobile and Inventory Tablet.

Included:
- runtime receiving branch context from paired session/device
- control-plane reads for:
  - `receiving-board`
  - purchase-order detail with lines
  - latest goods receipt list
- control-plane reviewed receipt creation
- remote Android receiving repository
- Store Mobile wiring swap for receiving only

Not included:
- restock, expiry, or stock-count changes beyond existing work
- offline fallback for remote receiving
- new mobile-specific backend contracts

## Backend Boundary

The existing control-plane inventory routes already support:
- `GET /v1/tenants/{tenant_id}/branches/{branch_id}/receiving-board`
- `POST /v1/tenants/{tenant_id}/branches/{branch_id}/goods-receipts`
- `GET /v1/tenants/{tenant_id}/branches/{branch_id}/goods-receipts`

The missing piece is approved purchase-order line detail for building the reviewed receiving draft. Instead of inventing a mobile-only route, add:

- `GET /v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order_id}`

That route should reuse the existing `PurchaseOrderResponse` schema and existing `_purchase_order_response` service helper.

## Mobile Architecture

Add a small receiving extension to the existing mobile control-plane client:
- `getReceivingBoard`
- `getPurchaseOrder`
- `listGoodsReceipts`
- `createGoodsReceipt`

Then add `RemoteReceivingRepository` that maps:
- receiving board record -> current `ReceivingBoard`
- purchase-order detail -> current `ReceivingDraft`
- latest goods receipt list + created goods receipt -> current `ReviewedGoodsReceipt`

The `ReceivingViewModel` and `ReceivingScreen` should remain largely unchanged. This is a repository swap, not another UI redesign.

## Runtime Wiring

`StoreMobileApp` should:
- keep using paired runtime `branchId`
- build a remote receiving repository when session + paired device context are present
- leave restock and expiry on their current repositories for now

## Failure Posture

Reviewed receiving becomes truly remote-backed for paired runtimes. If the control plane call fails:
- surface a real error in receiving state
- do not silently fall back to in-memory receiving

## Verification

Required verification:
- targeted backend tests for purchase-order detail route
- targeted Android tests for:
  - control-plane client receiving calls
  - remote receiving repository mapping
  - runtime context helper / repository selection
- full `apps/store-mobile` unit-test run
- `npm run ci:store-mobile`
- `git diff --check`
