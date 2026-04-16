# Reviewed Goods Receipt Design

## Goal

Land the first `V2-004` store-operations slice by replacing the current blind full-PO receipt action with a reviewed receiving workflow that lets operators confirm line-by-line received quantities and capture discrepancies before inventory is posted.

## Why This Slice

The current receiving path is still foundation-grade:

- owner-web can only post a goods receipt from the latest approved purchase order with one click
- backend receiving always receives the full approved quantity for every line
- discrepancies, shortages, and receive-time notes are not captured anywhere
- downstream batch-lot and purchase-invoice flows inherit that all-or-nothing assumption

This slice deepens receiving without yet introducing multi-stage warehouse processes or multiple receipts per purchase order.

## Scope

### Included

- reviewed receiving against an approved purchase order in owner-web
- per-line `received_quantity` entry, defaulting to the approved ordered quantity
- optional per-line discrepancy note
- optional receipt-level note
- persisted ordered-vs-received detail on goods receipt lines
- receiving-board visibility for discrepancy posture
- inventory ledger posting from actual received quantities, not always ordered quantities
- compatibility with existing batch-lot intake and purchase-invoice flows by using the posted goods-receipt quantities

### Deferred

- multiple goods receipts against the same purchase order
- explicit receiving draft records and submit/approve stages
- mobile/tablet live receiving sync
- over-receipt handling
- supplier-claim workflow for shortages/damages

## Architecture

### Backend

The existing `goods_receipts` and `goods_receipt_lines` tables stay authoritative for this slice. We extend them rather than inventing a new receiving-draft subsystem.

- `goods_receipts` gains an optional `note`
- `goods_receipt_lines` keeps `quantity` as the actual received quantity and gains:
  - `ordered_quantity`
  - `discrepancy_note`

`InventoryService.create_goods_receipt(...)` will accept reviewed line inputs, validate them against the approved purchase-order lines, and persist only the reviewed received quantities into inventory ledger entries.

Validation rules:

- purchase order must still be approved
- one goods receipt per purchase order still holds for this slice
- every purchase-order line must appear exactly once in the payload
- `received_quantity` must be `>= 0`
- `received_quantity` must be `<= ordered_quantity`
- at least one line must have a positive received quantity

### Policy Layer

`inventory_policy.py` should own the normalized reviewed-line draft builder so the service stays orchestration-focused.

That policy layer will derive:

- ordered quantity
- received quantity
- variance quantity
- whether the line is matched or has a discrepancy

### API Contract

`GoodsReceiptCreateRequest` expands from:

- `purchase_order_id`

to:

- `purchase_order_id`
- `note?`
- `lines[]`
  - `product_id`
  - `received_quantity`
  - `discrepancy_note?`

`GoodsReceiptResponse` and `GoodsReceiptRecord` expand to expose discrepancy posture:

- receipt note
- line ordered quantity
- line received quantity via existing `quantity`
- line variance quantity
- line discrepancy note
- receipt variance summary and discrepancy flag on list/read models

`ReceivingBoardRecord` expands to show whether the completed receipt matched the PO or was received with variance.

## Owner-Web UX

The current `Create goods receipt` button becomes a reviewed receiving panel for the latest approved purchase order.

The receiving section should show:

- supplier and PO number context
- one editable row per purchase-order line
- ordered quantity
- received quantity input
- optional discrepancy note input
- receipt note field
- summary totals:
  - ordered quantity
  - received quantity
  - variance quantity

The create action remains single-step, but now it is explicit and operator-reviewed.

After posting, the section should show:

- latest receipt note
- line-level received vs ordered posture
- discrepancy badge or summary

The receiving board should also surface `RECEIVED_WITH_VARIANCE` separately from a clean matched receipt.

## Error Handling

- invalid quantities return `400` with explicit validation messages
- batch-lot intake keeps enforcing that batch quantities match actual goods-receipt received quantities
- duplicate receipt attempts remain blocked
- zero-total receipt attempts are rejected

## Testing

### Backend

- reviewed partial receipt posts only received quantity into the ledger
- goods receipt list and receiving board surface discrepancy posture
- invalid reviewed quantities are rejected
- zero-total reviewed receipts are rejected
- duplicate receipt is still blocked

### Owner-Web

- receiving section renders reviewed line inputs for the approved PO
- posting a partial receipt sends reviewed line payloads
- latest receipt detail shows ordered vs received differences
- receiving board reflects `RECEIVED_WITH_VARIANCE`

## Result

This slice makes receiving a real reviewed store workflow instead of a foundation stub, while keeping the authority model simple enough to ship quickly and extend later into richer multi-receipt or mobile receiving lanes.
