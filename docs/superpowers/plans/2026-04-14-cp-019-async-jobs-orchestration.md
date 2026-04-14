# Async Jobs And Orchestration (CP-019) Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Postgres-backed operations queue, worker loop, and first async job types for GST export preparation, supplier-report snapshot refresh, and maintenance.

**Architecture:** Add one new backend domain for operations jobs rather than scattering background logic through compliance and supplier reporting. Existing domain tables remain authoritative; queue jobs only orchestrate when expensive or retryable work runs. Supplier-report reads keep first-snapshot compatibility, but dirty refreshes move behind the queue and worker lease model.

**Tech Stack:** FastAPI, SQLAlchemy async ORM, Alembic, Pydantic, pytest, existing owner-web React surfaces, existing control-plane settings and repositories.

---

## File Structure

### Existing files to modify

- `services/control-plane-api/store_control_plane/config/settings.py`
  - add worker and queue tuning settings
- `services/control-plane-api/store_control_plane/main.py`
  - expose session factory cleanly for worker entrypoints
- `services/control-plane-api/store_control_plane/models/__init__.py`
  - export operations job model
- `services/control-plane-api/store_control_plane/repositories/__init__.py`
  - export operations repository
- `services/control-plane-api/store_control_plane/services/__init__.py`
  - export operations queue and worker services
- `services/control-plane-api/store_control_plane/routes/compliance.py`
  - return queued GST export posture instead of inline creation
- `services/control-plane-api/store_control_plane/routes/supplier_reporting.py`
  - surface stale-refresh metadata and new queue behavior
- `services/control-plane-api/store_control_plane/routes/system.py`
  - optionally expose a minimal worker or queue status route if needed
- `services/control-plane-api/store_control_plane/repositories/compliance.py`
  - support queued export-job creation and status transitions
- `services/control-plane-api/store_control_plane/repositories/supplier_reporting.py`
  - support snapshot read metadata and dirty refresh helpers
- `services/control-plane-api/store_control_plane/services/compliance.py`
  - enqueue GST export preparation work
- `services/control-plane-api/store_control_plane/services/supplier_reporting.py`
  - enqueue snapshot refresh work and return stale metadata
- `services/control-plane-api/store_control_plane/schemas/compliance.py`
  - add queued export status compatibility
- `services/control-plane-api/store_control_plane/schemas/supplier_reporting.py`
  - add additive snapshot refresh metadata
- `services/control-plane-api/store_control_plane/routes/__init__.py`
  - include operations router
- `services/control-plane-api/store_control_plane/schemas/__init__.py`
  - export operations schemas
- `services/control-plane-api/requirements.txt`
  - keep dependency footprint minimal; no Redis
- `services/control-plane-api/README.md`
  - document worker start command
- `docs/TASK_LEDGER.md`
  - mark `CP-019` done only after verification passes
- `apps/owner-web/src/control-plane/client.ts`
  - adapt compliance and supplier-report clients to new metadata if required
- `apps/owner-web/src/control-plane/OwnerComplianceSection.tsx`
  - show queued export posture
- `apps/owner-web/src/control-plane/OwnerSupplierReportingSection.tsx`
  - show stale-refresh posture
- `packages/types/src/index.ts`
  - add shared operations job and snapshot metadata contracts

### New files to create

- `services/control-plane-api/store_control_plane/models/operations.py`
  - `OperationsJob` ORM model
- `services/control-plane-api/store_control_plane/repositories/operations.py`
  - enqueue, lease, complete, retry, dead-letter, retention helpers
- `services/control-plane-api/store_control_plane/services/operations_queue.py`
  - producer-facing queue service
- `services/control-plane-api/store_control_plane/services/operations_worker.py`
  - handler dispatch and polling-loop worker
- `services/control-plane-api/store_control_plane/routes/operations.py`
  - branch-scoped job visibility and retry routes
- `services/control-plane-api/store_control_plane/schemas/operations.py`
  - Pydantic job response models
- `services/control-plane-api/store_control_plane/services/gst_export_jobs.py`
  - focused GST export preparation handler
- `services/control-plane-api/store_control_plane/services/supplier_report_jobs.py`
  - focused supplier snapshot refresh and maintenance helpers
- `services/control-plane-api/tests/test_operations_queue.py`
  - queue repository and worker regression tests
- `services/control-plane-api/tests/test_compliance_async_jobs.py`
  - GST export queue integration tests
- `services/control-plane-api/tests/test_supplier_reporting_async_jobs.py`
  - supplier snapshot async refresh integration tests
- `services/control-plane-api/scripts/run_operations_worker.py`
  - local worker entrypoint
- `services/control-plane-api/alembic/versions/20260414_0020_operations_jobs.py`
  - operations queue migration

### Notes

- Do **not** introduce Redis or Celery in this plan.
- Do **not** build a generic workflow engine.
- Do **not** move IRN attachment itself behind the queue in this phase.
- Do **not** break existing report payloads; add metadata fields instead.
- Keep supplier-report first-snapshot seeding compatible for now; only dirty refreshes must be async.

### Task 1: Add Operations Job Persistence And Queue Service

**Files:**
- Create: `services/control-plane-api/store_control_plane/models/operations.py`
- Create: `services/control-plane-api/store_control_plane/repositories/operations.py`
- Create: `services/control-plane-api/store_control_plane/services/operations_queue.py`
- Create: `services/control-plane-api/tests/test_operations_queue.py`
- Create: `services/control-plane-api/alembic/versions/20260414_0020_operations_jobs.py`
- Modify: `services/control-plane-api/store_control_plane/models/__init__.py`
- Modify: `services/control-plane-api/store_control_plane/repositories/__init__.py`
- Modify: `services/control-plane-api/store_control_plane/services/__init__.py`

- [ ] **Step 1: Write failing queue tests for enqueue dedupe, leasing, retry, and dead-letter**

```python
assert first_job["id"] == second_job["id"]
assert leased[0]["status"] == "RUNNING"
assert retried["status"] == "RETRYABLE"
assert dead_lettered["status"] == "DEAD_LETTER"
```

- [ ] **Step 2: Run the targeted queue tests and confirm they fail**

Run: `python -m pytest services/control-plane-api/tests/test_operations_queue.py -q`
Expected: FAIL because the operations queue model and services do not exist.

- [ ] **Step 3: Add the `OperationsJob` model and Alembic migration**

```python
class OperationsJob(Base, TimestampMixin):
    __tablename__ = "operations_jobs"
```

- [ ] **Step 4: Add repository helpers for enqueue, lease, success, retry, and dead-letter**

```python
async def enqueue_job(..., queue_key: str, payload: dict[str, object]) -> OperationsJob: ...
async def lease_due_jobs(..., now: datetime, limit: int) -> list[OperationsJob]: ...
```

- [ ] **Step 5: Add a producer-facing queue service**

```python
class OperationsQueueService:
    async def enqueue_branch_job(...): ...
```

- [ ] **Step 6: Re-run the targeted queue tests**

Run: `python -m pytest services/control-plane-api/tests/test_operations_queue.py -q`
Expected: PASS

- [ ] **Step 7: Commit the queue foundation**

```bash
git add services/control-plane-api/store_control_plane/models/operations.py services/control-plane-api/store_control_plane/repositories/operations.py services/control-plane-api/store_control_plane/services/operations_queue.py services/control-plane-api/tests/test_operations_queue.py services/control-plane-api/alembic/versions/20260414_0020_operations_jobs.py services/control-plane-api/store_control_plane/models/__init__.py services/control-plane-api/store_control_plane/repositories/__init__.py services/control-plane-api/store_control_plane/services/__init__.py
git commit -m "feat: add operations job queue foundation"
```

### Task 2: Add Worker Dispatch And GST Export Async Preparation

**Files:**
- Create: `services/control-plane-api/store_control_plane/services/operations_worker.py`
- Create: `services/control-plane-api/store_control_plane/services/gst_export_jobs.py`
- Create: `services/control-plane-api/tests/test_compliance_async_jobs.py`
- Modify: `services/control-plane-api/store_control_plane/repositories/compliance.py`
- Modify: `services/control-plane-api/store_control_plane/services/compliance.py`
- Modify: `services/control-plane-api/store_control_plane/routes/compliance.py`
- Modify: `services/control-plane-api/store_control_plane/schemas/compliance.py`
- Modify: `packages/types/src/index.ts`

- [ ] **Step 1: Write failing compliance async tests**

```python
assert export_response.json()["status"] == "QUEUED"
assert queue_jobs[0]["job_type"] == "GST_EXPORT_PREPARE"
```

- [ ] **Step 2: Extend the failing tests to process the worker and confirm the export moves to `IRN_PENDING`**

```python
assert processed["completed"] == 1
assert refreshed_report.json()["records"][0]["status"] == "IRN_PENDING"
```

- [ ] **Step 3: Run the targeted compliance async tests and confirm they fail**

Run: `python -m pytest services/control-plane-api/tests/test_compliance_async_jobs.py -q`
Expected: FAIL because GST export creation is still inline.

- [ ] **Step 4: Add GST export preparation handler and worker dispatch**

```python
async def handle_gst_export_prepare(job): ...
```

- [ ] **Step 5: Change compliance create route to enqueue queued export work**

```python
job = await service.request_gst_export(...)
return GstExportJobResponse(**job)
```

- [ ] **Step 6: Re-run the targeted compliance async tests**

Run: `python -m pytest services/control-plane-api/tests/test_compliance_async_jobs.py -q`
Expected: PASS

- [ ] **Step 7: Commit the GST export async slice**

```bash
git add services/control-plane-api/store_control_plane/services/operations_worker.py services/control-plane-api/store_control_plane/services/gst_export_jobs.py services/control-plane-api/tests/test_compliance_async_jobs.py services/control-plane-api/store_control_plane/repositories/compliance.py services/control-plane-api/store_control_plane/services/compliance.py services/control-plane-api/store_control_plane/routes/compliance.py services/control-plane-api/store_control_plane/schemas/compliance.py packages/types/src/index.ts
git commit -m "feat: queue gst export preparation"
```

### Task 3: Move Supplier Snapshot Refresh Behind The Queue

**Files:**
- Create: `services/control-plane-api/store_control_plane/services/supplier_report_jobs.py`
- Create: `services/control-plane-api/tests/test_supplier_reporting_async_jobs.py`
- Modify: `services/control-plane-api/store_control_plane/repositories/supplier_reporting.py`
- Modify: `services/control-plane-api/store_control_plane/services/supplier_reporting.py`
- Modify: `services/control-plane-api/store_control_plane/routes/supplier_reporting.py`
- Modify: `services/control-plane-api/store_control_plane/schemas/supplier_reporting.py`
- Modify: `packages/types/src/index.ts`

- [ ] **Step 1: Write failing supplier snapshot async tests**

```python
assert dirty_response.json()["snapshot_status"] == "STALE_REFRESH_QUEUED"
assert queued_jobs[0]["job_type"] == "SUPPLIER_REPORT_REFRESH"
```

- [ ] **Step 2: Extend the tests to run the worker and verify the snapshot becomes clean**

```python
assert processed["completed"] >= 1
assert refreshed_response.json()["snapshot_status"] == "CURRENT"
```

- [ ] **Step 3: Run the targeted supplier async tests and confirm they fail**

Run: `python -m pytest services/control-plane-api/tests/test_supplier_reporting_async_jobs.py -q`
Expected: FAIL because dirty snapshots are still rebuilt inline.

- [ ] **Step 4: Add supplier snapshot refresh handler**

```python
async def refresh_supplier_snapshot(...): ...
```

- [ ] **Step 5: Change supplier reporting service so dirty snapshots enqueue refresh and return stale payload metadata**

```python
if snapshot is not None and snapshot.is_dirty:
    queued_job = await queue_service.enqueue_branch_job(...)
    return {**snapshot.payload, "snapshot_status": "STALE_REFRESH_QUEUED", "snapshot_job_id": queued_job.id}
```

- [ ] **Step 6: Keep first snapshot compatibility while avoiding async refresh regressions**

```python
if snapshot is None:
    payload = builder(source, report_date)
```

- [ ] **Step 7: Re-run the targeted supplier async tests**

Run: `python -m pytest services/control-plane-api/tests/test_supplier_reporting_async_jobs.py -q`
Expected: PASS

- [ ] **Step 8: Commit the supplier async slice**

```bash
git add services/control-plane-api/store_control_plane/services/supplier_report_jobs.py services/control-plane-api/tests/test_supplier_reporting_async_jobs.py services/control-plane-api/store_control_plane/repositories/supplier_reporting.py services/control-plane-api/store_control_plane/services/supplier_reporting.py services/control-plane-api/store_control_plane/routes/supplier_reporting.py services/control-plane-api/store_control_plane/schemas/supplier_reporting.py packages/types/src/index.ts
git commit -m "feat: queue supplier snapshot refresh"
```

### Task 4: Add Operations Visibility Routes, Worker Entry Point, And Owner-Web Posture

**Files:**
- Create: `services/control-plane-api/store_control_plane/routes/operations.py`
- Create: `services/control-plane-api/store_control_plane/schemas/operations.py`
- Create: `services/control-plane-api/scripts/run_operations_worker.py`
- Modify: `services/control-plane-api/store_control_plane/routes/__init__.py`
- Modify: `services/control-plane-api/store_control_plane/config/settings.py`
- Modify: `services/control-plane-api/README.md`
- Modify: `apps/owner-web/src/control-plane/client.ts`
- Modify: `apps/owner-web/src/control-plane/OwnerComplianceSection.tsx`
- Modify: `apps/owner-web/src/control-plane/OwnerSupplierReportingSection.tsx`
- Modify: `apps/owner-web/src/control-plane/OwnerComplianceSection.test.tsx`
- Modify: `apps/owner-web/src/control-plane/OwnerSupplierReportingSection.test.tsx`

- [ ] **Step 1: Write failing owner-web tests for queued export status and stale supplier reporting posture**

```tsx
expect(screen.getByText('QUEUED')).toBeInTheDocument()
expect(screen.getByText(/refresh queued/i)).toBeInTheDocument()
```

- [ ] **Step 2: Add failing API tests for operations job visibility and retry**

```python
assert jobs_response.json()["records"][0]["status"] == "DEAD_LETTER"
assert retry_response.json()["status"] == "QUEUED"
```

- [ ] **Step 3: Run the targeted API and owner-web tests and confirm they fail**

Run: `python -m pytest services/control-plane-api/tests/test_operations_queue.py services/control-plane-api/tests/test_compliance_async_jobs.py services/control-plane-api/tests/test_supplier_reporting_async_jobs.py -q`
Expected: FAIL on missing visibility routes or retry behavior.

Run: `npm run test --workspace @store/owner-web -- OwnerComplianceSection.test.tsx OwnerSupplierReportingSection.test.tsx`
Expected: FAIL on missing queued/stale UI posture.

- [ ] **Step 4: Add operations routes and worker CLI**

```python
@router.get("/v1/tenants/{tenant_id}/branches/{branch_id}/operations/jobs")
async def list_operations_jobs(...): ...
```

- [ ] **Step 5: Add owner-web posture for queued exports and stale supplier reports**

```tsx
{report?.snapshot_status === 'STALE_REFRESH_QUEUED' ? <p>Snapshot refresh queued.</p> : null}
```

- [ ] **Step 6: Re-run the targeted API and owner-web tests**

Run: `python -m pytest services/control-plane-api/tests/test_operations_queue.py services/control-plane-api/tests/test_compliance_async_jobs.py services/control-plane-api/tests/test_supplier_reporting_async_jobs.py -q`
Expected: PASS

Run: `npm run test --workspace @store/owner-web -- OwnerComplianceSection.test.tsx OwnerSupplierReportingSection.test.tsx`
Expected: PASS

- [ ] **Step 7: Commit the visibility and worker-entrypoint slice**

```bash
git add services/control-plane-api/store_control_plane/routes/operations.py services/control-plane-api/store_control_plane/schemas/operations.py services/control-plane-api/scripts/run_operations_worker.py services/control-plane-api/store_control_plane/routes/__init__.py services/control-plane-api/store_control_plane/config/settings.py services/control-plane-api/README.md apps/owner-web/src/control-plane/client.ts apps/owner-web/src/control-plane/OwnerComplianceSection.tsx apps/owner-web/src/control-plane/OwnerSupplierReportingSection.tsx apps/owner-web/src/control-plane/OwnerComplianceSection.test.tsx apps/owner-web/src/control-plane/OwnerSupplierReportingSection.test.tsx
git commit -m "feat: add operations job visibility"
```

### Task 5: Add Maintenance Sweep And Final Verification

**Files:**
- Modify: `services/control-plane-api/store_control_plane/services/operations_worker.py`
- Modify: `services/control-plane-api/tests/test_operations_queue.py`
- Modify: `docs/TASK_LEDGER.md`

- [ ] **Step 1: Add failing maintenance tests for expired leases and retention cleanup**

```python
assert requeued["status"] == "QUEUED"
assert cleaned["deleted_completed_jobs"] >= 1
```

- [ ] **Step 2: Run the targeted queue tests and confirm the maintenance assertions fail**

Run: `python -m pytest services/control-plane-api/tests/test_operations_queue.py -q`
Expected: FAIL on missing maintenance behavior.

- [ ] **Step 3: Add maintenance sweep behavior to the worker**

```python
async def run_maintenance_sweep(...): ...
```

- [ ] **Step 4: Re-run the queue tests**

Run: `python -m pytest services/control-plane-api/tests/test_operations_queue.py -q`
Expected: PASS

- [ ] **Step 5: Run full backend and owner-web verification**

Run: `python -m pytest services/control-plane-api/tests/test_operations_queue.py services/control-plane-api/tests/test_compliance_async_jobs.py services/control-plane-api/tests/test_supplier_reporting_async_jobs.py services/control-plane-api/tests/test_compliance_flow.py services/control-plane-api/tests/test_supplier_reporting_flow.py -q`
Expected: PASS

Run: `npm run test --workspace @store/owner-web -- OwnerComplianceSection.test.tsx OwnerSupplierReportingSection.test.tsx`
Expected: PASS

Run: `npm run typecheck --workspace @store/owner-web`
Expected: PASS

Run: `npm run build --workspace @store/owner-web`
Expected: PASS

- [ ] **Step 6: Mark `CP-019` done**

```bash
git add docs/TASK_LEDGER.md
git commit -m "docs: close cp-019"
```

