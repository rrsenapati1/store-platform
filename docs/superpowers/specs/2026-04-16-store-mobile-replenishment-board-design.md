# Store Mobile Replenishment Board Design

Date: 2026-04-16
Track: `V2-004`
Surface: `apps/store-mobile`

## Goal

Extend the existing mobile/tablet assisted-restock flow so operators can start from a real low-stock replenishment board instead of scan-first only.

## Scope

- keep the workflow inside the existing `RESTOCK` section
- add a control-plane-backed replenishment board read to the Android client
- map replenishment board records through the existing restock repository boundary
- let operators select a low-stock product from the board to seed the current restock draft
- preserve the current scan-first path as an equal entry point

## Out of Scope

- new backend model or route changes
- new top-level mobile section
- replenishment policy editing on mobile/tablet
- desktop changes in this slice

## Design

The control-plane already exposes `GET /replenishment-board`, so this slice adds a read-only replenishment board model to the Android control-plane client and threads it through `RestockRepository`.

`RestockViewModel` remains the orchestration boundary. It now loads both:

- the existing restock task board
- the replenishment board

and exposes a `selectReplenishmentProduct(productId)` path that seeds:

- product identity
- stock on hand
- reorder point
- target stock
- suggested quantity
- requested quantity

This keeps one restock draft model and avoids forking scan-first vs board-first logic.

## Verification

- targeted Android tests for:
  - control-plane replenishment-board parsing
  - remote restock repository mapping
  - restock view-model board selection
- full `testDebugUnitTest`
- `npm run ci:store-mobile`
