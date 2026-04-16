# Store Mobile Replenishment Board Plan

Date: 2026-04-16
Spec: `docs/superpowers/specs/2026-04-16-store-mobile-replenishment-board-design.md`

1. Extend Android control-plane models and client with replenishment-board types and parsing.
2. Extend the restock repository boundary with `loadReplenishmentBoard`.
3. Map the remote replenishment board in `RemoteRestockRepository` and provide a minimal in-memory fallback.
4. Update `RestockViewModel` to hold replenishment board state and select a low-stock product into the current draft.
5. Update `RestockScreen` and `StoreMobileApp` action wiring for replenishment-board selection.
6. Run targeted Android tests, full mobile unit tests, `ci:store-mobile`, and `git diff --check`.
