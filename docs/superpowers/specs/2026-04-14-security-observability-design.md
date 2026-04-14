# Security And Observability Design

Date: 2026-04-14
Task: `CP-025`
Status: Drafted after design approval

## Goal

Add the first production-grade security and observability layer for the Store control plane and web surfaces.

This task is meant to close the most important launch gaps:

- engineering diagnostics for backend and web exceptions
- structured operational visibility for platform operators
- baseline request hardening
- explicit alert and scan posture

It is not meant to build a full internal observability product or a full SOC-style security stack.

## Chosen Observability Model

The accepted approach is a hybrid split:

- `Sentry` for engineering diagnostics
- self-managed logs, health, and metrics for operator workflows
- internal platform-admin observability views for Store-specific operational posture

This is the fastest path to actionable incident response without turning `CP-025` into “build our own Sentry”.

## Scope

### In Scope

- backend exception monitoring for `services/control-plane-api`
- web exception monitoring for:
  - `apps/owner-web`
  - `apps/platform-admin`
- structured JSON request and error logging on the control plane
- request ID generation and propagation
- platform-admin internal observability surface
- first security hardening pass:
  - secure headers
  - rate limiting on sensitive routes
  - secret scrubbing
- alert-threshold documentation
- dependency-scan and image-scan baseline runbook posture

### Out of Scope

- full desktop Sentry instrumentation
- centralized log shipping platform
- full metrics stack like Prometheus/Grafana
- SIEM integration
- hosted CI automation for scans and alerts

Those belong primarily to later hardening and CI/CD work.

## Observability Split

### Sentry Lane

Use Sentry for developer-facing diagnostics.

Surfaces:

- FastAPI backend exceptions
- owner-web frontend exceptions
- platform-admin frontend exceptions

Required Sentry context:

- `environment`
- `release`
- `request_id`
- `tenant_id`
- `branch_id`
- `actor_email`
- `device_id`
- `job_type`
- `job_id`

Use Sentry for:

- unhandled exceptions
- async job failures after retry exhaustion
- new release regressions
- frontend crashes and unhandled promise rejections

Do not use Sentry for:

- high-volume business events
- branch heartbeat streams
- audit-event archives
- backup metadata

### Self-Managed Ops Lane

Keep operator-facing observability in the product and VM stack.

This includes:

- structured JSON logs on the app VM
- health and deployment status
- worker/job posture
- branch sync/runtime degradation
- offline continuity backlog
- backup freshness

This lane must remain Store-specific and readable by operators without requiring engineering tooling.

## Backend Logging Contract

The control plane should emit structured JSON logs with a stable field contract.

Minimum fields:

- `timestamp`
- `level`
- `environment`
- `release_version`
- `request_id`
- `route`
- `method`
- `status_code`
- `duration_ms`
- `actor_id`
- `actor_email`
- `tenant_id`
- `branch_id`
- `device_id`
- `job_id`
- `error_class`

Rules:

- request logging and error logging must share the same `request_id`
- sensitive values must be scrubbed before logging
- logs should be safe to retain locally on the VM or ship later without redesign

## Internal Observability Surface

Add one platform-admin observability section instead of scattering operational cards through unrelated screens.

The internal observability API should be read-only and platform-admin scoped.

Suggested route family:

- `GET /v1/platform/observability/summary`
- `GET /v1/platform/observability/jobs`
- `GET /v1/platform/observability/runtime`
- `GET /v1/platform/observability/backups`

The initial summary should include:

- current environment and release version
- control-plane health
- worker configured/running posture
- dead-letter job counts
- recent failed job list
- hub/spoke runtime degradation summary
- offline continuity pending replay counts
- latest backup freshness and metadata

This is not intended to be a generic charting surface. It is an operator cockpit.

## Security Hardening Scope

### Rate Limiting

Apply first-pass rate limiting to:

- `/v1/auth/oidc/exchange`
- desktop activation and unlock routes
- provider webhook routes
- other sensitive write surfaces where brute-force or spam is realistic

For the current single-app-VM topology, an app-level in-memory limiter is acceptable for the first slice.

### Secure Headers

At minimum:

- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: no-referrer`
- `Content-Security-Policy` for the web apps
- `Strict-Transport-Security` in the deployed HTTPS proxy posture

### Secret Scrubbing

Never send to logs or Sentry:

- bearer tokens
- auth headers
- sync secrets
- PIN or local auth material
- taxpayer passwords
- billing provider secrets
- IRP provider credentials

### Alert Posture

Initial actionable alerts should cover:

- new backend exception class in production
- exception spike above a baseline
- repeated webhook signature failures
- dead-letter queue growth
- backup freshness breach
- worker health degraded
- runtime degradation spike

This task defines the alert posture and thresholds. Full hosted delivery automation can follow later.

## Dependency And Image Scan Baseline

Do not over-automate this slice.

For `CP-025`, the repo should provide:

- documented dependency-scan commands for Python and npm
- documented image-scan or container-scan baseline posture where relevant
- operator runbook guidance on how often to run them and what counts as a release blocker

CI enforcement belongs to `CP-026`.

## Release And Environment Rules

Observability and security settings must be environment-aware:

- separate Sentry DSNs for `staging` and `prod`, or disabled in `dev`
- separate release names per environment
- secure-header strictness should respect deployed HTTPS vs local dev
- alert thresholds should be tuned separately for `staging` and `prod`

No environment should silently share the same Sentry release identity if the deployed code differs.

## Implementation Boundaries

### Backend

Add:

- Sentry SDK configuration for FastAPI
- request-ID middleware
- JSON logging middleware
- secure-header middleware
- rate-limiter middleware or dependency support
- observability service and read-only routes

### Web Apps

Add:

- Sentry initialization in `apps/owner-web`
- Sentry initialization in `apps/platform-admin`
- environment guard so local dev and tests do not spam real telemetry

Do not add desktop Sentry in this first slice.

### Platform Admin

Add:

- one observability section
- summary tiles for deployment, jobs, runtime, and backups
- recent incident list based on backend observability summary

## Testing Expectations

Backend tests must cover:

- request ID generation and propagation
- observability summary routes
- rate-limit triggering on repeated auth/webhook requests
- secret scrubbing for logs/Sentry payload shaping
- secure headers on responses

Frontend tests must cover:

- observability section rendering
- Sentry initialization guard behavior

Runbook verification must cover:

- Sentry env values documented correctly
- scan commands documented and runnable

## Exit Criteria

`CP-025` is complete when:

- backend and web exceptions are visible in Sentry with useful context
- the platform-admin app exposes an internal observability surface for ops
- structured request and error logging exists with request IDs
- secure headers and basic rate limiting are enforced
- secret scrubbing is explicit
- alert and scan posture is documented for staging and prod
