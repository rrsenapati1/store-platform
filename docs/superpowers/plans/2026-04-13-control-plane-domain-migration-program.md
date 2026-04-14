# Control-Plane Domain Migration Program Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the remaining enterprise migration program after Milestone 1 by moving catalog, procurement, inventory, billing, GST, print, and runtime authority off the legacy retail API in milestone order.

**Architecture:** Extend the new control plane as the system of record one bounded domain at a time. Each task must add modular models, repositories, services, schemas, routes, frontend integration, docs updates, and verification without reopening the oversized legacy entrypoint pattern.

**Tech Stack:** FastAPI, SQLAlchemy asyncio, Alembic, PostgreSQL, React 19, Vite, Vitest, Pytest

---

### Task 1: Complete CP-007 catalog, staff, and device migration

**Files:**
- Modify: `services/control-plane-api/store_control_plane/models/*.py`
- Modify: `services/control-plane-api/store_control_plane/repositories/*.py`
- Modify: `services/control-plane-api/store_control_plane/services/*.py`
- Modify: `services/control-plane-api/store_control_plane/schemas/*.py`
- Modify: `services/control-plane-api/store_control_plane/routes/*.py`
- Modify: `services/control-plane-api/alembic/versions/*.py`
- Modify: `apps/owner-web/src/control-plane/*.ts*`
- Test: `services/control-plane-api/tests/test_*catalog*.py`

- [ ] Finish CP-007 catalog depth needed before procurement handoff.
- [ ] Keep owner-web on the new control plane for staff, devices, and catalog.
- [ ] Remove any remaining legacy retail dependency for these three surfaces.

### Task 2: Execute CP-008 purchasing and inventory migration

**Files:**
- Create: `services/control-plane-api/store_control_plane/models/purchasing.py`
- Create: `services/control-plane-api/store_control_plane/models/inventory.py`
- Create: `services/control-plane-api/store_control_plane/repositories/purchasing.py`
- Create: `services/control-plane-api/store_control_plane/repositories/inventory.py`
- Create: `services/control-plane-api/store_control_plane/services/purchasing.py`
- Create: `services/control-plane-api/store_control_plane/services/inventory.py`
- Create: `services/control-plane-api/store_control_plane/schemas/purchasing.py`
- Create: `services/control-plane-api/store_control_plane/schemas/inventory.py`
- Create: `services/control-plane-api/store_control_plane/routes/purchasing.py`
- Create: `services/control-plane-api/store_control_plane/routes/inventory.py`
- Modify: `apps/owner-web/src/control-plane/*.ts*`
- Modify: `apps/store-desktop/src/**/*.tsx`

- [x] Move suppliers, purchase orders, approval gates, GRN, and supplier billing off the legacy API.
- [x] Establish supplier master, purchase-order creation, and approval-report foundations on the new control plane.
- [x] Establish approved-PO receipt, goods-receipt read models, and purchase-receipt ledger/snapshot foundations on the new backend.
- [x] Move stock adjustments, counts, and transfers onto the new backend.
- [x] Keep file boundaries modular and route modules domain-specific.

### Task 3: Execute CP-009 billing, GST, print, and runtime migration

**Files:**
- Create: `services/control-plane-api/store_control_plane/models/billing.py`
- Create: `services/control-plane-api/store_control_plane/models/runtime.py`
- Create: `services/control-plane-api/store_control_plane/repositories/billing.py`
- Create: `services/control-plane-api/store_control_plane/repositories/runtime.py`
- Create: `services/control-plane-api/store_control_plane/services/billing.py`
- Create: `services/control-plane-api/store_control_plane/services/runtime.py`
- Create: `services/control-plane-api/store_control_plane/schemas/billing.py`
- Create: `services/control-plane-api/store_control_plane/schemas/runtime.py`
- Create: `services/control-plane-api/store_control_plane/routes/billing.py`
- Create: `services/control-plane-api/store_control_plane/routes/runtime.py`
- Modify: `apps/store-desktop/src/**/*.tsx`

- [x] Move sales, invoices, GST document creation, credit notes, returns, and exchanges to the new backend.
- [x] Establish branch sale, GST invoice, and first store-desktop checkout foundations on the new backend.
- [x] Establish sale returns, credit-note generation, and owner refund approval on the new backend.
- [x] Establish cashier exchanges, replacement sale generation, and exchange credit allocation on the new backend.
- [x] Reattach print queue ownership and runtime device polling to the new architecture.
- [x] Define the boundary where branch-local SQLite becomes runtime cache only, not backend authority.

### Task 4: Hardening and legacy cutover

**Files:**
- Modify: `docs/**/*.md`
- Modify: `services/control-plane-api/README.md`
- Modify: `services/control-plane-api/compose.yaml`
- Modify: CI and verification scripts when introduced

- [x] Add runbook-grade verification for Alembic, Postgres, and app flows.
- [x] Define the cutover point where the legacy retail API is no longer authoritative.
- [x] Close the remaining task ledger items only after end-to-end verification passes.

### Task 5: Migrate remaining legacy operational support domains

**Files:**
- Modify: `services/control-plane-api/store_control_plane/services/*.py`
- Modify: `services/control-plane-api/store_control_plane/routes/*.py`
- Modify: `services/control-plane-api/store_control_plane/schemas/*.py`
- Modify: `apps/owner-web/src/control-plane/*.ts*`
- Modify: `apps/store-desktop/src/control-plane/*.ts*`
- Modify: `docs/**/*.md`

- [x] Move barcode allocation, scan lookup, and label preview onto the new control plane.
- [x] Move batch and expiry tracking onto the new control plane.
- [x] Move compliance export and document-job orchestration onto the new control plane.
- [x] Move customer reporting onto the new control plane.
- [ ] Move supplier reporting and sync-runtime surfaces onto the new control plane.
