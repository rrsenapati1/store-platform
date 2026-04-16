# Branch Replenishment Policy Design

## Goal

Add the first replenishment slice to `V2-004` by letting branch operators define simple per-item replenishment policy and view a low-stock suggestion board from the control plane and owner-web.

## Why This Slice

The current inventory depth covers reviewed receiving, reviewed stock counts, and reviewed expiry disposition, but branch replenishment is still implicit:

- branch catalog items do not store reorder policy
- owner-web has no low-stock suggestion surface
- operators must infer replenishment needs from raw stock and memory
- reviewed inventory workflows do not yet feed into a branch-facing reorder board

This slice fixes that without widening into purchase-order automation, supplier selection, or advanced forecasting.

## Scope

### Included

- per-branch catalog replenishment policy fields:
  - `reorder_point`
  - `target_stock`
- control-plane replenishment board for one branch
- low-stock vs adequate replenishment status
- suggested reorder quantity derived from current stock and branch policy
- owner-web workflow to:
  - set replenishment policy on the first assigned branch item
  - refresh and review replenishment board output

### Explicitly Deferred

- automatic purchase-order generation
- supplier-aware replenishment recommendations
- lead-time forecasting
- multi-branch replenishment planning
- mobile/tablet replenishment execution
- analytics-grade replenishment dashboards

## Architecture

### Backend

Do not create a separate replenishment-policy table for this first slice. The policy belongs to the branch catalog item because it is branch-specific product configuration.

Extend `branch_catalog_items` with:

- `reorder_point`
- `target_stock`

Validation rules:

- both values must be provided together or both omitted
- `reorder_point >= 0`
- `target_stock > 0`
- `target_stock >= reorder_point`

The replenishment board can be derived from existing read models:

1. branch catalog items
2. current inventory snapshot
3. branch catalog product metadata

Only `ACTIVE` branch catalog items with a complete replenishment policy participate in the board.

### Policy Layer

`inventory_policy.py` should own the replenishment-board derivation so service code stays orchestration-focused.

For each eligible branch item:

- `stock_on_hand` comes from the branch inventory snapshot
- `LOW_STOCK` if `stock_on_hand < reorder_point`
- `ADEQUATE` otherwise
- `suggested_reorder_quantity = target_stock - stock_on_hand` only for `LOW_STOCK`

The board should sort `LOW_STOCK` items first so the operator sees urgent items immediately.

### API Shape

Expand branch catalog upsert/read contracts with:

- `reorder_point`
- `target_stock`

Add a new read route:

- `GET /v1/tenants/{tenant_id}/branches/{branch_id}/replenishment-board`

Response shape:

- branch id
- low stock count
- adequate count
- records[]
  - product id
  - product name
  - SKU code
  - availability status
  - stock on hand
  - reorder point
  - target stock
  - suggested reorder quantity
  - replenishment status

## Owner-Web UX

Keep the first slice small and branch-owner oriented.

Add one replenishment section with two responsibilities:

1. policy editing
- enter reorder point
- enter target stock
- apply those values to the first assigned branch catalog item

2. replenishment visibility
- refresh the board
- show latest saved policy
- show branch suggestions with status badges and reorder quantity

This is intentionally lightweight. It gives branch operators immediate low-stock visibility without forcing a full procurement workflow in the same slice.

## Error Handling

The backend must reject:

- only one replenishment value provided
- target stock smaller than reorder point
- negative reorder point
- zero or negative target stock

Owner-web should keep surfacing existing control-plane error messages instead of inventing a second validation language.

## Testing

### Backend

- policy helper tests for low-stock and adequate suggestion derivation
- flow test proving:
  - branch catalog item can persist replenishment policy
  - replenishment board reflects current stock
  - suggested reorder quantity is correct

### Owner-Web

- workflow test proving:
  - operator can set branch replenishment policy
  - latest policy reflects saved values
  - replenishment board renders `LOW_STOCK` suggestion output

## Success Criteria

This slice is done when:

- replenishment policy is persisted per branch catalog item
- the control plane exposes a branch replenishment board
- owner-web can set policy and render low-stock suggestions
- focused backend and owner-web verification are green
