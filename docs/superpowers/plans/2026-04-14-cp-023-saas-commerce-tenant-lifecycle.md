# CP-023 SaaS Commerce And Tenant Lifecycle Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add billing plans, trial-backed tenant subscriptions, Cashfree or Razorpay recurring-subscription foundation, canonical entitlements, and lifecycle enforcement across owner-web and packaged runtime.

**Architecture:** Build canonical billing and entitlement persistence in the control plane first, add provider adapters and webhook normalization next, then expose platform-admin and owner-web lifecycle surfaces before enforcing entitlement state in auth and runtime activation or unlock flows. The control plane remains the only authority for subscription state and commercial enforcement; payment providers are external rails only.

**Tech Stack:** FastAPI, SQLAlchemy async ORM, Pydantic, React, Vitest, Python pytest

---

### Task 1: Add billing-plan, subscription, entitlement, and webhook persistence

**Files:**
- Create: `services/control-plane-api/alembic/versions/20260414_0022_saas_billing_lifecycle.py`
- Create: `services/control-plane-api/store_control_plane/models/commerce.py`
- Modify: `services/control-plane-api/store_control_plane/models/__init__.py`
- Create: `services/control-plane-api/store_control_plane/repositories/commerce.py`
- Test: `services/control-plane-api/tests/test_commerce_lifecycle.py`

- [ ] **Step 1: Write failing persistence tests**
- [ ] **Step 2: Run `python -m pytest services/control-plane-api/tests/test_commerce_lifecycle.py -q` and confirm red**
- [ ] **Step 3: Add the commerce models and Alembic migration**
- [ ] **Step 4: Add repository methods for plan, subscription, entitlement, and webhook-event reads or writes**
- [ ] **Step 5: Re-run the targeted pytest command and confirm green**
- [ ] **Step 6: Commit**

### Task 2: Add commerce schemas, provider adapters, and lifecycle service foundation

**Files:**
- Create: `services/control-plane-api/store_control_plane/schemas/commerce.py`
- Create: `services/control-plane-api/store_control_plane/services/subscription_providers.py`
- Create: `services/control-plane-api/store_control_plane/services/commerce.py`
- Modify: `services/control-plane-api/store_control_plane/services/__init__.py`
- Modify: `services/control-plane-api/store_control_plane/config/settings.py`
- Modify: `services/control-plane-api/store_control_plane/schemas/__init__.py`
- Test: `services/control-plane-api/tests/test_commerce_provider_adapters.py`
- Test: `services/control-plane-api/tests/test_commerce_lifecycle.py`

- [ ] **Step 1: Write failing provider and lifecycle-service tests**
- [ ] **Step 2: Run the targeted pytest commands and confirm red**
- [ ] **Step 3: Implement Cashfree and Razorpay provider adapter interfaces with deterministic stub behavior for tests**
- [ ] **Step 4: Implement lifecycle service methods for trial issuance, subscription bootstrap, webhook normalization, and entitlement refresh**
- [ ] **Step 5: Re-run the targeted pytest commands and confirm green**
- [ ] **Step 6: Commit**

### Task 3: Add platform-admin commerce routes and tenant lifecycle APIs

**Files:**
- Modify: `services/control-plane-api/store_control_plane/routes/platform.py`
- Create: `services/control-plane-api/store_control_plane/routes/commerce.py`
- Modify: `services/control-plane-api/store_control_plane/main.py`
- Test: `services/control-plane-api/tests/test_platform_commerce_routes.py`

- [ ] **Step 1: Write failing platform-admin route tests**
- [ ] **Step 2: Run `python -m pytest services/control-plane-api/tests/test_platform_commerce_routes.py -q` and confirm red**
- [ ] **Step 3: Add plan CRUD, tenant subscription summary, suspend, reactivate, and bounded override routes**
- [ ] **Step 4: Add owner bootstrap and provider-webhook ingestion routes**
- [ ] **Step 5: Re-run the targeted pytest command and confirm green**
- [ ] **Step 6: Commit**

### Task 4: Expand platform-admin UI for plans and tenant lifecycle

**Files:**
- Modify: `apps/platform-admin/src/control-plane/client.ts`
- Modify: `apps/platform-admin/src/control-plane/usePlatformAdminWorkspace.ts`
- Modify: `apps/platform-admin/src/control-plane/PlatformAdminWorkspace.tsx`
- Modify: `apps/platform-admin/src/App.test.tsx`
- Modify: `packages/types/src/index.ts`

- [ ] **Step 1: Write failing platform-admin UI tests for plan and lifecycle visibility**
- [ ] **Step 2: Run `npm run test --workspace @store/platform-admin` and confirm red**
- [ ] **Step 3: Add shared types and client methods for commerce routes**
- [ ] **Step 4: Add plan catalog and tenant lifecycle sections to the platform-admin workspace**
- [ ] **Step 5: Re-run the platform-admin test command and confirm green**
- [ ] **Step 6: Commit**

### Task 5: Add owner-web billing posture and recovery flow

**Files:**
- Create: `apps/owner-web/src/control-plane/OwnerBillingLifecycleSection.tsx`
- Modify: `apps/owner-web/src/control-plane/client.ts`
- Modify: `apps/owner-web/src/control-plane/OwnerWorkspace.tsx`
- Create: `apps/owner-web/src/control-plane/OwnerBillingLifecycleSection.test.tsx`
- Modify: `packages/types/src/index.ts`

- [ ] **Step 1: Write failing owner-web billing lifecycle tests**
- [ ] **Step 2: Run `npm run test --workspace @store/owner-web -- OwnerBillingLifecycleSection.test.tsx` and confirm red**
- [ ] **Step 3: Add owner client calls for current subscription, provider bootstrap, and lifecycle status**
- [ ] **Step 4: Add owner billing lifecycle UI for trial, active, grace, and suspended posture**
- [ ] **Step 5: Re-run the targeted owner-web test command and confirm green**
- [ ] **Step 6: Commit**

### Task 6: Enforce entitlement state across auth and packaged runtime

**Files:**
- Modify: `services/control-plane-api/store_control_plane/services/auth.py`
- Modify: `services/control-plane-api/store_control_plane/services/workforce.py`
- Modify: `services/control-plane-api/store_control_plane/services/offline_continuity.py`
- Modify: `services/control-plane-api/tests/test_store_desktop_activation_flow.py`
- Modify: `services/control-plane-api/tests/test_auth_exchange.py`
- Modify: `apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts`
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.activation.test.tsx`

- [ ] **Step 1: Write failing entitlement-enforcement tests**
- [ ] **Step 2: Run the targeted backend and desktop tests and confirm red**
- [ ] **Step 3: Block suspended tenants and expired-grace runtime access in auth and workforce services**
- [ ] **Step 4: Surface suspension or grace messaging in packaged runtime unlock and activation flow**
- [ ] **Step 5: Re-run the targeted backend and desktop tests and confirm green**
- [ ] **Step 6: Commit**

### Task 7: Verify the full SaaS-lifecycle slice and publish

**Files:**
- Modify only if verification exposes gaps
- Modify: `docs/TASK_LEDGER.md`
- Modify: `docs/WORKLOG.md`

- [ ] **Step 1: Run `python -m pytest services/control-plane-api/tests -q`**
- [ ] **Step 2: Run `npm run test --workspace @store/platform-admin`**
- [ ] **Step 3: Run `npm run test --workspace @store/owner-web`**
- [ ] **Step 4: Run `npm run test --workspace @store/store-desktop -- StoreRuntimeWorkspace.activation.test.tsx`**
- [ ] **Step 5: Run `npm run typecheck --workspace @store/platform-admin`**
- [ ] **Step 6: Run `npm run typecheck --workspace @store/owner-web`**
- [ ] **Step 7: Run `npm run typecheck --workspace @store/store-desktop`**
- [ ] **Step 8: Mark `CP-023` done in the ledger and add the worklog entry**
- [ ] **Step 9: Commit**
