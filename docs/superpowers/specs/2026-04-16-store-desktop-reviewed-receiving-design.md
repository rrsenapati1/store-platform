# Store Desktop Reviewed Receiving Design

Date: 2026-04-16  
Owner: Codex  
Status: Approved for implementation

## Goal

Add a real reviewed receiving workflow to `apps/store-desktop` so branch operators can process approved purchase orders through the existing control-plane goods-receipt model instead of relying on owner-web or mobile/tablet only.

## Scope

This slice is limited to `Store Desktop` and reuses existing control-plane routes:

- `GET /v1/tenants/{tenant_id}/branches/{branch_id}/receiving-board`
- `POST /v1/tenants/{tenant_id}/branches/{branch_id}/goods-receipts`
- `GET /v1/tenants/{tenant_id}/branches/{branch_id}/goods-receipts`
- existing inventory snapshot refresh after receipt creation

Included:

- board-driven desktop receiving
- reviewed goods-receipt draft lines per selected purchase order
- discrepancy note capture per line
- receipt note capture
- latest goods receipt visibility after submission
- board and inventory refresh after receipt creation

Not included:

- purchase-order authoring or approval on desktop
- lot/batch intake UI
- receiving-session lifecycle beyond the existing reviewed goods-receipt create call
- backend schema changes

## Recommended Approach

Use a dedicated desktop receiving section with a board-driven selector.

Why:

- the control-plane receiving board already describes which approved purchase orders are ready, blocked, or already received
- owner-web and mobile/tablet already follow the reviewed receipt model
- desktop should align to that authority boundary instead of inventing an auto-open or shortcut flow

## Architecture

### Client Boundary

Extend `apps/store-desktop/src/control-plane/client.ts` with the receiving routes already used elsewhere:

- `getReceivingBoard`
- `createGoodsReceipt`
- `listGoodsReceipts`

The client remains a thin route wrapper.

### Workspace Boundary

Add reviewed-receiving state to `useStoreRuntimeWorkspace.ts`, but keep orchestration thin by extracting business-side request flow into a new `storeReceivingActions.ts`.

New workspace state should include:

- `receivingBoard`
- `goodsReceipts`
- `latestGoodsReceipt`
- `selectedReceivingPurchaseOrderId`
- `receivingLineDrafts`
- `goodsReceiptNote`

The workspace remains responsible for:

- bootstrapped tenant/branch/runtime context
- exposing receiving actions to the UI
- integrating post-receipt inventory refresh

### UI Boundary

Add a new `StoreReceivingSection.tsx`.

The section should:

- load the receiving board
- show board summary and per-PO posture
- let the operator select a ready PO from the board
- show line-level reviewed receipt inputs for the selected PO
- create a goods receipt from that reviewed draft
- show the latest goods receipt and board/inventory aftermath

### Selection Model

Desktop does not currently load purchase orders directly in the runtime workspace. For this slice, the receiving board record is the entry point and the reviewed draft is built from the selected PO’s catalog/inventory context plus the receiving payload entered by the operator.

Board-driven means:

- no hidden auto-selection of the “latest” PO
- operator can explicitly pick the PO they are receiving
- the UI remains stable even if multiple ready POs exist

## Data Flow

1. Operator loads the receiving board.
2. Desktop shows ready/blocked/received posture per approved PO.
3. Operator selects a ready PO.
4. Desktop loads or derives the reviewed line draft for that PO.
5. Operator records:
   - received quantity per line
   - discrepancy note per line
   - overall receipt note
6. Desktop posts `createGoodsReceipt`.
7. On success, desktop refreshes:
   - receiving board
   - goods-receipt list
   - inventory snapshot
8. Desktop surfaces the latest goods receipt details.

Inventory authority remains unchanged:

- no stock movement on selection or draft editing
- stock posts only when the goods receipt is created successfully

## Validation And Error Handling

Desktop should enforce the same basic constraints before posting:

- a PO must be selected
- at least one line must have a positive received quantity
- every entered quantity must be numeric and within ordered bounds
- blocked board records cannot submit a receipt

Errors remain explicit:

- no silent fallback
- no optimistic local receipt creation
- request failures surface through the existing workspace error channel

## Testing

Add three focused desktop layers of coverage:

1. `client.receiving.test.ts`
   - route and payload coverage for board, create, and list
2. `StoreRuntimeWorkspace.receiving.test.tsx`
   - end-to-end reviewed receiving flow inside the desktop workspace hook
3. `StoreReceivingSection.test.tsx`
   - board-driven selection
   - reviewed line editing
   - latest goods receipt rendering after creation

Regression expectation:

- full `@store/store-desktop` test suite still passes

## Exit Criteria

This slice is done when:

- desktop has a visible reviewed receiving section
- operators can select a ready PO from the board
- desktop can create a reviewed goods receipt through the control plane
- board, goods receipts, and inventory snapshot refresh after receipt creation
- desktop receiving behavior matches the reviewed authority model already used by owner-web and mobile/tablet
