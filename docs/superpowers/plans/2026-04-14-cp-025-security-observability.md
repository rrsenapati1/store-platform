# CP-025 Security And Observability Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add hybrid production observability and first-pass security hardening with Sentry-backed engineering diagnostics, internal operator observability, structured backend logging, secure headers, and rate limiting.

**Architecture:** Split the work into three aligned layers: backend middleware and diagnostics in `services/control-plane-api`, operator-facing summary routes plus platform-admin UI for Store-specific posture, and environment-guarded Sentry bootstrapping for owner-web and platform-admin. Keep packaged desktop out of the first slice, use one stable backend request/context envelope, and treat security hardening as enforceable middleware rather than runbook-only advice.

**Tech Stack:** FastAPI, SQLAlchemy async ORM, Pydantic, Python logging, Sentry SDK for Python/FastAPI, React, Vite, Vitest, TypeScript, Markdown runbooks

---

## Planned File Structure

### Backend configuration and middleware

- `services/control-plane-api/store_control_plane/config/settings.py`
  - add Sentry DSN, sample-rate, rate-limit, log-format, and secure-header configuration
- `services/control-plane-api/store_control_plane/main.py`
  - wire middleware and Sentry bootstrap into app startup
- `services/control-plane-api/store_control_plane/logging.py`
  - JSON log formatting and scrub helpers
- `services/control-plane-api/store_control_plane/middleware/request_context.py`
  - request ID generation and request-context extraction
- `services/control-plane-api/store_control_plane/middleware/security.py`
  - secure-header middleware
- `services/control-plane-api/store_control_plane/middleware/rate_limit.py`
  - simple in-process rate limiter for sensitive routes
- `services/control-plane-api/store_control_plane/observability/sentry.py`
  - backend Sentry bootstrap and event scrubbing

### Backend observability routes and read models

- `services/control-plane-api/store_control_plane/routes/platform.py`
  - add observability endpoints under the platform-admin boundary
- `services/control-plane-api/store_control_plane/schemas/platform.py`
  - add observability response payloads
- `services/control-plane-api/store_control_plane/services/platform_observability.py`
  - aggregate health, worker/job, runtime, and backup summaries
- `services/control-plane-api/store_control_plane/repositories/operations.py`
  - add dead-letter and recent-failure summary reads
- `services/control-plane-api/store_control_plane/repositories/sync_runtime.py`
  - add runtime degradation summary reads

### Frontend observability and Sentry bootstrapping

- `apps/platform-admin/package.json`
- `apps/platform-admin/src/main.tsx`
- `apps/platform-admin/src/control-plane/client.ts`
- `apps/platform-admin/src/control-plane/usePlatformAdminWorkspace.ts`
- `apps/platform-admin/src/control-plane/PlatformAdminWorkspace.tsx`
- `apps/platform-admin/src/control-plane/PlatformAdminObservabilitySection.tsx`
- `apps/platform-admin/src/control-plane/PlatformAdminObservabilitySection.test.tsx`
- `apps/owner-web/package.json`
- `apps/owner-web/src/main.tsx`
- `packages/types/src/index.ts`
  - add shared observability payload types

### Runbooks and docs

- `services/control-plane-api/.env.example`
- `services/control-plane-api/README.md`
- `docs/runbooks/control-plane-production-deployment.md`
- `docs/runbooks/security-observability-operations.md`
- `docs/runbooks/dependency-scanning.md`

### Tests

- `services/control-plane-api/tests/test_settings.py`
- `services/control-plane-api/tests/test_platform_observability_routes.py`
- `services/control-plane-api/tests/test_rate_limiting.py`
- `services/control-plane-api/tests/test_security_headers.py`
- `services/control-plane-api/tests/test_logging_context.py`
- `apps/platform-admin/src/control-plane/PlatformAdminObservabilitySection.test.tsx`
- `apps/platform-admin/src/App.test.tsx`

---

### Task 1: Expand settings for Sentry, logging, rate limits, and secure headers

**Files:**
- Modify: `services/control-plane-api/store_control_plane/config/settings.py`
- Modify: `services/control-plane-api/tests/test_settings.py`
- Modify: `services/control-plane-api/.env.example`
- Modify: `services/control-plane-api/README.md`

- [ ] **Step 1: Write failing settings tests for Sentry DSN, release environment, rate-limit values, and secure-header configuration**
- [ ] **Step 2: Run `python -m pytest services/control-plane-api/tests/test_settings.py -q` and confirm red**
- [ ] **Step 3: Add new normalized settings for backend Sentry, logging mode, rate-limit thresholds, and secure-header toggles**
- [ ] **Step 4: Update `.env.example` and README documentation for staging/prod observability configuration**
- [ ] **Step 5: Re-run `python -m pytest services/control-plane-api/tests/test_settings.py -q` and confirm green**
- [ ] **Step 6: Commit**

### Task 2: Add backend request context, JSON logging, secure headers, and rate limiting

**Files:**
- Create: `services/control-plane-api/store_control_plane/logging.py`
- Create: `services/control-plane-api/store_control_plane/middleware/request_context.py`
- Create: `services/control-plane-api/store_control_plane/middleware/security.py`
- Create: `services/control-plane-api/store_control_plane/middleware/rate_limit.py`
- Modify: `services/control-plane-api/store_control_plane/main.py`
- Create: `services/control-plane-api/tests/test_logging_context.py`
- Create: `services/control-plane-api/tests/test_security_headers.py`
- Create: `services/control-plane-api/tests/test_rate_limiting.py`

- [ ] **Step 1: Write failing backend middleware tests for request IDs, secure headers, and repeated auth/webhook throttling**
- [ ] **Step 2: Run `python -m pytest services/control-plane-api/tests/test_logging_context.py services/control-plane-api/tests/test_security_headers.py services/control-plane-api/tests/test_rate_limiting.py -q` and confirm red**
- [ ] **Step 3: Implement request-context middleware and JSON log shaping with secret scrubbing**
- [ ] **Step 4: Implement secure-header middleware and a bounded in-process rate limiter for sensitive routes**
- [ ] **Step 5: Wire the middleware into app startup in a stable order**
- [ ] **Step 6: Re-run the targeted pytest commands and confirm green**
- [ ] **Step 7: Commit**

### Task 3: Add backend Sentry integration and scrubbing

**Files:**
- Modify: `services/control-plane-api/requirements.txt`
- Create: `services/control-plane-api/store_control_plane/observability/sentry.py`
- Modify: `services/control-plane-api/store_control_plane/main.py`
- Modify: `services/control-plane-api/tests/test_logging_context.py`

- [ ] **Step 1: Write failing backend tests or unit checks for Sentry event scrubbing and environment-guarded initialization**
- [ ] **Step 2: Run the targeted pytest command and confirm red**
- [ ] **Step 3: Add backend Sentry bootstrap with request, tenant, branch, and job context tagging**
- [ ] **Step 4: Add `before_send` scrubbing for auth headers, secrets, PIN material, and provider credentials**
- [ ] **Step 5: Re-run the targeted pytest command and confirm green**
- [ ] **Step 6: Commit**

### Task 4: Add platform observability summary routes

**Files:**
- Create: `services/control-plane-api/store_control_plane/services/platform_observability.py`
- Modify: `services/control-plane-api/store_control_plane/repositories/operations.py`
- Modify: `services/control-plane-api/store_control_plane/repositories/sync_runtime.py`
- Modify: `services/control-plane-api/store_control_plane/routes/platform.py`
- Modify: `services/control-plane-api/store_control_plane/schemas/platform.py`
- Create: `services/control-plane-api/tests/test_platform_observability_routes.py`

- [ ] **Step 1: Write failing route tests for observability summary, recent failing jobs, runtime degradation, and backup freshness payloads**
- [ ] **Step 2: Run `python -m pytest services/control-plane-api/tests/test_platform_observability_routes.py -q` and confirm red**
- [ ] **Step 3: Add repository helpers for dead-letter counts, recent failures, and runtime degradation summaries**
- [ ] **Step 4: Add a platform observability service and read-only platform-admin routes**
- [ ] **Step 5: Re-run `python -m pytest services/control-plane-api/tests/test_platform_observability_routes.py -q` and confirm green**
- [ ] **Step 6: Commit**

### Task 5: Add platform-admin observability UI and shared types

**Files:**
- Modify: `packages/types/src/index.ts`
- Modify: `apps/platform-admin/src/control-plane/client.ts`
- Modify: `apps/platform-admin/src/control-plane/usePlatformAdminWorkspace.ts`
- Modify: `apps/platform-admin/src/control-plane/PlatformAdminWorkspace.tsx`
- Create: `apps/platform-admin/src/control-plane/PlatformAdminObservabilitySection.tsx`
- Create: `apps/platform-admin/src/control-plane/PlatformAdminObservabilitySection.test.tsx`
- Modify: `apps/platform-admin/src/App.test.tsx`

- [ ] **Step 1: Write failing platform-admin UI tests for observability rendering and incident posture**
- [ ] **Step 2: Run `npm run test --workspace @store/platform-admin -- PlatformAdminObservabilitySection.test.tsx` and confirm red**
- [ ] **Step 3: Add shared types and platform-admin client methods for observability routes**
- [ ] **Step 4: Add a dedicated observability section to the platform-admin workspace**
- [ ] **Step 5: Re-run the targeted platform-admin test command and confirm green**
- [ ] **Step 6: Commit**

### Task 6: Add Sentry bootstrapping for owner-web and platform-admin

**Files:**
- Modify: `apps/platform-admin/package.json`
- Modify: `apps/platform-admin/src/main.tsx`
- Modify: `apps/owner-web/package.json`
- Modify: `apps/owner-web/src/main.tsx`
- Modify: `apps/platform-admin/src/App.test.tsx`
- Modify: `apps/owner-web/src/App.test.tsx`

- [ ] **Step 1: Write failing frontend tests for environment-guarded Sentry initialization**
- [ ] **Step 2: Run `npm run test --workspace @store/platform-admin` and `npm run test --workspace @store/owner-web` and confirm red in the targeted assertions**
- [ ] **Step 3: Add `@sentry/react` dependencies and initialize Sentry only when DSN + non-test environment are present**
- [ ] **Step 4: Include release/environment tagging for both web apps**
- [ ] **Step 5: Re-run the targeted web test commands and confirm green**
- [ ] **Step 6: Commit**

### Task 7: Add security/observability runbooks and verify the slice

**Files:**
- Create: `docs/runbooks/security-observability-operations.md`
- Create: `docs/runbooks/dependency-scanning.md`
- Modify: `docs/runbooks/control-plane-production-deployment.md`
- Modify: `docs/TASK_LEDGER.md`
- Modify: `docs/WORKLOG.md`

- [ ] **Step 1: Document alert thresholds, Sentry environment wiring, rate-limit posture, and operator incident flow**
- [ ] **Step 2: Document baseline dependency/image scanning commands and release-blocker posture**
- [ ] **Step 3: Run `python -m pytest services/control-plane-api/tests -q`**
- [ ] **Step 4: Run `npm run test --workspace @store/platform-admin`**
- [ ] **Step 5: Run `npm run test --workspace @store/owner-web`**
- [ ] **Step 6: Run `npm run typecheck --workspace @store/platform-admin`**
- [ ] **Step 7: Run `npm run typecheck --workspace @store/owner-web`**
- [ ] **Step 8: Run `npm run build --workspace @store/platform-admin`**
- [ ] **Step 9: Run `npm run build --workspace @store/owner-web`**
- [ ] **Step 10: Mark `CP-025` done in the ledger and add the worklog entry**
- [ ] **Step 11: Commit**
