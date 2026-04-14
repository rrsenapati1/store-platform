# Control-Plane Production Deployment

Updated: 2026-04-14

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
- `/etc/store-control-plane/app.env`
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

## Release Order

Always deploy:

1. `staging`
2. verify staging
3. `prod`

Do not skip staging for schema or secrets changes.

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
3. owner sign-in still works
4. packaged desktop activation or unlock against the environment still works
5. worker service is active and logs show clean startup
6. desktop release channel still points at the matching environment

## Failure Posture

- If pre-migration backup fails: stop deployment.
- If Alembic fails: do not restart services on the new release.
- If API or worker restart fails: revert the release bundle path and investigate before re-running migrations.
- If post-deploy verification fails after migrations succeed: prefer restore-forward fixes; use DB restore only when the release cannot be recovered safely.
