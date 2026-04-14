# Store Control Plane API

This service is the side-by-side Milestone 1 control plane for Store.

It owns:

- Korsenex-backed actor resolution
- tenant onboarding
- branch setup
- tenant and branch memberships
- control-plane audit events
- supplier, receiving, and inventory control foundations
- billing, returns, exchanges, and runtime print queue foundations

It does not own backend authority for offline runtime continuity or the final sync boundary.

The control plane publishes the current authority contract at `GET /v1/system/authority-boundary`, including migrated domains, legacy-only domains, and the current legacy write mode.

## Local Development

1. Create a virtual environment and install dependencies:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and fill in the real Korsenex values.
   - `STORE_CONTROL_PLANE_PLATFORM_ADMIN_EMAILS` accepts a comma-separated list such as `admin@store.local,ops@store.local`.
   - `STORE_CONTROL_PLANE_LEGACY_WRITE_MODE` defaults to `shadow` and should be switched to `cutover` only during an explicit legacy-authority cutover window.
   - `STORE_CONTROL_PLANE_DEPLOYMENT_ENVIRONMENT`, `STORE_CONTROL_PLANE_PUBLIC_BASE_URL`, and `STORE_CONTROL_PLANE_RELEASE_VERSION` should stay `dev`-oriented locally.
   - object-storage variables are optional for local development unless you are explicitly testing backup or release-artifact flows.

3. Start Postgres:

```powershell
docker compose -f compose.yaml up -d postgres
```

4. Apply migrations:

```powershell
.venv\Scripts\Activate.ps1
$env:STORE_CONTROL_PLANE_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:54321/store_control_plane"
alembic upgrade head
```

5. Start the API:

```powershell
.venv\Scripts\Activate.ps1
uvicorn store_control_plane.main:create_app --factory --reload --app-dir .
```

6. Start the operations worker:

```powershell
.venv\Scripts\Activate.ps1
python scripts/run_operations_worker.py
```

For a single batch run during local debugging:

```powershell
.venv\Scripts\Activate.ps1
python scripts/run_operations_worker.py --once
```

## IRP Configuration

`CP-020` adds a real provider-backed GST or IRP path. Production deploys must configure the global solution-provider settings in `.env`, and each branch must save its own taxpayer IRP profile from owner web before queued B2B exports can submit successfully.

Environment variables:

- `STORE_CONTROL_PLANE_COMPLIANCE_SECRET_KEY`
  - Fernet-compatible key used to encrypt branch taxpayer passwords at rest.
- `STORE_CONTROL_PLANE_COMPLIANCE_IRP_MODE`
  - `disabled`, `stub`, or `iris_direct`
- `STORE_CONTROL_PLANE_COMPLIANCE_IRP_CLIENT_ID`
- `STORE_CONTROL_PLANE_COMPLIANCE_IRP_CLIENT_SECRET`
- `STORE_CONTROL_PLANE_COMPLIANCE_IRP_AUTH_URL`
- `STORE_CONTROL_PLANE_COMPLIANCE_IRP_GENERATE_IRN_URL`
- `STORE_CONTROL_PLANE_COMPLIANCE_IRP_GET_BY_DOCUMENT_URL`
- `STORE_CONTROL_PLANE_COMPLIANCE_IRP_GET_GSTIN_DETAILS_URL`
- `STORE_CONTROL_PLANE_COMPLIANCE_IRP_PUBLIC_KEY_PEM`
- `STORE_CONTROL_PLANE_COMPLIANCE_IRP_TIMEOUT_SECONDS`

Notes:

- `stub` mode is for tests and isolated local development only.
- `iris_direct` expects solution-provider endpoints and client credentials to already be provisioned.
- Branch taxpayer credentials are configured from the owner-web compliance section and are never returned to the UI after save.

## Runbook-Grade Verification

From `services/control-plane-api/` after Postgres is up and `.env` is configured:

```powershell
.venv\Scripts\Activate.ps1
$env:STORE_CONTROL_PLANE_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:54321/store_control_plane"
python scripts/verify_control_plane.py
```

The verifier runs:

- `alembic upgrade head`
- control-plane backend pytest suite
- `platform-admin`, `owner-web`, and `store-desktop` app-flow tests
- workspace `typecheck` and `build`
- a real control-plane smoke path across auth, onboarding, procurement, receiving, sale creation, runtime heartbeat, and print queue handling

The script manages its pytest temp root under `%LOCALAPPDATA%\\store-control-plane-verification` so backend verification is not coupled to the repo mount.
The smoke portion is safe to rerun against the same Postgres database because it now uses a unique tenant slug per verification run.

Detailed operator steps live in [docs/runbooks/control-plane-verification.md](../../docs/runbooks/control-plane-verification.md).
Legacy cutover steps live in [docs/runbooks/legacy-authority-cutover.md](../../docs/runbooks/legacy-authority-cutover.md).

## Staging And Production Environment Files

`CP-024` introduces host-local, non-secret environment templates for self-managed staging and production VMs:

- `ops/env/app.staging.env.example`
- `ops/env/app.prod.env.example`
- `ops/env/db.staging.env.example`
- `ops/env/db.prod.env.example`

These files are templates only. Real secrets must be injected from operator-managed files or systemd environment files on the target hosts and must never be committed back into the repo.

## Self-Managed Deployment Scripts

`CP-024` adds operator-facing scripts for staged deployments and recovery:

- `python scripts/backup_postgres.py --help`
- `python scripts/restore_postgres.py --help`
- `python scripts/deploy_control_plane_release.py --help`
- `python scripts/verify_deployed_control_plane.py --help`

Production deployment guidance lives in [docs/runbooks/control-plane-production-deployment.md](../../docs/runbooks/control-plane-production-deployment.md).
Backup and restore guidance lives in [docs/runbooks/control-plane-backup-restore.md](../../docs/runbooks/control-plane-backup-restore.md).

## Security And Observability Configuration

`CP-025` adds backend observability and first-pass request hardening knobs.

Backend environment variables:

- `STORE_CONTROL_PLANE_SENTRY_DSN`
- `STORE_CONTROL_PLANE_SENTRY_TRACES_SAMPLE_RATE`
- `STORE_CONTROL_PLANE_SENTRY_ENVIRONMENT`
- `STORE_CONTROL_PLANE_LOG_FORMAT`
  - `plain` for local development, `json` for deployed environments
- `STORE_CONTROL_PLANE_RATE_LIMIT_WINDOW_SECONDS`
- `STORE_CONTROL_PLANE_RATE_LIMIT_AUTH_REQUESTS`
- `STORE_CONTROL_PLANE_RATE_LIMIT_ACTIVATION_REQUESTS`
- `STORE_CONTROL_PLANE_RATE_LIMIT_WEBHOOK_REQUESTS`
- `STORE_CONTROL_PLANE_SECURE_HEADERS_ENABLED`
- `STORE_CONTROL_PLANE_SECURE_HEADERS_HSTS_ENABLED`
- `STORE_CONTROL_PLANE_SECURE_HEADERS_CSP`

Recommended starting posture:

- `dev`
  - no Sentry DSN
  - `STORE_CONTROL_PLANE_LOG_FORMAT=plain`
- `staging`
  - staging-specific Sentry DSN or project
  - `STORE_CONTROL_PLANE_LOG_FORMAT=json`
- `prod`
  - prod-specific Sentry DSN or project
  - `STORE_CONTROL_PLANE_LOG_FORMAT=json`

## Development Fallback

`stub` mode exists only for tests and isolated local development.

Production and shared development environments should use `jwks` mode with real Korsenex configuration.
