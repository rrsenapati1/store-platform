# Control-Plane Verification Runbook

Updated: 2026-04-14

## Purpose

This runbook is the repeatable verification path for the new Store control plane. It is the required gate before claiming that Postgres migrations, backend behavior, and the current control-plane-driven app flows are healthy together.

## Preconditions

1. `services/control-plane-api/.env` exists and is configured.
2. Dependencies are installed for:
   - `services/control-plane-api/`
   - repo-root npm workspaces
3. Docker is available locally.

## Start Postgres

From `services/control-plane-api/`:

```powershell
docker compose -f compose.yaml up -d postgres
```

Wait for the container healthcheck to pass before continuing.

## Run the Verification Stack

From `services/control-plane-api/`:

```powershell
.venv\Scripts\Activate.ps1
$env:STORE_CONTROL_PLANE_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:54321/store_control_plane"
python scripts/verify_control_plane.py
```

What the verifier does:

1. Applies `alembic upgrade head`.
2. Runs `pytest tests -q` for the control-plane backend.
3. Runs:
   - `npm run test --workspace @store/platform-admin`
   - `npm run test --workspace @store/owner-web`
   - `npm run test --workspace @store/store-desktop`
4. Runs repo-root `npm run typecheck`.
5. Runs repo-root `npm run build`.
6. Executes a real HTTP smoke path through:
   - platform-admin auth exchange and tenant creation
   - owner invite acceptance and branch setup
   - catalog, supplier, purchase order, approval, and goods receipt
   - runtime device registration
   - cashier checkout
   - runtime heartbeat
   - invoice print queueing
   - sale return creation
   - credit-note print queue failure handling

The script stores pytest temp state under `%LOCALAPPDATA%\\store-control-plane-verification` so Windows temp cleanup does not depend on the repo mount.
The live smoke path uses a unique tenant slug on each run, so rerunning the verifier does not require an empty Postgres database.

## Verify A Deployed Environment

For staging or production after rollout:

```powershell
python services/control-plane-api/scripts/verify_deployed_control_plane.py `
  --base-url https://control.store.korsenex.com `
  --expected-environment prod `
  --expected-release-version 2026.04.14
```

Optional:

- pass `--bearer-token <token>` if you also want the script to verify `/v1/auth/me`

## Run The Launch-Foundation Performance Validation Lane

From `services/control-plane-api/` or repo root with the database URL available:

```powershell
python scripts/validate_performance_foundation.py `
  --database-url postgresql+asyncpg://postgres:postgres@localhost:54321/store_control_plane `
  --iterations 3 `
  --output-path ..\..\docs\launch\evidence\performance-launch-foundation.json
```

What this validates:

- checkout price preview
- direct sale creation
- checkout payment-session creation
- offline sale replay
- reviewed receiving creation
- restock task lifecycle
- reviewed stock count lifecycle
- branch reporting dashboard read

The output is a machine-readable JSON report with:

- `status`
- `scenario_set`
- `scenario_results`
- `passing_scenarios`
- `failing_scenarios`
- `total_iterations`
- `total_failures`

This lane is the first bounded performance gate for the broadened V2 suite. It is intentionally an in-process validation harness, not an internet-scale external load test.

## Release Evidence Integration

`generate_release_candidate_evidence.py` now runs the performance-validation lane by default unless you explicitly pass:

```powershell
python services/control-plane-api/scripts/generate_release_candidate_evidence.py `
  --base-url https://control.store.korsenex.com `
  --expected-environment prod `
  --expected-release-version 2026.04.18 `
  --skip-performance-validation
```

If you do not skip it, the evidence markdown records:

- the performance validation command
- the result status
- a compact scenario summary

`certify_release_candidate.py` can also consume a saved performance report directly:

```powershell
python services/control-plane-api/scripts/certify_release_candidate.py `
  --base-url https://control.store.korsenex.com `
  --expected-environment prod `
  --expected-release-version 2026.04.18 `
  --performance-report docs\launch\evidence\performance-launch-foundation.json
```

## Expected Success Signal

The script exits `0` and prints a JSON summary with:

- `goods_receipt_number`
- `sale_invoice_number`
- `queued_print_job_count`
- `heartbeat_job_count`
- `inventory_stock_on_hand`
- `ledger_entry_types`

## Failure Handling

- If Alembic fails, stop and fix the migration/database path before trusting any app-flow result.
- If backend pytest fails, treat the backend as unhealthy even if the smoke passes.
- If app-flow tests fail, do not mark the current UI/runtime surface healthy.
- If the smoke fails after tests pass, treat it as an integration regression between control-plane modules.
- If performance validation fails, treat the release evidence as incomplete until the failing scenarios are understood and the budgets are re-met or intentionally revised.

## Cleanup

When finished:

```powershell
docker compose -f compose.yaml down -v
```
