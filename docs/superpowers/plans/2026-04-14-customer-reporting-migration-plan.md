# Customer Reporting Migration Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move customer directory, history, and branch customer report to the control plane with owner-web and store-desktop read-only visibility, and cut over legacy authority.

**Architecture:** Add a dedicated control-plane customer reporting module (models/repositories/services/schemas/routes) that aggregates from existing control-plane sales/returns/exchanges. Wire owner-web and store-desktop to the new read-only endpoints. Update authority manifest and legacy cutover rules.

**Tech Stack:** FastAPI, SQLAlchemy asyncio, Alembic, PostgreSQL, React 19, Vite, Vitest, Pytest

---

### Task 1: Add control-plane customer reporting backend (tests first)

**Files:**
- Create: `services/control-plane-api/store_control_plane/models/customers.py`
- Create: `services/control-plane-api/store_control_plane/repositories/customers.py`
- Create: `services/control-plane-api/store_control_plane/services/customer_reporting.py`
- Create: `services/control-plane-api/store_control_plane/schemas/customers.py`
- Create: `services/control-plane-api/store_control_plane/routes/customers.py`
- Modify: `services/control-plane-api/store_control_plane/models/__init__.py`
- Modify: `services/control-plane-api/store_control_plane/repositories/__init__.py`
- Modify: `services/control-plane-api/store_control_plane/services/__init__.py`
- Modify: `services/control-plane-api/store_control_plane/schemas/__init__.py`
- Modify: `services/control-plane-api/store_control_plane/routes/__init__.py`
- Modify: `services/control-plane-api/store_control_plane/main.py`
- Modify: `services/control-plane-api/alembic/versions/*.py`
- Test: `services/control-plane-api/tests/test_customer_reporting_flow.py`

- [x] **Step 1: Write failing backend flow test**

```python
def test_customer_directory_history_and_branch_report():
    # create tenant/branch, catalog, supplier, PO, GRN, sale, return, exchange
    # hit /customers, /customers/{id}/history, /branches/{id}/customer-report
    # assert counts, totals, and status fields
```

- [x] **Step 2: Run test to verify it fails**

Run: `python -m pytest services/control-plane-api/tests/test_customer_reporting_flow.py -q`  
Expected: FAIL with 404 or missing modules.

- [x] **Step 3: Implement models/repo/service**

```python
# customers.py: CustomerIndex, CustomerEvent, CustomerReport
# repositories/customers.py: read aggregation from sales/returns/exchanges
# services/customer_reporting.py: guardrails + read model construction
```

- [x] **Step 4: Add schemas and routes**

```python
class CustomerDirectoryResponse(BaseModel): ...
class CustomerHistoryResponse(BaseModel): ...
class BranchCustomerReportResponse(BaseModel): ...
```

- [x] **Step 5: Add Alembic migration (if any tables are persisted)**

No new persisted tables were added for customer reporting; migration skipped.

- [x] **Step 6: Run test to verify it passes**

Run: `python -m pytest services/control-plane-api/tests/test_customer_reporting_flow.py -q`  
Expected: PASS

- [ ] **Step 7: Commit (skipped: repo is not a git workspace)**

```bash
git add services/control-plane-api/store_control_plane services/control-plane-api/tests services/control-plane-api/alembic
git commit -m "feat: add control-plane customer reporting read models"
```

---

### Task 2: Owner-web read-only customer reporting section

**Files:**
- Create: `apps/owner-web/src/control-plane/OwnerCustomerInsightsSection.tsx`
- Modify: `apps/owner-web/src/control-plane/client.ts`
- Modify: `apps/owner-web/src/control-plane/OwnerWorkspace.tsx`
- Modify: `packages/types/src/index.ts`
- Test: `apps/owner-web/src/control-plane/OwnerCustomerInsightsSection.test.tsx`
- Test: `apps/owner-web/src/App.test.tsx`

- [x] **Step 1: Write failing owner-web test**

```tsx
test('loads customer directory, history, and branch report', async () => {
  // mock directory + history + branch report responses
  // expect rendered summary and customer selection
})
```

- [x] **Step 2: Run test to verify it fails**

Run: `npm run test --workspace @store/owner-web -- OwnerCustomerInsightsSection.test.tsx`  
Expected: FAIL due to missing component.

- [x] **Step 3: Implement client + types + section**

```ts
client.listCustomers(...)
client.getCustomerHistory(...)
client.getBranchCustomerReport(...)
```

- [x] **Step 4: Wire section into owner workspace**

Mount the section after procurement/returns and before device registration.

- [x] **Step 5: Run tests**

Run: `npm run test --workspace @store/owner-web -- OwnerCustomerInsightsSection.test.tsx App.test.tsx`  
Expected: PASS

- [ ] **Step 6: Commit (skipped: repo is not a git workspace)**

```bash
git add apps/owner-web packages/types
git commit -m "feat: add owner-web customer reporting section"
```

---

### Task 3: Store-desktop read-only customer reporting section

**Files:**
- Create: `apps/store-desktop/src/control-plane/StoreCustomerInsightsSection.tsx`
- Modify: `apps/store-desktop/src/control-plane/client.ts`
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.tsx`
- Modify: `packages/types/src/index.ts` (if needed)
- Test: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.customers.test.tsx`

- [x] **Step 1: Write failing store-desktop test**

```tsx
test('loads branch customer report and directory in read-only mode', async () => {
  // mock directory + branch report responses
})
```

- [x] **Step 2: Run test to verify it fails**

Run: `npm run test --workspace @store/store-desktop -- StoreRuntimeWorkspace.customers.test.tsx`  
Expected: FAIL due to missing component.

- [x] **Step 3: Implement client + section**

Read-only UI, no mutation actions.

- [x] **Step 4: Wire section into runtime workspace**

Mount near existing report surfaces (sales register).

- [x] **Step 5: Run tests**

Run: `npm run test --workspace @store/store-desktop -- StoreRuntimeWorkspace.customers.test.tsx`  
Expected: PASS

- [ ] **Step 6: Commit (skipped: repo is not a git workspace)**

```bash
git add apps/store-desktop packages/types
git commit -m "feat: add store-desktop customer reporting section"
```

---

### Task 4: Authority, verifier, and docs

**Files:**
- Modify: `services/control-plane-api/store_control_plane/services/authority.py`
- Modify: `services/api/store_api/authority.py`
- Modify: `services/api/tests/test_authority_cutover.py`
- Modify: `services/control-plane-api/store_control_plane/verification.py`
- Modify: `services/control-plane-api/tests/test_verification_smoke.py`
- Modify: `docs/TASK_LEDGER.md`
- Modify: `docs/API_CONTRACT_MATRIX.md`
- Modify: `docs/context/MODULE_MAP.md`
- Modify: `docs/PROJECT_CONTEXT.md`
- Modify: `docs/STORE_CANONICAL_BLUEPRINT.md`
- Modify: `docs/WORKLOG.md`
- Modify: `docs/superpowers/plans/2026-04-13-control-plane-domain-migration-program.md`

- [ ] **Step 1: Add authority and legacy cutover classification**

Update migrated domains and legacy patterns.

- [ ] **Step 2: Update verifier to hit the new endpoints**

Add directory/history/report checks after sales flow.

- [ ] **Step 3: Update docs and ledger**

Mark CP-011D done and document new contracts.

- [ ] **Step 4: Full verification**

Run: `python -m pytest services/control-plane-api/tests -q`  
Run: `python -m pytest services/api/tests/test_authority_cutover.py -q`  
Run: `npm run test`  
Run: `npm run typecheck`  
Run: `npm run build`  
Run: `python services/control-plane-api/scripts/verify_control_plane.py`

- [ ] **Step 5: Commit**

```bash
git add services docs apps packages
git commit -m "feat: migrate customer reporting to control plane"
```
