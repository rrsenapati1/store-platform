# CP-020 GST IRP Integration Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace placeholder GST export and manual IRN attachment with a real provider-backed, async IRP submission flow plus explicit operator retry posture.

**Architecture:** Add a branch-scoped encrypted IRP profile, a provider adapter boundary with stub and IRIS-direct modes, and extend the existing async operations worker to prepare and submit GST export jobs through that provider. Owner web shifts from manual IRN entry to provider configuration, queue visibility, and retry actions.

**Tech Stack:** FastAPI, SQLAlchemy async ORM, httpx, cryptography, Pydantic, Vitest, React

---

### Task 1: Extend compliance persistence for provider-backed jobs

**Files:**
- Create: `services/control-plane-api/alembic/versions/20260414_0021_branch_irp_profiles.py`
- Modify: `services/control-plane-api/store_control_plane/models/compliance.py`
- Modify: `services/control-plane-api/store_control_plane/models/__init__.py`
- Modify: `services/control-plane-api/store_control_plane/repositories/compliance.py`
- Test: `services/control-plane-api/tests/test_compliance_provider_profiles.py`

- [ ] **Step 1: Write the failing profile-persistence tests**

Add tests for:
- creating a branch IRP profile,
- updating the API password,
- listing GST export jobs with new provider-status fields.

- [ ] **Step 2: Run the targeted tests to verify red**

Run: `python -m pytest services/control-plane-api/tests/test_compliance_provider_profiles.py -q`
Expected: FAIL because the model, repository methods, and schema fields do not exist.

- [ ] **Step 3: Add the model and migration**

Implement:
- `BranchIrpProfile`
- new `GstExportJob` columns for payload, provider status, attempts, and errors
- Alembic migration for the new table and job columns

- [ ] **Step 4: Add repository methods**

Implement repository support for:
- get or upsert branch IRP profile
- read decrypted-enough profile metadata
- set prepared payload and provider-status fields on export jobs

- [ ] **Step 5: Run the targeted tests to verify green**

Run: `python -m pytest services/control-plane-api/tests/test_compliance_provider_profiles.py -q`
Expected: PASS

- [ ] **Step 6: Commit**

Run:
`git add services/control-plane-api/alembic/versions/20260414_0021_branch_irp_profiles.py services/control-plane-api/store_control_plane/models/compliance.py services/control-plane-api/store_control_plane/models/__init__.py services/control-plane-api/store_control_plane/repositories/compliance.py services/control-plane-api/tests/test_compliance_provider_profiles.py`

Commit:
`git commit -m "feat: add branch irp profile persistence"`

### Task 2: Add encrypted branch IRP profile services and routes

**Files:**
- Create: `services/control-plane-api/store_control_plane/services/compliance_secrets.py`
- Modify: `services/control-plane-api/store_control_plane/config/settings.py`
- Modify: `services/control-plane-api/store_control_plane/schemas/compliance.py`
- Modify: `services/control-plane-api/store_control_plane/services/compliance.py`
- Modify: `services/control-plane-api/store_control_plane/routes/compliance.py`
- Modify: `services/control-plane-api/store_control_plane/main.py`
- Test: `services/control-plane-api/tests/test_compliance_provider_profiles.py`

- [ ] **Step 1: Write the failing service and route assertions**

Extend the profile test to cover:
- saving a branch profile through the route,
- password not being returned,
- failure when the encryption key is not configured.

- [ ] **Step 2: Run the targeted tests to verify red**

Run: `python -m pytest services/control-plane-api/tests/test_compliance_provider_profiles.py -q`
Expected: FAIL because the service, settings, and routes do not exist.

- [ ] **Step 3: Implement encrypted secret handling**

Add:
- application setting for compliance secret encryption key
- helper for encrypting and decrypting branch API passwords
- service methods to read or write branch IRP profiles

- [ ] **Step 4: Implement compliance profile routes**

Add:
- `GET /v1/tenants/{tenant_id}/branches/{branch_id}/compliance/provider-profile`
- `PUT /v1/tenants/{tenant_id}/branches/{branch_id}/compliance/provider-profile`

- [ ] **Step 5: Run the targeted tests to verify green**

Run: `python -m pytest services/control-plane-api/tests/test_compliance_provider_profiles.py -q`
Expected: PASS

- [ ] **Step 6: Commit**

Run:
`git add services/control-plane-api/store_control_plane/services/compliance_secrets.py services/control-plane-api/store_control_plane/config/settings.py services/control-plane-api/store_control_plane/schemas/compliance.py services/control-plane-api/store_control_plane/services/compliance.py services/control-plane-api/store_control_plane/routes/compliance.py services/control-plane-api/store_control_plane/main.py services/control-plane-api/tests/test_compliance_provider_profiles.py`

Commit:
`git commit -m "feat: add branch irp profile routes"`

### Task 3: Add provider adapter and job preparation or submission logic

**Files:**
- Create: `services/control-plane-api/store_control_plane/services/irp_provider.py`
- Create: `services/control-plane-api/store_control_plane/services/irp_payloads.py`
- Modify: `services/control-plane-api/store_control_plane/services/gst_export_jobs.py`
- Modify: `services/control-plane-api/store_control_plane/services/operations_worker.py`
- Modify: `services/control-plane-api/store_control_plane/services/compliance.py`
- Test: `services/control-plane-api/tests/test_compliance_irp_jobs.py`
- Test: `services/control-plane-api/tests/test_compliance_async_jobs.py`

- [ ] **Step 1: Write the failing worker tests**

Add tests for:
- stub-provider IRN submission success,
- duplicate-document recovery,
- action-required status for missing provider profile,
- retryable worker failure for transient provider outage.

- [ ] **Step 2: Run the targeted tests to verify red**

Run: `python -m pytest services/control-plane-api/tests/test_compliance_irp_jobs.py services/control-plane-api/tests/test_compliance_async_jobs.py -q`
Expected: FAIL because the provider adapter and new worker behavior do not exist.

- [ ] **Step 3: Implement provider interfaces**

Add:
- `DisabledIrpProvider`
- `StubIrpProvider`
- `IrisDirectIrpProvider`
- auth token caching and public-key auth payload encryption

- [ ] **Step 4: Implement payload preparation**

Build a domestic B2B payload from:
- branch GSTIN
- provider GSTIN lookups for seller and buyer
- sale lines plus catalog product metadata
- invoice totals

Persist the prepared payload on the export job for reuse and inspection.

- [ ] **Step 5: Implement worker submission flow**

Update `GstExportJobService.handle_prepare` so it:
- prepares payload,
- submits through provider,
- attaches IRN on success,
- handles duplicate-document lookup,
- marks `ACTION_REQUIRED` for business or configuration failures,
- raises for retryable transport failures.

- [ ] **Step 6: Run the targeted tests to verify green**

Run: `python -m pytest services/control-plane-api/tests/test_compliance_irp_jobs.py services/control-plane-api/tests/test_compliance_async_jobs.py -q`
Expected: PASS

- [ ] **Step 7: Commit**

Run:
`git add services/control-plane-api/store_control_plane/services/irp_provider.py services/control-plane-api/store_control_plane/services/irp_payloads.py services/control-plane-api/store_control_plane/services/gst_export_jobs.py services/control-plane-api/store_control_plane/services/operations_worker.py services/control-plane-api/store_control_plane/services/compliance.py services/control-plane-api/tests/test_compliance_irp_jobs.py services/control-plane-api/tests/test_compliance_async_jobs.py`

Commit:
`git commit -m "feat: submit gst exports through irp provider"`

### Task 4: Replace manual IRN attach with explicit retry and queue posture

**Files:**
- Modify: `services/control-plane-api/store_control_plane/routes/compliance.py`
- Modify: `services/control-plane-api/store_control_plane/schemas/compliance.py`
- Modify: `services/control-plane-api/store_control_plane/services/compliance.py`
- Modify: `services/control-plane-api/tests/test_compliance_flow.py`

- [ ] **Step 1: Write the failing route tests**

Update the compliance flow test so it:
- no longer manually attaches an IRN,
- expects worker-backed attachment,
- exercises retry for `ACTION_REQUIRED` jobs after provider profile setup.

- [ ] **Step 2: Run the targeted tests to verify red**

Run: `python -m pytest services/control-plane-api/tests/test_compliance_flow.py -q`
Expected: FAIL because manual attach is still the only flow.

- [ ] **Step 3: Replace manual attach routes**

Remove or retire manual attach from the public owner flow and add:
- retry-submission route
- richer job list response fields for provider status and last error

- [ ] **Step 4: Run the targeted tests to verify green**

Run: `python -m pytest services/control-plane-api/tests/test_compliance_flow.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

Run:
`git add services/control-plane-api/store_control_plane/routes/compliance.py services/control-plane-api/store_control_plane/schemas/compliance.py services/control-plane-api/store_control_plane/services/compliance.py services/control-plane-api/tests/test_compliance_flow.py`

Commit:
`git commit -m "feat: add compliance retry posture"`

### Task 5: Update owner web for provider profile and real queue posture

**Files:**
- Modify: `apps/owner-web/src/control-plane/client.ts`
- Modify: `apps/owner-web/src/control-plane/OwnerComplianceSection.tsx`
- Modify: `apps/owner-web/src/control-plane/OwnerComplianceSection.test.tsx`
- Modify: `packages/types/src/index.ts`

- [ ] **Step 1: Write the failing owner-web tests**

Cover:
- loading provider profile,
- saving API username and password,
- showing action-required errors,
- retrying a failed export,
- absence of manual IRN attach controls.

- [ ] **Step 2: Run the targeted tests to verify red**

Run: `npm run test --workspace @store/owner-web -- OwnerComplianceSection.test.tsx`
Expected: FAIL because the UI and client still assume manual IRN attach.

- [ ] **Step 3: Update the shared types and client calls**

Add the new compliance types and client methods for:
- branch provider profile
- retry submission
- richer job status fields

- [ ] **Step 4: Rework the compliance section**

Replace manual attach inputs with:
- provider profile form
- queue refresh
- status and error badges
- retry button for eligible jobs

- [ ] **Step 5: Run the targeted tests to verify green**

Run: `npm run test --workspace @store/owner-web -- OwnerComplianceSection.test.tsx`
Expected: PASS

- [ ] **Step 6: Commit**

Run:
`git add apps/owner-web/src/control-plane/client.ts apps/owner-web/src/control-plane/OwnerComplianceSection.tsx apps/owner-web/src/control-plane/OwnerComplianceSection.test.tsx packages/types/src/index.ts`

Commit:
`git commit -m "feat: update compliance ui for irp submission"`

### Task 6: Verify the full slice, close the warning fix, and publish

**Files:**
- Modify: `services/control-plane-api/tests/conftest.py`
- Modify: `docs/TASK_LEDGER.md`
- Modify: `services/control-plane-api/README.md`

- [ ] **Step 1: Keep the backend warning fix in scope**

Stage the existing `services/control-plane-api/tests/conftest.py` cleanup with this task so the backend suite remains warning-free.

- [ ] **Step 2: Update docs and ledger**

Mark `CP-020` done in `docs/TASK_LEDGER.md` and document the required IRP environment variables in `services/control-plane-api/README.md`.

- [ ] **Step 3: Run targeted backend verification**

Run:
`python -m pytest services/control-plane-api/tests/test_compliance_provider_profiles.py services/control-plane-api/tests/test_compliance_irp_jobs.py services/control-plane-api/tests/test_compliance_flow.py services/control-plane-api/tests/test_compliance_async_jobs.py -q`
Expected: PASS

- [ ] **Step 4: Run full backend verification**

Run:
`python -m pytest services/control-plane-api/tests -q`
Expected: PASS with no warnings

- [ ] **Step 5: Run owner-web verification**

Run:
- `npm run test --workspace @store/owner-web`
- `npm run typecheck --workspace @store/owner-web`
- `npm run build --workspace @store/owner-web`

Expected: PASS

- [ ] **Step 6: Run worker smoke verification**

Run:
`python scripts/run_operations_worker.py --help`

Expected: exit 0

- [ ] **Step 7: Commit and push**

Run:
`git add services/control-plane-api/tests/conftest.py docs/TASK_LEDGER.md services/control-plane-api/README.md`

If the warning fix is not already committed separately, include it in the final feature commit.

Final commit:
`git commit -m "feat: add gst irp integration"`

Push:
`git push origin main`
