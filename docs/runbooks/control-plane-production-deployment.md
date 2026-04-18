# Control-Plane Production Deployment

Updated: 2026-04-19

## Topology

Each shared environment uses:

- `app VM`
  - nginx
  - `store-control-plane-api`
  - `store-control-plane-worker`
- `db VM`
  - Postgres only
- managed object storage
  - Postgres backups
  - restore-drill artifacts
  - Store Desktop update manifests and installers

Use separate VMs, secrets, Postgres data, and object-storage prefixes for `staging` and `prod`.

## Required Inputs

On the app VM:

- release bundle already copied to the target host
  - `CP-026` release automation produces `store-control-plane-<version>.tar.gz` as a GitHub artifact or GitHub Release attachment; download that artifact before starting the deployment runbook
- `/etc/store-control-plane/app.env`
- web-build environment for owner-web and platform-admin if those apps are built from the same deployment pipeline
- systemd units based on:
  - `services/control-plane-api/ops/systemd/store-control-plane-api.service.example`
  - `services/control-plane-api/ops/systemd/store-control-plane-worker.service.example`
  - `services/control-plane-api/ops/systemd/store-control-plane-backup.service.example`
  - `services/control-plane-api/ops/systemd/store-control-plane-backup.timer.example`
- nginx config based on:
  - `services/control-plane-api/ops/nginx/store-control-plane.conf.example`

On the DB VM:

- `/etc/store-control-plane/db.env`
- Postgres bound to a private network address or loopback-only tunnel
- inbound firewall allowing only the app VM and operator IPs

## Security And Observability Inputs

At minimum, set these in `/etc/store-control-plane/app.env` for `staging` and `prod`:

- `STORE_CONTROL_PLANE_LOG_FORMAT=json`
- `STORE_CONTROL_PLANE_SENTRY_DSN`
- `STORE_CONTROL_PLANE_SENTRY_TRACES_SAMPLE_RATE`
- `STORE_CONTROL_PLANE_SENTRY_ENVIRONMENT`
- `STORE_CONTROL_PLANE_RATE_LIMIT_WINDOW_SECONDS`
- `STORE_CONTROL_PLANE_RATE_LIMIT_AUTH_REQUESTS`
- `STORE_CONTROL_PLANE_RATE_LIMIT_ACTIVATION_REQUESTS`
- `STORE_CONTROL_PLANE_RATE_LIMIT_WEBHOOK_REQUESTS`
- `STORE_CONTROL_PLANE_SECURE_HEADERS_ENABLED=true`
- `STORE_CONTROL_PLANE_SECURE_HEADERS_HSTS_ENABLED=true`
- `STORE_CONTROL_PLANE_SECURE_HEADERS_CSP`

If owner-web and platform-admin are built for the same environment, also set:

- `VITE_SENTRY_DSN`
- `VITE_DEPLOYMENT_ENVIRONMENT`
- `VITE_RELEASE_VERSION`
- `VITE_SENTRY_TRACES_SAMPLE_RATE`

Do not reuse the same Sentry DSN between `staging` and `prod` unless you intentionally want both environments merged into one project.

## Release Order

Always deploy:

1. `staging`
2. verify staging
3. `prod`

Do not skip staging for schema or secrets changes.

## Artifact Source

After `CP-026`, the expected control-plane release bundle source is:

- GitHub Actions artifact from `.github/workflows/release-artifacts.yml`, or
- GitHub Release attachment on a `v*` tag

GitHub only builds the artifact. Operators still copy it to the app VM and run the deployment commands locally on that VM.

## App-VM Deployment Steps

From the app VM inside the extracted release:

```powershell
python scripts/backup_postgres.py --output-dir C:\store-control-plane\backups
python scripts/deploy_control_plane_release.py --release-bundle C:\store-control-plane\releases\store-control-plane-2026.04.14.tar.gz --yes
python scripts/verify_deployed_control_plane.py --base-url https://control.store.korsenex.com --expected-environment prod --expected-release-version 2026.04.14
```

What the deploy script is expected to enforce:

1. pre-migration backup
2. `alembic upgrade head`
3. API restart
4. worker restart

## Post-Deploy Verification

Required checks after deployment:

1. `GET /v1/system/health` returns `status=ok`
2. `GET /v1/system/authority-boundary` returns the expected cutover posture
3. `GET /v1/platform/observability/summary` returns the expected environment, release version, queue posture, and backup metadata
4. live API responses include secure headers
5. owner sign-in still works
6. packaged desktop activation or unlock against the environment still works
7. worker service is active and logs show clean startup
8. JSON request logs are being emitted on the app VM
9. desktop release channel still points at the matching environment

## Recovery Evidence

Before certifying a staging or production release candidate, attach recent restore-drill evidence where possible:

- run `python scripts/run_restore_drill.py ... --output-path <restore-drill-report.json> --yes`
- keep the JSON restore-drill report with the release notes or evidence bundle
- if release evidence is generated with `generate_release_candidate_evidence.py`, pass `--restore-drill-report <restore-drill-report.json>` so recovery posture is recorded alongside verification and performance evidence

Also keep the deployed security verification result from:

- `python scripts/verify_deployed_control_plane.py --base-url ... --expected-environment ... --expected-release-version ...`

That verification now includes secure-header checks and bounded live auth/webhook throttle probes, and release certification should block if those controls fail.

## Environment Drift Evidence

Before certifying a staging or production release candidate, generate environment-contract drift evidence:

```powershell
python scripts/verify_environment_drift.py `
  --base-url https://control.store.korsenex.com `
  --expected-environment prod `
  --expected-release-version 2026.04.18 `
  --output-path docs/launch/evidence/prod-environment-drift.json
```

Keep that JSON report with the release notes or evidence bundle.

If release evidence is generated with `generate_release_candidate_evidence.py`, also pass:

- `--environment-drift-report <environment-drift-report.json>`

If release certification is run with `certify_release_candidate.py`, also pass:

- `--environment-drift-report <environment-drift-report.json>`

Release certification should now block if the environment-drift report is missing or failed.

## TLS Evidence

Before certifying a staging or production release candidate, generate TLS certificate posture evidence:

```powershell
python scripts/verify_tls_posture.py `
  --base-url https://control.store.korsenex.com `
  --output-path docs/launch/evidence/prod-tls-posture.json `
  --min-days-remaining 30
```

Keep that JSON report with the release notes or evidence bundle.

If release evidence is generated with `generate_release_candidate_evidence.py`, also pass:

- `--tls-posture-report <tls-posture-report.json>`

If release certification is run with `certify_release_candidate.py`, also pass:

- `--tls-posture-report <tls-posture-report.json>`

Release certification should now block if the TLS posture report is missing or failed.

## SBOM Evidence

Before certifying a staging or production release candidate, generate SBOM evidence:

```powershell
python scripts/generate_sbom_bundle.py `
  --output-path docs/launch/evidence/prod-sbom-report.json `
  --raw-output-dir docs/launch/evidence/prod-sbom-artifacts `
  --image-ref store-control-plane-api:prod `
  --image-ref postgres:16
```

Keep that JSON report and the raw CycloneDX artifacts with the release notes or evidence bundle.

If release evidence is generated with `generate_release_candidate_evidence.py`, also pass:

- `--sbom-report <sbom-report.json>`

If release certification is run with `certify_release_candidate.py`, also pass:

- `--sbom-report <sbom-report.json>`

Release certification should now block if the SBOM report is missing or failed.

## License Compliance Evidence

Before certifying a staging or production release candidate, generate license-compliance evidence from the SBOM bundle:

```powershell
python scripts/run_license_compliance.py `
  --sbom-report docs/launch/evidence/prod-sbom-report.json `
  --output-path docs/launch/evidence/prod-license-compliance-report.json `
  --policy-path docs/launch/security/license-policy.json `
  --exceptions-path docs/launch/security/license-exceptions.json
```

Keep that JSON report with the release notes or evidence bundle.

If release evidence is generated with `generate_release_candidate_evidence.py`, also pass:

- `--license-compliance-report <license-compliance-report.json>`

If release certification is run with `certify_release_candidate.py`, also pass:

- `--license-compliance-report <license-compliance-report.json>`

Release certification should now block if the license-compliance report is missing or failed.

## Release Provenance Evidence

Before certifying a staging or production release candidate, keep the provenance sidecar produced with the release bundle:

- `store-control-plane-<version>.provenance.json`

`scripts/package-control-plane-release.mjs` now emits that file beside:

- `store-control-plane-<version>.tar.gz`
- `store-control-plane-<version>.manifest.json`

The provenance sidecar records:

- release version and bundle name
- archive and manifest SHA-256 hashes
- source commit, tree, ref, and origin remote
- whether the source worktree was clean at packaging time

If release evidence is generated with `generate_release_candidate_evidence.py`, also pass:

- `--provenance-report <provenance-report.json>`

If release certification is run with `certify_release_candidate.py`, also pass:

- `--provenance-report <provenance-report.json>`

Release certification should now block if the provenance report is missing or failed.

## Operational Alert Evidence

Before certifying a staging or production release candidate, generate operational alert posture evidence:

```powershell
python scripts/verify_operational_alert_posture.py `
  --base-url https://control.store.korsenex.com `
  --expected-environment prod `
  --expected-release-version 2026.04.18 `
  --output-path docs/launch/evidence/prod-operational-alerts.json
```

Keep that JSON report with the release notes or evidence bundle.

If release evidence is generated with `generate_release_candidate_evidence.py`, also pass:

- `--operational-alert-report <operational-alerts.json>`

If release certification is run with `certify_release_candidate.py`, also pass:

- `--operational-alert-report <operational-alerts.json>`

Release certification should now block if the operational alert report is missing or failed.

## Deployed Load Evidence

Before certifying a staging-style release candidate, generate deployed load posture evidence:

```powershell
python scripts/verify_deployed_load_posture.py `
  --base-url https://control.staging.store.korsenex.com `
  --expected-environment staging `
  --expected-release-version 2026.04.18 `
  --output-path docs/launch/evidence/staging-deployed-load.json `
  --admin-bearer-token <admin-token> `
  --branch-bearer-token <branch-token> `
  --tenant-id <tenant-id> `
  --branch-id <branch-id> `
  --product-id <product-id>
```

Keep that JSON report with the release notes or evidence bundle.

If release evidence is generated with `generate_release_candidate_evidence.py`, also pass:

- `--deployed-load-report <deployed-load-report.json>`

If release certification is run with `certify_release_candidate.py`, also pass:

- `--deployed-load-report <deployed-load-report.json>`

This gate is optional when no deployed-load report is supplied, but any supplied failed report should block approval.

## Rollback Evidence

Before certifying a staging or production release candidate, verify the intended rollback target:

```powershell
python scripts/verify_release_rollback.py `
  --base-url https://control.staging.store.korsenex.com `
  --target-bundle-manifest C:\store-control-plane\releases\store-control-plane-2026.04.17.manifest.json `
  --output-path docs/launch/evidence/staging-rollback-report.json
```

Keep that JSON report with the release notes or evidence bundle.

If release evidence is generated with `generate_release_candidate_evidence.py`, also pass:

- `--rollback-report <rollback-report.json>`

If release certification is run with `certify_release_candidate.py`, also pass:

- `--rollback-report <rollback-report.json>`

This verifier approves only schema-compatible app-layer rollback. If the target bundle `alembic_head` differs from the deployed schema head, treat rollback as `restore_required` and use the backup/restore path instead of a simple app rollback.

## Vulnerability Scan Evidence

Before certifying a staging or production release candidate, generate a normalized vulnerability report:

```powershell
python scripts/run_vulnerability_scans.py `
  --output-path docs/launch/evidence/prod-vulnerability-report.json `
  --exceptions-path docs/launch/security/vulnerability-exceptions.json `
  --image-ref store-control-plane-api:prod `
  --image-ref postgres:16
```

Keep that JSON report with the release notes or evidence bundle.

If release evidence is generated with `generate_release_candidate_evidence.py`, also pass:

- `--vulnerability-scan-report <vulnerability-report.json>`

If release certification is run with `certify_release_candidate.py`, also pass:

- `--vulnerability-scan-report <vulnerability-report.json>`

Release certification should now block if the vulnerability report is missing or failed.

## Evidence Bundle Assembly

Before handing a release candidate to human sign-off, assemble one evidence pack instead of passing around individual files:

```powershell
python services/control-plane-api/scripts/generate_release_candidate_evidence.py `
  --base-url https://control.store.korsenex.com `
  --expected-environment prod `
  --expected-release-version 2026.04.19 `
  --output-path docs/launch/evidence/prod-rc-evidence.md `
  --certification-output-path docs/launch/evidence/prod-certification-report.json `
  --vulnerability-scan-report docs/launch/evidence/prod-vulnerability-report.json `
  --sbom-report docs/launch/evidence/prod-sbom-report.json `
  --sbom-artifact-dir docs/launch/evidence/prod-sbom-artifacts `
  --evidence-bundle-output-dir docs/launch/evidence/prod-evidence-bundle
```

The bundle directory is deterministic and contains:

- the release-candidate evidence markdown
- the certification JSON result
- every supplied machine-readable evidence report
- copied raw artifact directories such as SBOM output
- `bundle-manifest.json` with hashes and copied-path metadata
- `bundle-index.md` as the operator-facing table of contents

If the markdown evidence already exists, you can also assemble the bundle separately with:

```powershell
python services/control-plane-api/scripts/build_release_evidence_bundle.py `
  --output-dir docs/launch/evidence/prod-evidence-bundle `
  --release-evidence docs/launch/evidence/prod-rc-evidence.md `
  --certification-report docs/launch/evidence/prod-certification-report.json `
  --vulnerability-scan-report docs/launch/evidence/prod-vulnerability-report.json `
  --sbom-report docs/launch/evidence/prod-sbom-report.json `
  --sbom-artifact-dir docs/launch/evidence/prod-sbom-artifacts
```

Treat `bundle-manifest.json` as the authoritative inventory of what evidence was actually packaged for approval.

## Evidence Publication And Retention

After the evidence bundle is assembled, publish it into a retained release artifact pack:

```powershell
python services/control-plane-api/scripts/publish_release_evidence_bundle.py `
  --bundle-dir docs/launch/evidence/prod-evidence-bundle `
  --output-dir docs/launch/evidence/published `
  --environment prod `
  --release-version 2026.04.19
```

This produces:

- `store-release-evidence-prod-2026.04.19.tar.gz`
- `prod-2026.04.19.publication.json`
- `release-evidence-catalog.json`

The publication manifest is the operator-visible retention record for:

- source bundle directory and bundle-manifest hash
- certification status at publication time
- archive SHA-256 and archive size
- published environment and release version

The catalog is the rolling local index of retained evidence packs. Re-publishing the same `environment + release_version` replaces that catalog entry instead of creating duplicates.

This remains an operator-controlled step. The current repo still does not push published evidence packs to object storage or GitHub Releases automatically.

## Off-Host Evidence Retention

After local publication, mirror the retained evidence pack into object storage:

```powershell
python services/control-plane-api/scripts/retain_release_evidence.py `
  --publication-dir docs/launch/evidence/published `
  --environment prod `
  --release-version 2026.04.19
```

This uploads:

- `store-release-evidence-prod-2026.04.19.tar.gz`
- `prod-2026.04.19.publication.json`
- `release-evidence-catalog.json`
- `prod-2026.04.19.offsite-retention.json`

The offsite-retention manifest is the operator-visible proof of what was uploaded, including:

- bucket and object keys
- release version and environment
- certification status at retention time
- SHA-256 hashes for the archive, publication manifest, and catalog

Use this step when the evidence pack must survive workstation loss or needs to be reviewed from a shared durable store.

## Retained Evidence Retrieval Verification

After off-host retention, periodically prove the stored evidence pack is still recoverable:

```powershell
python services/control-plane-api/scripts/verify_retained_release_evidence.py `
  --environment prod `
  --release-version 2026.04.19 `
  --output-dir docs/launch/evidence/retrieved/prod-2026.04.19 `
  --report-path docs/launch/evidence/retrieved/prod-2026.04.19.retrieval-report.json
```

This verification is intentionally separate from upload. It downloads the retained archive and manifests, validates the immutable archive and publication hashes from the offsite-retention manifest, checks the archive can still be opened, and confirms the rolling publication catalog still includes the retained release entry.

## Failure Posture

- If pre-migration backup fails: stop deployment.
- If Alembic fails: do not restart services on the new release.
- If API or worker restart fails: revert the release bundle path and investigate before re-running migrations.
- If post-deploy verification fails after migrations succeed: prefer restore-forward fixes; use DB restore only when the release cannot be recovered safely.
- If retained evidence retrieval verification fails: treat the retained evidence trail as incomplete until object-storage access, integrity, and catalog visibility are re-established.
