# Security And Observability Operations

Updated: 2026-04-15

## Purpose

`CP-025` adds the first production diagnostics and request-hardening layer for Store:

- backend structured request logging with request IDs
- backend Sentry exception reporting
- owner-web and platform-admin Sentry bootstrapping
- platform-admin observability summary
- secure response headers
- rate limiting on auth, desktop activation or unlock, and billing webhooks

This runbook describes how operators should wire, verify, and respond to that posture.

## Environment Wiring

### Control-plane API

Set these on the app VM in `/etc/store-control-plane/app.env`:

- `STORE_CONTROL_PLANE_SENTRY_DSN`
- `STORE_CONTROL_PLANE_SENTRY_TRACES_SAMPLE_RATE`
- `STORE_CONTROL_PLANE_SENTRY_ENVIRONMENT`
- `STORE_CONTROL_PLANE_LOG_FORMAT`
- `STORE_CONTROL_PLANE_RATE_LIMIT_WINDOW_SECONDS`
- `STORE_CONTROL_PLANE_RATE_LIMIT_AUTH_REQUESTS`
- `STORE_CONTROL_PLANE_RATE_LIMIT_ACTIVATION_REQUESTS`
- `STORE_CONTROL_PLANE_RATE_LIMIT_WEBHOOK_REQUESTS`
- `STORE_CONTROL_PLANE_SECURE_HEADERS_ENABLED`
- `STORE_CONTROL_PLANE_SECURE_HEADERS_HSTS_ENABLED`
- `STORE_CONTROL_PLANE_SECURE_HEADERS_CSP`

Recommended starting values:

- `staging`
  - `STORE_CONTROL_PLANE_LOG_FORMAT=json`
  - staging-only Sentry DSN or Sentry project
  - `STORE_CONTROL_PLANE_SENTRY_ENVIRONMENT=staging`
  - `STORE_CONTROL_PLANE_SECURE_HEADERS_HSTS_ENABLED=true` only if HTTPS is already enforced
- `prod`
  - `STORE_CONTROL_PLANE_LOG_FORMAT=json`
  - prod-only Sentry DSN or Sentry project
  - `STORE_CONTROL_PLANE_SENTRY_ENVIRONMENT=prod`
  - `STORE_CONTROL_PLANE_SECURE_HEADERS_HSTS_ENABLED=true`

### Owner-Web And Platform-Admin

Set these at web-build time for `apps/owner-web` and `apps/platform-admin`:

- `VITE_SENTRY_DSN`
- `VITE_DEPLOYMENT_ENVIRONMENT`
- `VITE_RELEASE_VERSION`
- `VITE_SENTRY_TRACES_SAMPLE_RATE`

The web apps intentionally do not initialize Sentry when:

- `VITE_SENTRY_DSN` is empty
- Vite is running in `DEV`
- the environment mode is `test`

Use separate DSNs or separate Sentry projects for `staging` and `prod`.

## What The System Enforces

### Structured logging

Every request should emit a structured record with:

- `request_id`
- route, method, status code, duration
- release and environment
- actor, tenant, branch, device, and job context when available

Secrets must not appear in logs. Auth headers, tokens, PIN material, and provider secrets are scrubbed before structured logging and before Sentry submission.

### Secure headers

When `STORE_CONTROL_PLANE_SECURE_HEADERS_ENABLED=true`, responses include:

- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: no-referrer`
- `Content-Security-Policy` from `STORE_CONTROL_PLANE_SECURE_HEADERS_CSP`

When `STORE_CONTROL_PLANE_SECURE_HEADERS_HSTS_ENABLED=true`, responses also include:

- `Strict-Transport-Security`

Enable HSTS only after HTTPS is enforced end-to-end.

### Rate limiting

The current bounded limiter applies to:

- `/v1/auth/oidc/exchange`
- `/v1/auth/store-desktop/*`
- `/v1/billing/webhooks/*`

When exceeded, the API returns:

- HTTP `429`
- JSON detail `Rate limit exceeded`
- `Retry-After` header

This first slice is intentionally simple. It is meant to slow abuse on public auth and webhook surfaces before a later dedicated infra or WAF pass.

## Platform Observability Summary

Platform admins can inspect:

- `GET /v1/platform/observability/summary`

The summary includes:

- current environment and release version
- system health
- operations queue posture
- recent retryable or dead-letter jobs
- branch runtime degradation summary
- backup freshness metadata

Use the platform-admin observability section as the operator cockpit for:

- dead-letter growth
- degraded branch runtime posture
- stale or missing backups
- repeated sync or continuity conflicts

## Alert Thresholds

Start with these thresholds:

- backend: any new Sentry issue in `prod`
- operations queue: `dead_letter_count > 0`
- operations queue: retryable failures growing across repeated checks
- runtime: any degraded branch count increase that persists for more than 15 minutes
- backup: no successful backup metadata for more than 26 hours
- webhooks: repeated signature or rate-limit failures within one window

These are release-blocking when they remain unresolved in `prod`.

## Incident Flow

### 1. Backend or frontend exception spike

1. Check Sentry for the issue group, release, and environment.
2. Correlate with the `request_id`, tenant, branch, actor, and device tags.
3. Cross-check structured logs on the app VM for the same `request_id`.
4. If the error is release-specific, stop rollout or revert before continuing feature work.

### 2. Auth or webhook abuse posture

1. Check structured logs for repeated `429` responses on auth or webhook routes.
2. Confirm secure headers are still present on live responses.
3. If limits are too low for a legitimate provider or traffic pattern, adjust only the affected threshold.
4. Do not disable rate limiting globally as a first response.

### 3. Queue or runtime degradation

1. Open platform-admin observability.
2. Inspect recent failure jobs and degraded branches.
3. If dead-letter growth is present, fix the underlying worker or provider issue before mass retries.
4. If branch runtime degradation is local to one branch, inspect hub connectivity and offline continuity posture before touching the global worker stack.

### 4. Backup freshness breach

1. Check `/v1/platform/observability/summary` backup status.
2. Confirm object-storage access and the backup timer or service status on the app VM.
3. Run the backup flow manually only after confirming Postgres health.
4. If a manual backup cannot complete, treat deployment changes as blocked until backup posture is restored.

## Verification Checklist

After environment changes or release deployment:

1. `GET /v1/system/health`
2. `GET /v1/platform/observability/summary`
3. confirm secure headers on a live API response
4. confirm JSON request logs are being written on the app VM
5. confirm Sentry receives testable errors only in the intended environment and project
6. confirm platform-admin renders the observability section without API errors

## Guardrails

- Never send access tokens, taxpayer credentials, billing secrets, or PIN material to Sentry.
- Never enable HSTS on a non-HTTPS environment.
- Never point `staging` and `prod` at the same Sentry DSN unless you are intentionally collapsing those environments.
- Treat observability drift as a deployment issue, not as optional polish.
