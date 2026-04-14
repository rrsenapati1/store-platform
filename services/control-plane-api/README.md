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

## Development Fallback

`stub` mode exists only for tests and isolated local development.

Production and shared development environments should use `jwks` mode with real Korsenex configuration.
