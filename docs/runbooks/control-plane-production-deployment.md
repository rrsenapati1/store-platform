# Control-Plane Production Deployment

Updated: 2026-04-18

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

## Failure Posture

- If pre-migration backup fails: stop deployment.
- If Alembic fails: do not restart services on the new release.
- If API or worker restart fails: revert the release bundle path and investigate before re-running migrations.
- If post-deploy verification fails after migrations succeed: prefer restore-forward fixes; use DB restore only when the release cannot be recovered safely.
