# Shelf/Backroom Restock Workflow Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first shelf/backroom restock workflow to `V2-004` so branch operators can create, pick, complete, and cancel explicit restock tasks for low-stock products.

**Architecture:** Add a new control-plane `restock_task_sessions` workflow and branch `restock board` without changing inventory authority. The backend persists task snapshots and status transitions, while owner-web gets a dedicated restock section plus focused action helpers so `useOwnerWorkspace.ts` remains orchestration-oriented instead of absorbing another full workflow.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, Pydantic, React, TypeScript, Vitest

---

### Task 1: Add Restock Task Persistence

**Files:**
- Create: `services/control-plane-api/alembic/versions/20260416_0029_restock_task_sessions.py`
- Modify: `services/control-plane-api/store_control_plane/models/inventory.py`
- Modify: `services/control-plane-api/store_control_plane/models/__init__.py`
- Modify: `services/control-plane-api/store_control_plane/repositories/inventory.py`

- [ ] Add a migration creating `restock_task_sessions` with branch-scoped `task_number`, task status, replenishment snapshots, requested/picked quantities, source posture, and notes.
- [ ] Add a new `RestockTaskSession` SQLAlchemy model in `models/inventory.py` and export it from `models/__init__.py`.
- [ ] Add inventory-repository helpers for:
  - next branch restock sequence
  - create restock task
  - load one restock task
  - list branch restock tasks
  - query active task for a branch/product

### Task 2: Add Restock Policy, Schemas, Service, And Routes

**Files:**
- Modify: `services/control-plane-api/store_control_plane/schemas/inventory.py`
- Modify: `services/control-plane-api/store_control_plane/schemas/__init__.py`
- Modify: `services/control-plane-api/store_control_plane/services/inventory_policy.py`
- Modify: `services/control-plane-api/store_control_plane/services/inventory.py`
- Modify: `services/control-plane-api/store_control_plane/routes/inventory.py`

- [ ] Add request/response schemas for:
  - restock task create
  - restock task pick
  - restock task complete
  - restock task cancel
  - restock task response
  - restock board record/response
- [ ] Add inventory-policy helpers for:
  - restock status transition guards
  - create-task validation
  - pick validation
  - board summary aggregation
- [ ] Add inventory-service orchestration for:
  - creating task from current branch stock + branch replenishment policy snapshots
  - recording `OPEN -> PICKED`
  - recording `PICKED -> COMPLETED`
  - recording `OPEN/PICKED -> CANCELED`
  - listing branch restock board
- [ ] Add new inventory routes:
  - `GET /v1/tenants/{tenant_id}/branches/{branch_id}/restock-board`
  - `POST /v1/tenants/{tenant_id}/branches/{branch_id}/restock-tasks`
  - `POST /v1/tenants/{tenant_id}/branches/{branch_id}/restock-tasks/{task_id}/pick`
  - `POST /v1/tenants/{tenant_id}/branches/{branch_id}/restock-tasks/{task_id}/complete`
  - `POST /v1/tenants/{tenant_id}/branches/{branch_id}/restock-tasks/{task_id}/cancel`

### Task 3: Add Backend Regression Coverage

**Files:**
- Modify: `services/control-plane-api/tests/test_inventory_policy.py`
- Create: `services/control-plane-api/tests/test_restock_flow.py`

- [ ] Add pure policy tests covering:
  - duplicate active-task rejection
  - invalid pick quantity rejection
  - invalid completion/cancel transition rejection
  - board count aggregation
- [ ] Add end-to-end API flow tests proving:
  - low-stock product can create a restock task
  - duplicate active task is rejected
  - `OPEN -> PICKED -> COMPLETED` works
  - `OPEN -> CANCELED` works
  - no restock transition creates inventory ledger entries

### Task 4: Wire Owner-Web Restock Surface

**Files:**
- Modify: `packages/types/src/index.ts`
- Modify: `apps/owner-web/src/control-plane/client.ts`
- Create: `apps/owner-web/src/control-plane/restockActions.ts`
- Create: `apps/owner-web/src/control-plane/OwnerRestockSection.tsx`
- Modify: `apps/owner-web/src/control-plane/useOwnerWorkspace.ts`
- Modify: `apps/owner-web/src/control-plane/OwnerWorkspace.tsx`
- Create: `apps/owner-web/src/control-plane/OwnerWorkspace.restock.test.tsx`

- [ ] Expand shared types and owner-web client contracts for restock task and restock board responses.
- [ ] Add focused `restockActions.ts` helpers for:
  - loading restock board
  - creating task
  - picking task
  - completing task
  - canceling task
- [ ] Add new owner-workspace state for:
  - restock board
  - latest restock task
  - requested quantity
  - picked quantity
  - source posture
  - restock note / completion note
- [ ] Add `OwnerRestockSection.tsx` that:
  - creates a task from the first low-stock product
  - shows latest active task detail
  - lets the operator mark picked
  - lets the operator complete or cancel
  - renders the restock board
- [ ] Mount the new section in `OwnerWorkspace.tsx` adjacent to replenishment and inventory-control surfaces.
- [ ] Add owner-web workflow coverage for task creation, pick, completion, and board updates.

### Task 5: Verify And Record The Slice

**Files:**
- Modify: `docs/WORKLOG.md`

- [ ] Run focused backend verification for restock policy and board behavior:
  - `C:\\Users\\Nebula\\AppData\\Local\\Python\\bin\\python.exe -m pytest services/control-plane-api/tests/test_inventory_policy.py services/control-plane-api/tests/test_restock_flow.py -q`
- [ ] Run focused owner-web workflow verification:
  - `npm run test --workspace @store/owner-web -- OwnerWorkspace.restock.test.tsx`
- [ ] Run broader owner-web verification:
  - `npm run test --workspace @store/owner-web`
  - `npm run typecheck --workspace @store/owner-web`
  - `npm run build --workspace @store/owner-web`
- [ ] Run `git -c core.safecrlf=false diff --check`.
- [ ] Record the restock-workflow slice in `docs/WORKLOG.md`.
