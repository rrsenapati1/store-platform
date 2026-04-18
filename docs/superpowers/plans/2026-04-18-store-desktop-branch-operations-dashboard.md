# Store Desktop Branch Operations Dashboard Plan

Date: 2026-04-18
Owner: Codex
Spec: `docs/superpowers/specs/2026-04-18-store-desktop-branch-operations-dashboard-design.md`

## Implementation Steps

1. Add a failing store-desktop dashboard section test.
2. Create a small dashboard loader helper that fetches:
   - replenishment board
   - restock board
   - receiving board
   - stock-count board
   - batch-expiry report
3. Add `StoreBranchOperationsDashboardSection.tsx`.
4. Wire the new section into `StoreRuntimeWorkspace.tsx`.
5. Keep workspace changes narrow and avoid adding new global runtime state unless necessary.
6. Update `docs/TASK_LEDGER.md` and `docs/WORKLOG.md` to mark `V2-007` as started.
7. Run targeted store-desktop tests, then full store-desktop verification, then `git diff --check`.

## Verification

- `npm run test --workspace @store/store-desktop -- src/control-plane/StoreBranchOperationsDashboardSection.test.tsx`
- `npm run test --workspace @store/store-desktop`
- `npm run typecheck --workspace @store/store-desktop`
- `npm run build --workspace @store/store-desktop`
- `git -c core.safecrlf=false diff --check`
