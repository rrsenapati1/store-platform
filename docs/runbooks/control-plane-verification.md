# Control-Plane Verification Runbook

Updated: 2026-04-19

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

The deployed verifier now also:

- reads `GET /v1/system/security-controls`
- verifies secure headers on the health response
- sends bounded invalid auth-exchange requests until the deployed auth throttle triggers
- sends bounded invalid billing-webhook requests until the deployed webhook throttle triggers

Those probes are intentionally invalid but well-formed and should not mutate tenant data. They do consume a small number of rate-limit slots from the verifying client IP, so do not run them continuously from a shared operator workstation during incident response.

## Verify Environment Contract Drift

For staging or production before release certification:

```powershell
python services/control-plane-api/scripts/verify_environment_drift.py `
  --base-url https://control.store.korsenex.com `
  --expected-environment prod `
  --expected-release-version 2026.04.18 `
  --output-path docs\launch\evidence\prod-environment-drift.json
```

What this validates:

- `GET /v1/system/environment-contract`
- deployment environment, public base URL, and release version alignment
- JSON logging posture
- Sentry configuration and environment labeling
- object-storage bucket/prefix posture
- operations-worker batch and lease posture
- secure-header and rate-limit configuration values exposed by the control plane

The output is a machine-readable JSON report with:

- `status`
- `environment`
- `release_version`
- `checks`
- `failing_checks`
- `summary`

## Verify TLS Certificate Posture

For staging or production before release certification:

```powershell
python services/control-plane-api/scripts/verify_tls_posture.py `
  --base-url https://control.store.korsenex.com `
  --output-path docs\launch\evidence\prod-tls-posture.json `
  --min-days-remaining 30
```

What this validates:

- HTTPS is in use for the deployed control-plane base URL
- the certificate matches the requested hostname
- the certificate is not expired
- the remaining certificate validity window stays above the required minimum

The output is a machine-readable JSON report with:

- `status`
- `scheme`
- `host`
- `port`
- `protocol`
- `cipher`
- `days_remaining`
- `checks`
- `failing_checks`
- `summary`

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

## Run The Deployed Load Verification Lane

From repo root against a staging-style environment with dedicated fixture credentials:

```powershell
python services/control-plane-api/scripts/verify_deployed_load_posture.py `
  --base-url https://control.staging.store.korsenex.com `
  --expected-environment staging `
  --expected-release-version 2026.04.18 `
  --output-path docs\launch\evidence\staging-deployed-load.json `
  --admin-bearer-token <admin-token> `
  --branch-bearer-token <branch-token> `
  --tenant-id <tenant-id> `
  --branch-id <branch-id> `
  --product-id <product-id>
```

What this validates:

- `GET /v1/system/health`
- `GET /v1/platform/observability/summary`
- `POST /v1/tenants/{tenant_id}/branches/{branch_id}/checkout-price-preview`
- `GET /v1/tenants/{tenant_id}/branches/{branch_id}/management-dashboard`

The output is a machine-readable JSON report with:

- `status`
- `environment`
- `release_version`
- `concurrency`
- `iterations_per_worker`
- `scenario_results`
- `failing_scenarios`

This lane is intentionally bounded and staging-safe. It is meant to prove deployed-stack posture under concurrent HTTP traffic, not replace a dedicated long-running load-testing system.

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
- the deployed security verification status and throttle posture
- environment drift posture when a `--environment-drift-report` is supplied
- TLS posture when a `--tls-posture-report` is supplied
- SBOM posture when a `--sbom-report` is supplied
- license compliance posture when a `--license-compliance-report` is supplied
- release provenance posture when a `--provenance-report` is supplied
- deployed load posture when a `--deployed-load-report` is supplied

It can now also assemble a deterministic evidence bundle in the same run:

```powershell
python services/control-plane-api/scripts/generate_release_candidate_evidence.py `
  --base-url https://control.store.korsenex.com `
  --expected-environment prod `
  --expected-release-version 2026.04.19 `
  --output-path docs\launch\evidence\prod-rc-evidence.md `
  --certification-output-path docs\launch\evidence\prod-certification-report.json `
  --vulnerability-scan-report docs\launch\evidence\prod-vulnerability-report.json `
  --sbom-report docs\launch\evidence\prod-sbom-report.json `
  --sbom-artifact-dir docs\launch\evidence\prod-sbom-artifacts `
  --evidence-bundle-output-dir docs\launch\evidence\prod-evidence-bundle
```

That bundle contains:

- the release-candidate markdown evidence
- the saved certification JSON
- any supplied machine-readable evidence reports
- any supplied raw artifact directories such as SBOM output
- `bundle-manifest.json` with copied-path, hash, and count metadata
- `bundle-index.md` for quick operator inspection

If you already have the reports and only need to assemble the pack, use:

```powershell
python services/control-plane-api/scripts/build_release_evidence_bundle.py `
  --output-dir docs\launch\evidence\prod-evidence-bundle `
  --release-evidence docs\launch\evidence\prod-rc-evidence.md `
  --certification-report docs\launch\evidence\prod-certification-report.json `
  --vulnerability-scan-report docs\launch\evidence\prod-vulnerability-report.json `
  --sbom-report docs\launch\evidence\prod-sbom-report.json `
  --sbom-artifact-dir docs\launch\evidence\prod-sbom-artifacts
```

To archive that assembled pack into a versioned retained artifact with a publication manifest and rolling catalog, run:

```powershell
python services/control-plane-api/scripts/publish_release_evidence_bundle.py `
  --bundle-dir docs\launch\evidence\prod-evidence-bundle `
  --output-dir docs\launch\evidence\published `
  --environment prod `
  --release-version 2026.04.19
```

That publication step writes:

- `store-release-evidence-<environment>-<version>.tar.gz`
- `<environment>-<version>.publication.json`
- `release-evidence-catalog.json`

`generate_release_candidate_evidence.py` can also do bundle assembly and publication in one run with:

```powershell
python services/control-plane-api/scripts/generate_release_candidate_evidence.py `
  --base-url https://control.store.korsenex.com `
  --expected-environment prod `
  --expected-release-version 2026.04.19 `
  --output-path docs\launch\evidence\prod-rc-evidence.md `
  --certification-output-path docs\launch\evidence\prod-certification-report.json `
  --evidence-bundle-output-dir docs\launch\evidence\prod-evidence-bundle `
  --evidence-publication-output-dir docs\launch\evidence\published
```

If publication is requested and no explicit bundle directory is supplied, the script now creates an adjacent bundle directory automatically before publishing it.

To mirror the published pack into object storage for off-host retention, run:

```powershell
python services/control-plane-api/scripts/retain_release_evidence.py `
  --publication-dir docs\launch\evidence\published `
  --environment prod `
  --release-version 2026.04.19
```

That step uploads:

- the published evidence archive
- the publication manifest
- the rolling publication catalog
- a local `offsite-retention` manifest describing uploaded keys and hashes

`generate_release_candidate_evidence.py` can also trigger this after local publication when you pass:

```powershell
python services/control-plane-api/scripts/generate_release_candidate_evidence.py `
  --base-url https://control.store.korsenex.com `
  --expected-environment prod `
  --expected-release-version 2026.04.19 `
  --output-path docs\launch\evidence\prod-rc-evidence.md `
  --evidence-publication-output-dir docs\launch\evidence\published `
  --retain-evidence-offsite
```

This path is explicit on purpose. Off-host retention should never happen implicitly during ordinary local verification.

To verify that retained evidence is actually recoverable later, download it back from object storage and re-check the retained hashes:

```powershell
python services/control-plane-api/scripts/verify_retained_release_evidence.py `
  --environment prod `
  --release-version 2026.04.19 `
  --output-dir docs\launch\evidence\retrieved\prod-2026.04.19 `
  --report-path docs\launch\evidence\retrieved\prod-2026.04.19.retrieval-report.json
```

This retrieves:

- the retained archive
- the retained publication manifest
- the rolling publication catalog
- the offsite-retention manifest

Then it verifies:

- archive SHA-256 against the retention manifest
- publication-manifest SHA-256 and identity
- archive readability plus required evidence contents
- that the rolling catalog still contains the retained `environment + release_version` entry

`certify_release_candidate.py` can also consume a saved performance report directly:

```powershell
python services/control-plane-api/scripts/certify_release_candidate.py `
  --base-url https://control.store.korsenex.com `
  --expected-environment prod `
  --expected-release-version 2026.04.18 `
  --performance-report docs\launch\evidence\performance-launch-foundation.json
```

It can also consume a saved deployed-load report directly:

```powershell
python services/control-plane-api/scripts/certify_release_candidate.py `
  --base-url https://control.store.korsenex.com `
  --expected-environment prod `
  --expected-release-version 2026.04.18 `
  --deployed-load-report docs\launch\evidence\staging-deployed-load.json
```

It can also consume a saved environment-drift report directly:

```powershell
python services/control-plane-api/scripts/certify_release_candidate.py `
  --base-url https://control.store.korsenex.com `
  --expected-environment prod `
  --expected-release-version 2026.04.18 `
  --environment-drift-report docs\launch\evidence\prod-environment-drift.json
```

It can also consume a saved TLS posture report directly:

```powershell
python services/control-plane-api/scripts/certify_release_candidate.py `
  --base-url https://control.store.korsenex.com `
  --expected-environment prod `
  --expected-release-version 2026.04.18 `
  --tls-posture-report docs\launch\evidence\prod-tls-posture.json
```

It can also consume a saved SBOM report directly:

```powershell
python services/control-plane-api/scripts/certify_release_candidate.py `
  --base-url https://control.store.korsenex.com `
  --expected-environment prod `
  --expected-release-version 2026.04.18 `
  --sbom-report docs\launch\evidence\prod-sbom-report.json
```

It can also consume a saved license-compliance report directly:

```powershell
python services/control-plane-api/scripts/certify_release_candidate.py `
  --base-url https://control.store.korsenex.com `
  --expected-environment prod `
  --expected-release-version 2026.04.18 `
  --license-compliance-report docs\launch\evidence\prod-license-compliance-report.json
```

It can also consume a saved provenance report directly:

```powershell
python services/control-plane-api/scripts/certify_release_candidate.py `
  --base-url https://control.store.korsenex.com `
  --expected-environment prod `
  --expected-release-version 2026.04.18 `
  --provenance-report docs\launch\evidence\store-control-plane-2026.04.18.provenance.json
```

It can also consume a saved restore-drill report directly:

```powershell
python services/control-plane-api/scripts/certify_release_candidate.py `
  --base-url https://control.store.korsenex.com `
  --expected-environment prod `
  --expected-release-version 2026.04.18 `
  --restore-drill-report docs\launch\evidence\prod-restore-drill-report.json
```

## Run The Full V2 Release Gate

For the bounded final V2-009 operator path, prefer the one-shot orchestration command instead of assembling the hardening lane manually:

```powershell
python services/control-plane-api/scripts/run_release_gate.py `
  --base-url https://control.store.korsenex.com `
  --expected-environment prod `
  --expected-release-version 2026.04.19 `
  --release-owner ops@store.korsenex.com `
  --output-dir docs\launch\evidence\prod-release-gate `
  --admin-bearer-token <admin-token> `
  --branch-bearer-token <branch-token> `
  --tenant-id <tenant-id> `
  --branch-id <branch-id> `
  --product-id <product-id> `
  --dump-key control-plane/prod/postgres-backups/<backup>/store-control-plane-prod.dump `
  --metadata-key control-plane/prod/postgres-backups/<backup>/metadata.json `
  --target-database-url postgresql+asyncpg://store:secret@restore-host:5432/store_control_plane_restore `
  --image-ref store-control-plane-api:prod `
  --image-ref postgres:16 `
  --retain-evidence-offsite `
  --verify-retained-evidence
```

That path now:

- runs vulnerability, alert, drift, TLS, SBOM, license, deployed-load, rollback, and restore-drill evidence
- packages the control-plane release and reuses that manifest for provenance and rollback verification
- generates strict certification that includes deployed-load, rollback, and restore-drill posture
- assembles and publishes the evidence bundle
- optionally performs off-host retention and post-retention retrieval verification
- writes `release-gate-report.json` as the final machine-readable result for the V2-009 hardening lane

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
- If environment drift verification fails, treat the release candidate as blocked until deployed configuration matches the declared environment contract.
- If TLS posture verification fails, treat the release candidate as blocked until certificate validity or hostname posture is corrected.
- If SBOM generation fails, treat the release candidate as blocked until machine-readable component inventory can be regenerated successfully.
- If license compliance fails, treat the release candidate as blocked until the policy issue is fixed or explicitly excepted with current approval.
- If release provenance is missing or failed, treat the release candidate as blocked until the bundle has source-attested provenance evidence again.
- If deployed load verification fails, treat the staged release as not scale-ready until the failing HTTP scenarios are understood and reverified.
- If deployed security verification fails, treat the release candidate as blocked until the secure-header or throttle mismatch is resolved.
- If restore-drill verification fails, treat recovery posture as unproven and block the strict final release gate.
- If retained evidence retrieval verification fails, treat off-host evidence retention as unproven until the stored pack can be downloaded and revalidated successfully.
- If `run_release_gate.py` finishes blocked, treat its `release-gate-report.json` as the final authority for the bounded V2-009 gate even if some lower-level reports were individually green.

## Cleanup

When finished:

```powershell
docker compose -f compose.yaml down -v
```
