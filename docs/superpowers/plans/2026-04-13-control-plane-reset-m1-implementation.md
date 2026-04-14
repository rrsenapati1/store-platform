# Control-Plane Reset Milestone 1 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the side-by-side Milestone 1 control-plane foundation with Postgres-ready backend modules, Korsenex-IDP integration boundary, and API-driven onboarding flows in platform-admin and owner-web.

**Architecture:** Add a new `services/control-plane-api/` service in parallel to the legacy retail API. The new service owns auth exchange, actor resolution, tenant and branch onboarding, memberships, and audit events. Platform-admin and owner-web will consume this new service through small client modules and onboarding-focused screens.

**Tech Stack:** FastAPI, SQLAlchemy asyncio, Alembic, Pydantic settings, React 19, Vite, Vitest

---

### Task 1: Backend test harness for the new control plane

**Files:**
- Create: `services/control-plane-api/tests/conftest.py`
- Create: `services/control-plane-api/tests/test_onboarding_flow.py`
- Create: `services/control-plane-api/tests/test_auth_exchange.py`

- [ ] **Step 1: Write the failing tests**
- [ ] **Step 2: Run `python -m pytest services/control-plane-api/tests -q` and verify missing-module failures**
- [ ] **Step 3: Add minimal package scaffolding so the tests import the new service**
- [ ] **Step 4: Re-run the same tests and confirm they now fail on missing behavior rather than missing files**

### Task 2: Control-plane backend foundation

**Files:**
- Create: `services/control-plane-api/requirements.txt`
- Create: `services/control-plane-api/alembic.ini`
- Create: `services/control-plane-api/store_control_plane/__init__.py`
- Create: `services/control-plane-api/store_control_plane/main.py`
- Create: `services/control-plane-api/store_control_plane/config/settings.py`
- Create: `services/control-plane-api/store_control_plane/db/base.py`
- Create: `services/control-plane-api/store_control_plane/db/session.py`
- Create: `services/control-plane-api/store_control_plane/models/*.py`
- Create: `services/control-plane-api/store_control_plane/schemas/*.py`
- Create: `services/control-plane-api/store_control_plane/repositories/*.py`
- Create: `services/control-plane-api/store_control_plane/services/*.py`
- Create: `services/control-plane-api/store_control_plane/dependencies/*.py`
- Create: `services/control-plane-api/store_control_plane/routes/*.py`
- Create: `services/control-plane-api/alembic/env.py`
- Create: `services/control-plane-api/alembic/versions/20260413_0001_control_plane_baseline.py`

- [ ] **Step 1: Implement config and async DB session foundation**
- [ ] **Step 2: Implement baseline models for tenants, branches, memberships, invites, audit events, and app sessions**
- [ ] **Step 3: Implement repository and service layer for onboarding and actor resolution**
- [ ] **Step 4: Implement OIDC exchange boundary with a testable stub adapter**
- [ ] **Step 5: Implement thin route modules and `main.py` app assembly**
- [ ] **Step 6: Run `python -m pytest services/control-plane-api/tests -q` and get backend green**

### Task 3: Platform-admin onboarding flow

**Files:**
- Create: `apps/platform-admin/src/api/controlPlaneClient.ts`
- Modify: `apps/platform-admin/src/App.tsx`
- Modify: `apps/platform-admin/src/App.test.tsx`

- [ ] **Step 1: Write failing app tests for tenant list and tenant creation flow**
- [ ] **Step 2: Run `npm run test --workspace @store/platform-admin` and verify red**
- [ ] **Step 3: Implement control-plane client helpers**
- [ ] **Step 4: Replace the static shell with tenant onboarding and owner-invite workflow**
- [ ] **Step 5: Re-run `npm run test --workspace @store/platform-admin` and get green**

### Task 4: Owner-web onboarding flow

**Files:**
- Create: `apps/owner-web/src/api/controlPlaneClient.ts`
- Modify: `apps/owner-web/src/App.tsx`
- Modify: `apps/owner-web/src/App.test.tsx`

- [ ] **Step 1: Write failing app tests for actor context, branch creation, and membership assignment**
- [ ] **Step 2: Run `npm run test --workspace @store/owner-web` and verify red**
- [ ] **Step 3: Implement control-plane client helpers**
- [ ] **Step 4: Replace the static shell with first-branch setup and membership workflow**
- [ ] **Step 5: Re-run `npm run test --workspace @store/owner-web` and get green**

### Task 5: Repo docs and verification closeout

**Files:**
- Modify: `docs/API_CONTRACT_MATRIX.md`
- Modify: `docs/TASK_LEDGER.md`
- Modify: `docs/WORKLOG.md`
- Modify: `docs/context/MODULE_MAP.md`

- [ ] **Step 1: Update docs to reflect the implemented control-plane routes and module layout**
- [ ] **Step 2: Run `python -m pytest services/control-plane-api/tests -q`**
- [ ] **Step 3: Run `python -m pytest services/api/tests -q`**
- [ ] **Step 4: Run `npm run test`**
- [ ] **Step 5: Run `npm run typecheck`**
- [ ] **Step 6: Run `npm run build`**
