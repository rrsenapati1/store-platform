# Reviewed Goods Receipt Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace blind full-PO receiving with a reviewed goods-receipt workflow that captures per-line received quantities and discrepancies in the control plane and owner-web.

**Architecture:** Extend the existing goods-receipt foundation rather than adding a new draft subsystem. Persist ordered-vs-received detail on receipt lines, keep one receipt per purchase order for now, and surface reviewed discrepancy posture through receiving-board and owner-web read models.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, Pydantic, React, TypeScript, Vitest

---

### Task 1: Extend Receiving Persistence And Policy

**Files:**
- Create: `services/control-plane-api/alembic/versions/20260415_0025_reviewed_goods_receipts.py`
- Modify: `services/control-plane-api/store_control_plane/models/inventory.py`
- Modify: `services/control-plane-api/store_control_plane/repositories/inventory.py`
- Modify: `services/control-plane-api/store_control_plane/services/inventory_policy.py`
- Test: `services/control-plane-api/tests/test_inventory_policy.py`

- [ ] Add migration columns for receipt note, ordered quantity, and discrepancy note.
- [ ] Update inventory models and repository create/list paths to persist and read the new fields.
- [ ] Add reviewed-line policy helpers that validate received quantities and compute variance.
- [ ] Add or update policy tests for partial receipt and invalid reviewed payloads.

### Task 2: Expand Inventory Service And Routes

**Files:**
- Modify: `services/control-plane-api/store_control_plane/schemas/inventory.py`
- Modify: `services/control-plane-api/store_control_plane/schemas/__init__.py`
- Modify: `services/control-plane-api/store_control_plane/routes/inventory.py`
- Modify: `services/control-plane-api/store_control_plane/services/inventory.py`
- Test: `services/control-plane-api/tests/test_receiving_foundation_flow.py`

- [ ] Expand the goods-receipt request/response schemas for reviewed lines and discrepancy metadata.
- [ ] Update `create_goods_receipt(...)` to accept reviewed lines, validate them, and post ledger entries from actual received quantities.
- [ ] Update receiving-board and goods-receipt list serialization to expose discrepancy posture.
- [ ] Add backend flow coverage for matched receipt, partial receipt, and invalid receipt attempts.

### Task 3: Update Shared Types And Owner Client

**Files:**
- Modify: `packages/types/src/index.ts`
- Modify: `apps/owner-web/src/control-plane/client.ts`

- [ ] Expand shared goods-receipt and receiving-board types with reviewed-line fields and discrepancy summaries.
- [ ] Update the owner-web client request shape for reviewed goods receipts.

### Task 4: Add Reviewed Receiving State And Actions In Owner-Web

**Files:**
- Modify: `apps/owner-web/src/control-plane/useOwnerWorkspace.ts`
- Modify: `apps/owner-web/src/control-plane/inventoryActions.ts`
- Modify: `apps/owner-web/src/control-plane/OwnerReceivingSection.tsx`
- Test: `apps/owner-web/src/control-plane/OwnerWorkspace.receiving.test.tsx`

- [ ] Add receiving-form state derived from the latest approved purchase order.
- [ ] Submit reviewed line payloads plus receipt note instead of a blind one-click receive action.
- [ ] Render reviewed line inputs, summary totals, and receipt discrepancy posture in the receiving section.
- [ ] Update owner-web tests to cover reviewed partial receipt and receiving-board discrepancy display.

### Task 5: Verify And Close Out Docs

**Files:**
- Modify: `docs/TASK_LEDGER.md`
- Modify: `docs/WORKLOG.md`

- [ ] Run focused backend and owner-web verification.
- [ ] Run workspace typecheck or build as needed for touched surfaces.
- [ ] Update the ledger to mark `V2-004` in progress with this receiving-depth slice recorded in the worklog.
