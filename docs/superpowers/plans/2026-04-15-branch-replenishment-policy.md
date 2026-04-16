# Branch Replenishment Policy Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a first replenishment slice to `V2-004` by persisting branch-level reorder policy and exposing a low-stock suggestion board in the control plane and owner-web.

**Architecture:** Extend `branch_catalog_items` with simple replenishment policy fields and derive the branch suggestion board from branch catalog items plus the existing inventory snapshot. Keep the UI small: one policy form and one replenishment board section in owner-web.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, Pydantic, React, TypeScript, Vitest

---

### Task 1: Add Replenishment Policy Persistence

**Files:**
- Create: `services/control-plane-api/alembic/versions/20260415_0028_branch_replenishment_policy.py`
- Modify: `services/control-plane-api/store_control_plane/models/catalog.py`
- Modify: `services/control-plane-api/store_control_plane/repositories/catalog.py`

- [ ] Add nullable `reorder_point` and `target_stock` columns to branch catalog items.
- [ ] Persist the new policy fields through the branch catalog repository upsert path.

### Task 2: Expand Catalog And Inventory Contracts

**Files:**
- Modify: `services/control-plane-api/store_control_plane/schemas/catalog.py`
- Modify: `services/control-plane-api/store_control_plane/services/catalog.py`
- Modify: `services/control-plane-api/store_control_plane/routes/catalog.py`
- Modify: `services/control-plane-api/store_control_plane/schemas/inventory.py`
- Modify: `services/control-plane-api/store_control_plane/schemas/__init__.py`
- Modify: `services/control-plane-api/store_control_plane/services/inventory_policy.py`
- Modify: `services/control-plane-api/store_control_plane/services/inventory.py`
- Modify: `services/control-plane-api/store_control_plane/routes/inventory.py`

- [ ] Validate replenishment policy inputs on branch catalog upsert.
- [ ] Add replenishment-board response schemas.
- [ ] Add policy helper logic that derives low-stock vs adequate suggestions from current stock and branch policy.
- [ ] Expose a new branch replenishment-board route.

### Task 3: Add Backend Regression Coverage

**Files:**
- Modify: `services/control-plane-api/tests/test_inventory_policy.py`
- Create: `services/control-plane-api/tests/test_replenishment_flow.py`

- [ ] Add pure policy coverage for replenishment suggestion derivation.
- [ ] Add end-to-end API coverage for persisting policy and reading the replenishment board.

### Task 4: Wire Owner-Web Replenishment Surface

**Files:**
- Modify: `packages/types/src/index.ts`
- Modify: `apps/owner-web/src/control-plane/client.ts`
- Create: `apps/owner-web/src/control-plane/replenishmentActions.ts`
- Create: `apps/owner-web/src/control-plane/OwnerReplenishmentSection.tsx`
- Modify: `apps/owner-web/src/control-plane/useOwnerWorkspace.ts`
- Modify: `apps/owner-web/src/control-plane/OwnerWorkspace.tsx`
- Create: `apps/owner-web/src/control-plane/OwnerWorkspace.replenishment.test.tsx`

- [ ] Expand shared types and owner-web client contracts for replenishment policy and board reads.
- [ ] Add focused replenishment actions so `useOwnerWorkspace.ts` stays wiring-oriented.
- [ ] Add owner-web state and UI for editing the first branch item's replenishment policy and rendering the branch suggestion board.
- [ ] Add workflow coverage for policy update and low-stock board rendering.

### Task 5: Verify And Record The Slice

**Files:**
- Modify: `docs/WORKLOG.md`

- [ ] Run focused backend verification for replenishment policy and board behavior.
- [ ] Run owner-web tests, typecheck, and build.
- [ ] Run `git diff --check`.
- [ ] Record the replenishment slice in the worklog.
