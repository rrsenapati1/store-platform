# Reviewed Stock Count Sessions Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the owner-web one-step stock-count write with a reviewed stock-count session workflow where blind count entry happens first and inventory variance posts only on approval.

**Architecture:** Add a new reviewed-session backend model and routes while preserving the existing approved historical stock-count record. Owner-web switches to the reviewed-session workflow and surfaces a count board plus approval/cancel posture.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, React, TypeScript, Vitest.

---

### Task 1: Backend Reviewed Session Model

**Files:**
- Create: `services/control-plane-api/alembic/versions/20260415_0026_reviewed_stock_count_sessions.py`
- Modify: `services/control-plane-api/store_control_plane/models/inventory.py`
- Modify: `services/control-plane-api/store_control_plane/models/__init__.py`

- [ ] Add the new review-session table migration.
- [ ] Add the SQLAlchemy model and export it.
- [ ] Keep the existing approved stock-count table untouched for compatibility.

### Task 2: Backend Repository + Policy

**Files:**
- Modify: `services/control-plane-api/store_control_plane/repositories/inventory.py`
- Modify: `services/control-plane-api/store_control_plane/services/inventory_policy.py`
- Test: `services/control-plane-api/tests/test_inventory_policy.py`

- [ ] Write failing policy tests for reviewed-session status transitions and invalid actions.
- [ ] Add repository methods for create/get/list/record/approve/cancel session.
- [ ] Add minimal policy helpers for blind count validation and state transitions.
- [ ] Run the focused backend policy test and verify it passes.

### Task 3: Backend Service + Routes + Schemas

**Files:**
- Modify: `services/control-plane-api/store_control_plane/schemas/inventory.py`
- Modify: `services/control-plane-api/store_control_plane/schemas/__init__.py`
- Modify: `services/control-plane-api/store_control_plane/services/inventory.py`
- Modify: `services/control-plane-api/store_control_plane/routes/inventory.py`
- Test: `services/control-plane-api/tests/test_inventory_control_flow.py`

- [ ] Write a failing integration test for reviewed stock count session flow.
- [ ] Add request/response schemas for session creation, record, approval, cancel, and board.
- [ ] Implement service methods with approval-only ledger posting.
- [ ] Add the new routes.
- [ ] Run the focused flow test and verify it passes.

### Task 4: Owner Web Client + Actions

**Files:**
- Modify: `packages/types/src/index.ts`
- Modify: `apps/owner-web/src/control-plane/client.ts`
- Modify: `apps/owner-web/src/control-plane/inventoryActions.ts`

- [ ] Add type contracts for count board and reviewed session.
- [ ] Add client methods for the new count-session routes.
- [ ] Extend owner inventory actions with create/record/approve/cancel helpers.

### Task 5: Owner Web Workspace + UI

**Files:**
- Modify: `apps/owner-web/src/control-plane/useOwnerWorkspace.ts`
- Modify: `apps/owner-web/src/control-plane/OwnerInventoryControlSection.tsx`
- Test: `apps/owner-web/src/control-plane/OwnerWorkspace.inventory-control.test.tsx`

- [ ] Write or update the owner-web inventory-control test to fail against the new reviewed flow.
- [ ] Add only the minimal new workspace state required for session board and latest reviewed session.
- [ ] Replace the direct count button path with:
  - create session
  - record blind count
  - approve/cancel
- [ ] Run the focused owner-web inventory-control test and verify it passes.

### Task 6: Ledger + Verification

**Files:**
- Modify: `docs/WORKLOG.md`
- Modify: `docs/TASK_LEDGER.md`

- [ ] Record the reviewed stock-count session slice in the worklog.
- [ ] Keep `V2-004` as `In Progress`.
- [ ] Run fresh verification:
  - `C:\Users\Nebula\AppData\Local\Python\bin\python.exe -m pytest services/control-plane-api/tests/test_inventory_policy.py services/control-plane-api/tests/test_inventory_control_flow.py -q`
  - `npm run test --workspace @store/owner-web -- OwnerWorkspace.inventory-control.test.tsx`
  - `npm run test --workspace @store/owner-web`
  - `npm run typecheck --workspace @store/owner-web`
  - `npm run build --workspace @store/owner-web`
  - `git -c core.safecrlf=false diff --check`
