# Supplier Reporting And Sync Runtime Migration Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the remaining supplier reporting and hub-and-spoke sync runtime surfaces off the legacy retail API and onto the control plane, including owner-web and store-desktop read visibility plus authority cutover.

**Architecture:** Add two new bounded domains to the control plane: `supplier_reporting` and `sync_runtime`. Supplier reporting will use materialized snapshot rows backed by procurement-finance and vendor-dispute data, with dirty-on-write and inline refresh-on-read. Sync runtime will use hub-only machine transport, per-branch hub health state, conflict/envelope ledgers, and branch-scoped monitoring reads while keeping human runtime and machine sync auth paths separate.

**Tech Stack:** FastAPI, SQLAlchemy asyncio, Alembic, PostgreSQL, React 19, Vite, Vitest, Pytest

---

### Task 1: Add supplier reporting backend with snapshot refresh and vendor-dispute support

**Files:**
- Create: `services/control-plane-api/store_control_plane/models/supplier_reporting.py`
- Create: `services/control-plane-api/store_control_plane/repositories/supplier_reporting.py`
- Create: `services/control-plane-api/store_control_plane/services/supplier_reporting.py`
- Create: `services/control-plane-api/store_control_plane/schemas/supplier_reporting.py`
- Create: `services/control-plane-api/store_control_plane/routes/supplier_reporting.py`
- Modify: `services/control-plane-api/store_control_plane/models/__init__.py`
- Modify: `services/control-plane-api/store_control_plane/repositories/__init__.py`
- Modify: `services/control-plane-api/store_control_plane/services/__init__.py`
- Modify: `services/control-plane-api/store_control_plane/schemas/__init__.py`
- Modify: `services/control-plane-api/store_control_plane/routes/__init__.py`
- Modify: `services/control-plane-api/store_control_plane/main.py`
- Modify: `services/control-plane-api/store_control_plane/services/procurement_finance.py`
- Modify: `services/control-plane-api/store_control_plane/repositories/procurement_finance.py`
- Modify: `services/control-plane-api/alembic/versions/20260414_0014_supplier_reporting_sync_runtime.py`
- Test: `services/control-plane-api/tests/test_supplier_reporting_flow.py`

- [ ] **Step 1: Write the failing supplier-reporting backend flow test**

```python
def test_supplier_reporting_snapshots_cover_payables_aging_statements_disputes_and_exceptions():
    # create tenant/branch, product, supplier, PO, GRN, purchase invoice, return, payment
    # create open and resolved vendor disputes
    # hit all supplier-reporting routes
    # assert snapshot-backed totals, aging buckets, blocker counts, exception counts, performance metrics, and dispute board ordering
```

- [ ] **Step 2: Run the supplier-reporting test to verify it fails**

Run: `python -m pytest services/control-plane-api/tests/test_supplier_reporting_flow.py -q`  
Expected: FAIL with missing routes, missing models, or missing snapshot support.

- [ ] **Step 3: Implement persisted supplier-reporting support models**

```python
class VendorDispute(Base, TimestampMixin): ...
class SupplierReportSnapshot(Base, TimestampMixin): ...
```

Include:
- dispute reference fields for goods receipt or purchase invoice
- report-type keyed snapshot payloads
- branch-scoped dirty flag, source watermark, and `refreshed_at`

- [ ] **Step 4: Implement repository refresh and read helpers**

```python
async def mark_branch_supplier_snapshots_dirty(...): ...
async def upsert_snapshot(...): ...
async def list_snapshots(...): ...
async def list_vendor_disputes(...): ...
```

- [ ] **Step 5: Implement supplier-reporting service and routes**

```python
GET /v1/tenants/{tenant_id}/branches/{branch_id}/supplier-payables-report
GET /v1/tenants/{tenant_id}/branches/{branch_id}/supplier-aging-report
GET /v1/tenants/{tenant_id}/branches/{branch_id}/supplier-statements
GET /v1/tenants/{tenant_id}/branches/{branch_id}/supplier-due-schedule
GET /v1/tenants/{tenant_id}/branches/{branch_id}/supplier-settlement-report
GET /v1/tenants/{tenant_id}/branches/{branch_id}/supplier-settlement-blockers
GET /v1/tenants/{tenant_id}/branches/{branch_id}/supplier-exception-report
GET /v1/tenants/{tenant_id}/branches/{branch_id}/supplier-escalation-report
GET /v1/tenants/{tenant_id}/branches/{branch_id}/supplier-performance-report
GET /v1/tenants/{tenant_id}/branches/{branch_id}/supplier-payment-activity
POST /v1/tenants/{tenant_id}/branches/{branch_id}/vendor-disputes
POST /v1/tenants/{tenant_id}/branches/{branch_id}/vendor-disputes/{dispute_id}/resolve
GET /v1/tenants/{tenant_id}/branches/{branch_id}/vendor-dispute-board
```

- [ ] **Step 6: Dirty snapshots from procurement-finance writes**

```python
await self._supplier_reporting_repo.mark_branch_supplier_snapshots_dirty(...)
```

Call this after purchase invoice, supplier return, and supplier payment writes commit their domain data.

- [ ] **Step 7: Run the supplier-reporting test to verify it passes**

Run: `python -m pytest services/control-plane-api/tests/test_supplier_reporting_flow.py -q`  
Expected: PASS

- [ ] **Step 8: Commit (skipped: repo is not a git workspace)**

```bash
git add services/control-plane-api/store_control_plane services/control-plane-api/tests services/control-plane-api/alembic
git commit -m "feat: add control-plane supplier reporting and vendor dispute snapshots"
```

---

### Task 2: Add hub-only sync runtime backend with machine auth and monitoring

**Files:**
- Create: `services/control-plane-api/store_control_plane/models/sync_runtime.py`
- Create: `services/control-plane-api/store_control_plane/repositories/sync_runtime.py`
- Create: `services/control-plane-api/store_control_plane/services/sync_runtime.py`
- Create: `services/control-plane-api/store_control_plane/schemas/sync_runtime.py`
- Create: `services/control-plane-api/store_control_plane/routes/sync_runtime.py`
- Modify: `services/control-plane-api/store_control_plane/models/workforce.py`
- Modify: `services/control-plane-api/store_control_plane/repositories/workforce.py`
- Modify: `services/control-plane-api/store_control_plane/services/workforce.py`
- Modify: `services/control-plane-api/store_control_plane/schemas/workforce.py`
- Modify: `services/control-plane-api/store_control_plane/routes/workforce.py`
- Modify: `services/control-plane-api/store_control_plane/models/__init__.py`
- Modify: `services/control-plane-api/store_control_plane/repositories/__init__.py`
- Modify: `services/control-plane-api/store_control_plane/services/__init__.py`
- Modify: `services/control-plane-api/store_control_plane/schemas/__init__.py`
- Modify: `services/control-plane-api/store_control_plane/routes/__init__.py`
- Modify: `services/control-plane-api/store_control_plane/main.py`
- Modify: `services/control-plane-api/alembic/versions/20260414_0014_supplier_reporting_sync_runtime.py`
- Test: `services/control-plane-api/tests/test_sync_runtime_flow.py`

- [ ] **Step 1: Write the failing sync-runtime backend flow test**

```python
def test_branch_hub_sync_transport_and_monitoring_surface():
    # register branch devices, designate one hub, capture hub credential
    # push accepted mutation, push conflicting mutation, pull cursor, heartbeat with spoke summary
    # read sync-status, sync-conflicts, and sync-envelopes with human auth
    # assert hub-only auth, idempotency, lag fields, and conflict visibility
```

- [ ] **Step 2: Run the sync-runtime test to verify it fails**

Run: `python -m pytest services/control-plane-api/tests/test_sync_runtime_flow.py -q`  
Expected: FAIL with missing sync routes, missing device credential fields, or missing monitoring state.

- [ ] **Step 3: Extend device registration for hub runtime identity**

```python
class DeviceRegistration(...):
    sync_role: Mapped[str]
    runtime_secret_hash: Mapped[str | None]
    runtime_secret_last_rotated_at: Mapped[datetime | None]
```

Return the plain-text runtime credential only on create or rotate for the designated hub device.

- [ ] **Step 4: Implement sync runtime persistence**

```python
class SyncMutationLog(Base, TimestampMixin): ...
class SyncEnvelope(Base, TimestampMixin): ...
class SyncConflict(Base, TimestampMixin): ...
class HubSyncStatus(Base, TimestampMixin): ...
```

- [ ] **Step 5: Implement hub-only sync service and transport routes**

```python
POST /v1/sync/push
GET /v1/sync/pull
GET /v1/sync/heartbeat
```

Require machine headers or credentials that bind:
- `tenant_id`
- `branch_id`
- `device_id`
- device runtime credential

- [ ] **Step 6: Implement human monitoring routes**

```python
GET /v1/tenants/{tenant_id}/branches/{branch_id}/runtime/sync-status
GET /v1/tenants/{tenant_id}/branches/{branch_id}/runtime/sync-conflicts
GET /v1/tenants/{tenant_id}/branches/{branch_id}/runtime/sync-envelopes
```

- [ ] **Step 7: Run the sync-runtime test to verify it passes**

Run: `python -m pytest services/control-plane-api/tests/test_sync_runtime_flow.py -q`  
Expected: PASS

- [ ] **Step 8: Commit (skipped: repo is not a git workspace)**

```bash
git add services/control-plane-api/store_control_plane services/control-plane-api/tests services/control-plane-api/alembic
git commit -m "feat: add control-plane hub sync runtime and monitoring"
```

---

### Task 3: Add owner-web supplier reporting and sync monitoring sections

**Files:**
- Create: `apps/owner-web/src/control-plane/OwnerSupplierReportingSection.tsx`
- Create: `apps/owner-web/src/control-plane/OwnerRuntimeSyncSection.tsx`
- Create: `apps/owner-web/src/control-plane/OwnerSupplierReportingSection.test.tsx`
- Create: `apps/owner-web/src/control-plane/OwnerRuntimeSyncSection.test.tsx`
- Modify: `apps/owner-web/src/control-plane/client.ts`
- Modify: `apps/owner-web/src/control-plane/OwnerWorkspace.tsx`
- Modify: `packages/types/src/index.ts`

- [ ] **Step 1: Write failing owner-web section tests**

```tsx
test('loads supplier reporting snapshots and dispute board for a branch', async () => {
  // mock report endpoints and verify totals, records, and dispute visibility
})

test('loads runtime sync status conflicts and degraded envelopes for a branch', async () => {
  // mock monitoring endpoints and verify hub health metrics
})
```

- [ ] **Step 2: Run the owner-web tests to verify they fail**

Run: `npm run test --workspace @store/owner-web -- OwnerSupplierReportingSection.test.tsx OwnerRuntimeSyncSection.test.tsx`  
Expected: FAIL due to missing client methods or components.

- [ ] **Step 3: Implement owner-web client methods and shared types**

```ts
client.getSupplierAgingReport(...)
client.getSupplierStatements(...)
client.getSupplierExceptionReport(...)
client.createVendorDispute(...)
client.resolveVendorDispute(...)
client.getRuntimeSyncStatus(...)
client.listRuntimeSyncConflicts(...)
client.listRuntimeSyncEnvelopes(...)
```

- [ ] **Step 4: Implement dedicated owner sections**

Keep them self-contained and mount them after procurement-finance and before branch device setup.

- [ ] **Step 5: Run the owner-web tests to verify they pass**

Run: `npm run test --workspace @store/owner-web -- OwnerSupplierReportingSection.test.tsx OwnerRuntimeSyncSection.test.tsx`  
Expected: PASS

- [ ] **Step 6: Commit (skipped: repo is not a git workspace)**

```bash
git add apps/owner-web packages/types
git commit -m "feat: add owner-web supplier reporting and sync monitoring"
```

---

### Task 4: Add store-desktop read-only supplier reporting and sync monitoring sections

**Files:**
- Create: `apps/store-desktop/src/control-plane/StoreSupplierReportingSection.tsx`
- Create: `apps/store-desktop/src/control-plane/StoreRuntimeSyncSection.tsx`
- Modify: `apps/store-desktop/src/control-plane/client.ts`
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.tsx`
- Modify: `packages/types/src/index.ts`
- Test: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.supplier-sync.test.tsx`

- [ ] **Step 1: Write the failing store-desktop read-only test**

```tsx
test('loads read-only supplier reporting and sync monitoring for branch staff', async () => {
  // mock supplier reporting and sync status responses
  // verify read-only rendering with no mutation controls
})
```

- [ ] **Step 2: Run the store-desktop test to verify it fails**

Run: `npm run test --workspace @store/store-desktop -- StoreRuntimeWorkspace.supplier-sync.test.tsx`  
Expected: FAIL due to missing section components.

- [ ] **Step 3: Implement client methods and read-only sections**

Use the new supplier-reporting and runtime-monitoring client calls, but expose no vendor-dispute mutations and no machine-sync controls.

- [ ] **Step 4: Wire the sections into the runtime workspace**

Mount them near other read-only operational posture surfaces.

- [ ] **Step 5: Run the store-desktop test to verify it passes**

Run: `npm run test --workspace @store/store-desktop -- StoreRuntimeWorkspace.supplier-sync.test.tsx`  
Expected: PASS

- [ ] **Step 6: Commit (skipped: repo is not a git workspace)**

```bash
git add apps/store-desktop packages/types
git commit -m "feat: add store-desktop supplier reporting and sync monitoring"
```

---

### Task 5: Cut over authority, verifier, and documentation

**Files:**
- Modify: `services/control-plane-api/store_control_plane/services/authority.py`
- Modify: `services/api/store_api/authority.py`
- Modify: `services/api/tests/test_authority_cutover.py`
- Modify: `services/control-plane-api/store_control_plane/verification.py`
- Modify: `services/control-plane-api/tests/test_verification_smoke.py`
- Modify: `docs/TASK_LEDGER.md`
- Modify: `docs/WORKLOG.md`
- Modify: `docs/PROJECT_CONTEXT.md`
- Modify: `docs/STORE_CANONICAL_BLUEPRINT.md`
- Modify: `docs/API_CONTRACT_MATRIX.md`
- Modify: `docs/context/MODULE_MAP.md`
- Modify: `docs/superpowers/plans/2026-04-13-control-plane-domain-migration-program.md`

- [ ] **Step 1: Update authority classification and legacy cutover tests**

Move `supplier_reporting` and `sync_runtime` into the migrated domain list and block migrated legacy writes in cutover mode.

- [ ] **Step 2: Extend control-plane verification**

Add supplier finance activity, vendor disputes, supplier report reads, hub sync push/pull/heartbeat, and sync-status checks to the smoke verifier.

- [ ] **Step 3: Update docs and task ledger**

Mark CP-011E complete only after the verification stack passes and the remaining legacy operational list is empty.

- [ ] **Step 4: Run full verification**

Run: `python -m pytest services/control-plane-api/tests -q`  
Run: `python -m pytest services/api/tests/test_authority_cutover.py -q`  
Run: `npm run test`  
Run: `npm run typecheck`  
Run: `npm run build`  
Run: `python services/control-plane-api/scripts/verify_control_plane.py`

- [ ] **Step 5: Commit (skipped: repo is not a git workspace)**

```bash
git add services docs apps packages
git commit -m "feat: migrate supplier reporting and sync runtime to control plane"
```
