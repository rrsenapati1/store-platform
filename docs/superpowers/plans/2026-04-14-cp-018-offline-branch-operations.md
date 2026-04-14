# Offline Branch Operations (CP-018) Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land bounded offline sale checkout on the approved branch hub, with durable local continuity storage, explicit replay into the control plane, and visible reconciliation or conflict posture.

**Architecture:** Implement `CP-018` as a first-class branch-hub continuity slice, not as an extension of the existing cache-only runtime store. The desktop runtime gets a dedicated continuity store and an extracted offline-continuity hook, while the control plane gets a sync-authenticated offline-sale replay endpoint that is idempotent and records conflicts explicitly through the existing sync envelope and sync conflict infrastructure.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, React 19, Vitest, Tauri 2, Rust, `rusqlite`, browser-storage fallback, existing control-plane billing and sync-runtime services.

---

## File Structure

### Existing files to modify

- `packages/types/src/index.ts`
  - add shared offline continuity and replay result contracts
- `services/control-plane-api/store_control_plane/routes/sync_runtime.py`
  - add sync-authenticated offline sale replay route
- `services/control-plane-api/store_control_plane/schemas/sync_runtime.py`
  - add offline sale replay request and response schemas
- `services/control-plane-api/store_control_plane/services/sync_runtime.py`
  - keep branch sync monitoring aware of replayed offline sales and conflict posture when needed
- `services/control-plane-api/store_control_plane/services/billing.py`
  - extract reusable sale-persistence path so online and offline replay do not diverge
- `services/control-plane-api/store_control_plane/repositories/billing.py`
  - support explicit invoice number and issued-on persistence for replayed offline sales
- `apps/store-desktop/src/control-plane/client.ts`
  - add control-plane replay client method for offline sales
- `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.tsx`
  - keep orchestration only; render dedicated offline continuity section
- `apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts`
  - `mixed-responsibility`, 1198 lines, `>800` threshold from `@large-file-governance`
  - compose extracted offline continuity hook instead of adding more inline authority logic
- `apps/store-desktop/src/runtime-cache/storeRuntimeCacheContract.ts`
  - keep cache-only authority boundary explicit while allowing seeding into the continuity store
- `apps/store-desktop/src-tauri/Cargo.toml`
  - include any additional native persistence dependencies only if needed beyond current `rusqlite`
- `apps/store-desktop/src-tauri/src/lib.rs`
  - register new continuity commands
- `docs/TASK_LEDGER.md`
  - mark `CP-018` done only after verification passes

### New files to create

- `services/control-plane-api/store_control_plane/services/offline_continuity.py`
  - focused backend authority for offline-sale replay, duplicate detection, and conflict recording
- `services/control-plane-api/tests/test_offline_sale_replay_flow.py`
  - backend regression suite for accepted replay, duplicate replay, and conflict outcomes
- `apps/store-desktop/src/control-plane/storeRuntimeContinuityStore.ts`
  - dedicated continuity-store adapter with browser fallback and native invoke support
- `apps/store-desktop/src/control-plane/storeRuntimeContinuityPolicy.ts`
  - offline sale draft builder, invoice continuity numbering, and readiness checks
- `apps/store-desktop/src/control-plane/useStoreRuntimeOfflineContinuity.ts`
  - extracted hook for offline continuity mode, local sale creation, and replay orchestration
- `apps/store-desktop/src/control-plane/StoreOfflineContinuitySection.tsx`
  - UI for continuity banner, offline sale list, replay trigger, and conflict posture
- `apps/store-desktop/src/control-plane/storeRuntimeContinuityStore.test.ts`
  - adapter contract tests
- `apps/store-desktop/src/control-plane/storeRuntimeContinuityPolicy.test.ts`
  - local draft, stock decrement, and invoice numbering tests
- `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.offline-continuity.test.tsx`
  - integration tests for offline sale creation and replay posture
- `apps/store-desktop/src-tauri/src/runtime_continuity.rs`
  - dedicated native SQLite continuity store

### Notes

- Do **not** reuse `storeRuntimeCache` for authoritative offline sales.
- Do **not** add offline sale authority directly into `useStoreRuntimeWorkspace.ts`; extract it.
- Do **not** add offline returns or exchanges in this plan.
- Do **not** add a generic replay route; keep replay to offline sales only.
- Prefer reusing the existing billing draft and persistence rules instead of inventing a second sale model.

### Task 1: Add Continuity Contracts And Dedicated Local Store

**Files:**
- Create: `apps/store-desktop/src/control-plane/storeRuntimeContinuityStore.ts`
- Create: `apps/store-desktop/src/control-plane/storeRuntimeContinuityStore.test.ts`
- Create: `apps/store-desktop/src-tauri/src/runtime_continuity.rs`
- Modify: `apps/store-desktop/src-tauri/src/lib.rs`
- Modify: `apps/store-desktop/src-tauri/Cargo.toml`
- Modify: `packages/types/src/index.ts`

- [ ] **Step 1: Write the failing continuity-store adapter tests**

```ts
expect(saved.authority).toBe('BRANCH_HUB_CONTINUITY');
expect(loaded?.offline_sales).toHaveLength(1);
expect(loaded?.next_continuity_invoice_sequence).toBe(2);
```

- [ ] **Step 2: Run the targeted continuity-store tests and confirm they fail**

Run: `npm run test --workspace @store/store-desktop -- storeRuntimeContinuityStore.test.ts`
Expected: FAIL because the continuity store module does not exist.

- [ ] **Step 3: Add dedicated continuity contracts**

```ts
export interface StoreRuntimeOfflineSaleRecord {
  continuity_sale_id: string;
  continuity_invoice_number: string;
  reconciliation_state: 'PENDING_REPLAY' | 'REPLAYING' | 'RECONCILED' | 'CONFLICT' | 'REJECTED';
}
```

- [ ] **Step 4: Add a dedicated continuity adapter with browser fallback**

```ts
export interface StoreRuntimeContinuitySnapshot {
  schema_version: 1;
  authority: 'BRANCH_HUB_CONTINUITY';
  next_continuity_invoice_sequence: number;
  inventory_snapshot: ControlPlaneInventorySnapshotRecord[];
  offline_sales: StoreRuntimeOfflineSaleRecord[];
}
```

- [ ] **Step 5: Add native SQLite continuity persistence**

```rust
CREATE TABLE IF NOT EXISTS continuity_entries (
  continuity_key TEXT PRIMARY KEY,
  snapshot_json TEXT NOT NULL,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

- [ ] **Step 6: Re-run the continuity-store tests and native focused tests**

Run: `npm run test --workspace @store/store-desktop -- storeRuntimeContinuityStore.test.ts`
Expected: PASS

Run: `cargo test --manifest-path apps/store-desktop/src-tauri/Cargo.toml --lib runtime_continuity`
Expected: PASS

- [ ] **Step 7: Commit the continuity-store slice**

```bash
git add packages/types/src/index.ts apps/store-desktop/src/control-plane/storeRuntimeContinuityStore.ts apps/store-desktop/src/control-plane/storeRuntimeContinuityStore.test.ts apps/store-desktop/src-tauri/src/runtime_continuity.rs apps/store-desktop/src-tauri/src/lib.rs apps/store-desktop/src-tauri/Cargo.toml
git commit -m "feat: add offline continuity store"
```

### Task 2: Add Local Offline Sale Drafting And Readiness Policy

**Files:**
- Create: `apps/store-desktop/src/control-plane/storeRuntimeContinuityPolicy.ts`
- Create: `apps/store-desktop/src/control-plane/storeRuntimeContinuityPolicy.test.ts`
- Modify: `packages/types/src/index.ts`

- [ ] **Step 1: Write the failing offline-sale policy tests**

```ts
expect(result.continuityInvoiceNumber).toBe('OFF-BLRFLAGSHIP-0001');
expect(result.updatedInventory[0]?.stock_on_hand).toBe(20);
expect(result.sale.grand_total).toBe(388.5);
```

- [ ] **Step 2: Run the targeted policy tests and confirm they fail**

Run: `npm run test --workspace @store/store-desktop -- storeRuntimeContinuityPolicy.test.ts`
Expected: FAIL because the policy module does not exist.

- [ ] **Step 3: Add readiness checks and draft builder**

```ts
export function isOfflineSaleContinuityReady(args: {...}) {
  return args.runtimeProfile === 'branch_hub' && args.inventorySnapshot.length > 0;
}
```

- [ ] **Step 4: Add continuity invoice numbering and local stock decrement**

```ts
export function reserveContinuityInvoiceNumber(branchCode: string, sequence: number) {
  return `OFF-${branchCode.toUpperCase()}-${String(sequence).padStart(4, '0')}`;
}
```

- [ ] **Step 5: Re-run the targeted policy tests**

Run: `npm run test --workspace @store/store-desktop -- storeRuntimeContinuityPolicy.test.ts`
Expected: PASS

- [ ] **Step 6: Commit the offline-sale policy slice**

```bash
git add apps/store-desktop/src/control-plane/storeRuntimeContinuityPolicy.ts apps/store-desktop/src/control-plane/storeRuntimeContinuityPolicy.test.ts packages/types/src/index.ts
git commit -m "feat: add offline sale continuity policy"
```

### Task 3: Add Sync-Authenticated Offline Sale Replay Authority

**Files:**
- Create: `services/control-plane-api/store_control_plane/services/offline_continuity.py`
- Create: `services/control-plane-api/tests/test_offline_sale_replay_flow.py`
- Modify: `services/control-plane-api/store_control_plane/routes/sync_runtime.py`
- Modify: `services/control-plane-api/store_control_plane/schemas/sync_runtime.py`
- Modify: `services/control-plane-api/store_control_plane/services/billing.py`
- Modify: `services/control-plane-api/store_control_plane/repositories/billing.py`
- Modify: `packages/types/src/index.ts`

- [ ] **Step 1: Write the failing backend replay tests**

```python
accepted = client.post("/v1/sync/offline-sales/replay", headers=device_headers, json=payload)
assert accepted.status_code == 200
assert accepted.json()["result"] == "accepted"

duplicate = client.post("/v1/sync/offline-sales/replay", headers=device_headers, json=payload)
assert duplicate.status_code == 200
assert duplicate.json()["duplicate"] is True
```

- [ ] **Step 2: Extend the failing tests with a conflict path**

```python
assert conflict.json()["result"] == "conflict_review_required"
assert conflict.json()["conflict_id"]
```

- [ ] **Step 3: Run the backend replay tests and confirm they fail**

Run: `python -m pytest services/control-plane-api/tests/test_offline_sale_replay_flow.py -q`
Expected: FAIL because the replay route and service do not exist.

- [ ] **Step 4: Extract a reusable billing persistence path**

```python
async def persist_sale_bundle(..., *, invoice_number: str, issued_on, replay_metadata: dict | None = None):
    ...
```

- [ ] **Step 5: Add a focused offline continuity service**

```python
class OfflineContinuityService:
    async def replay_offline_sale(self, *, device, payload): ...
```

- [ ] **Step 6: Keep replay idempotent through the existing sync envelope contract**

```python
existing = await self._sync_repo.get_sync_envelope(...)
if existing is not None:
    return {"duplicate": True, **existing.response_payload}
```

- [ ] **Step 7: Record replay conflicts explicitly**

```python
await self._sync_repo.create_sync_conflict(
    table_name="offline_sales",
    record_id=payload["continuity_sale_id"],
    reason="STOCK_DIVERGENCE",
)
```

- [ ] **Step 8: Re-run the backend replay tests**

Run: `python -m pytest services/control-plane-api/tests/test_offline_sale_replay_flow.py -q`
Expected: PASS

- [ ] **Step 9: Commit the backend replay slice**

```bash
git add services/control-plane-api/store_control_plane/services/offline_continuity.py services/control-plane-api/tests/test_offline_sale_replay_flow.py services/control-plane-api/store_control_plane/routes/sync_runtime.py services/control-plane-api/store_control_plane/schemas/sync_runtime.py services/control-plane-api/store_control_plane/services/billing.py services/control-plane-api/store_control_plane/repositories/billing.py packages/types/src/index.ts
git commit -m "feat: add offline sale replay authority"
```

### Task 4: Extract Desktop Offline Continuity Hook And UI

**Files:**
- Create: `apps/store-desktop/src/control-plane/useStoreRuntimeOfflineContinuity.ts`
- Create: `apps/store-desktop/src/control-plane/StoreOfflineContinuitySection.tsx`
- Create: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.offline-continuity.test.tsx`
- Modify: `apps/store-desktop/src/control-plane/client.ts`
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.tsx`
- Modify: `apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts`
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.billing.test.tsx`

- [ ] **Step 1: Write the failing desktop continuity integration tests**

```ts
expect(await screen.findByText('Cloud unavailable. Branch continuity mode is active.')).toBeInTheDocument();
expect(screen.getByText('OFF-BLRFLAGSHIP-0001')).toBeInTheDocument();
expect(screen.getByText(/Pending reconciliation/)).toBeInTheDocument();
```

- [ ] **Step 2: Run the targeted desktop continuity tests and confirm they fail**

Run: `npm run test --workspace @store/store-desktop -- StoreRuntimeWorkspace.offline-continuity.test.tsx StoreRuntimeWorkspace.billing.test.tsx`
Expected: FAIL because there is no offline continuity hook or UI.

- [ ] **Step 3: Extract offline continuity orchestration out of `useStoreRuntimeWorkspace.ts`**

```ts
const offlineContinuity = useStoreRuntimeOfflineContinuity({
  runtimeShellStatus,
  localAuthRecord,
  inventorySnapshot,
  branchCatalogItems,
});
```

- [ ] **Step 4: Add offline sale creation and local replay orchestration**

```ts
await offlineContinuity.createOfflineSale({...});
await offlineContinuity.replayOfflineSales({...});
```

- [ ] **Step 5: Add dedicated UI for continuity banner, pending sales, and conflict posture**

```tsx
<SectionCard eyebrow="Offline continuity" title={`Pending offline sales: ${offlineSaleCount}`}>
```

- [ ] **Step 6: Re-run the targeted desktop continuity tests**

Run: `npm run test --workspace @store/store-desktop -- StoreRuntimeWorkspace.offline-continuity.test.tsx StoreRuntimeWorkspace.billing.test.tsx`
Expected: PASS

- [ ] **Step 7: Commit the desktop continuity slice**

```bash
git add apps/store-desktop/src/control-plane/useStoreRuntimeOfflineContinuity.ts apps/store-desktop/src/control-plane/StoreOfflineContinuitySection.tsx apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.offline-continuity.test.tsx apps/store-desktop/src/control-plane/client.ts apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.tsx apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.billing.test.tsx
git commit -m "feat: add offline sale continuity flow"
```

### Task 5: Run Full Verification And Close `CP-018`

**Files:**
- Modify: `docs/TASK_LEDGER.md`

- [ ] **Step 1: Mark the ledger done only after all verification passes**

```md
| CP-018 | P0 | Done | Public release | Offline branch operations | ... |
```

- [ ] **Step 2: Run the backend verification set**

Run: `python -m pytest services/control-plane-api/tests/test_store_desktop_activation_flow.py services/control-plane-api/tests/test_sync_runtime_flow.py services/control-plane-api/tests/test_spoke_runtime_flow.py services/control-plane-api/tests/test_offline_sale_replay_flow.py -q`
Expected: PASS

- [ ] **Step 3: Run the desktop verification set**

Run: `npm run test --workspace @store/store-desktop`
Expected: PASS

- [ ] **Step 4: Run desktop typecheck and build**

Run: `npm run typecheck --workspace @store/store-desktop`
Expected: PASS

Run: `npm run build --workspace @store/store-desktop`
Expected: PASS

- [ ] **Step 5: Run the native verification set**

Run: `cargo test --manifest-path apps/store-desktop/src-tauri/Cargo.toml --lib`
Expected: PASS

- [ ] **Step 6: Commit the closure**

```bash
git add docs/TASK_LEDGER.md
git commit -m "chore: close CP-018 offline branch operations"
```

## Manual Review Checklist

- the continuity store is separate from the cache-only runtime store
- offline authority is limited to approved branch hubs
- `useStoreRuntimeWorkspace.ts` only composes the extracted continuity hook
- offline sale replay is idempotent and not a generic sync mutation proxy
- stock divergence becomes an explicit conflict instead of a silent correction
- continuity invoice numbering stays explicit and branch-local
- browser fallback remains test-only posture while packaged runtime uses native SQLite

## Verification Summary

- Backend: `python -m pytest services/control-plane-api/tests/test_store_desktop_activation_flow.py services/control-plane-api/tests/test_sync_runtime_flow.py services/control-plane-api/tests/test_spoke_runtime_flow.py services/control-plane-api/tests/test_offline_sale_replay_flow.py -q`
- Desktop: `npm run test --workspace @store/store-desktop`
- Desktop type safety: `npm run typecheck --workspace @store/store-desktop`
- Desktop build: `npm run build --workspace @store/store-desktop`
- Native: `cargo test --manifest-path apps/store-desktop/src-tauri/Cargo.toml --lib`
