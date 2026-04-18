# Control-Plane Backup And Restore

Updated: 2026-04-18

## Scope

This runbook covers:

- scheduled Postgres backups to managed object storage
- manual backup invocation
- restore drills
- production restore safety checks

## Backup Contract

Required metadata per artifact:

- deployment environment
- release version
- Alembic head
- object-storage bucket and keys
- creation timestamp
- retention window

The backup script writes a local metadata manifest and uploads both the dump and manifest to object storage.

## Daily Backup

The app VM should install and enable:

- `store-control-plane-backup.service`
- `store-control-plane-backup.timer`

Manual run:

```powershell
python scripts/backup_postgres.py --output-dir C:\store-control-plane\backups
```

## Retention

Recommended starting policy:

- `staging`
  - keep 14 days
- `prod`
  - keep 30 days

Longer legal or accounting retention can be layered on later, but the first public-release slice must at least preserve operational recovery history.

## Restore Drill

Run restore drills on staging or on an isolated restore target only.

Low-level artifact validation:

```powershell
python scripts/restore_postgres.py `
  --dump-key control-plane/prod/postgres-backups/20260414T103045Z/store-control-plane-prod-20260414T103045Z.dump `
  --metadata-key control-plane/prod/postgres-backups/20260414T103045Z/metadata.json `
  --target-database-url postgresql+asyncpg://store:secret@restore-db.internal:5432/store_control_plane_restore `
  --dry-run
```

Low-level real restore:

```powershell
python scripts/restore_postgres.py `
  --dump-key control-plane/prod/postgres-backups/20260414T103045Z/store-control-plane-prod-20260414T103045Z.dump `
  --metadata-key control-plane/prod/postgres-backups/20260414T103045Z/metadata.json `
  --target-database-url postgresql+asyncpg://store:secret@restore-db.internal:5432/store_control_plane_restore `
  --yes
```

Operational restore drill with mandatory health verification:

```powershell
python scripts/run_restore_drill.py `
  --dump-key control-plane/prod/postgres-backups/20260414T103045Z/store-control-plane-prod-20260414T103045Z.dump `
  --metadata-key control-plane/prod/postgres-backups/20260414T103045Z/metadata.json `
  --target-database-url postgresql+asyncpg://store:secret@restore-db.internal:5432/store_control_plane_restore `
  --output-path C:\store-control-plane\restore-drills\20260418-prod-restore-drill.json `
  --yes
```

Operational restore drill with bounded smoke verification:

```powershell
python scripts/run_restore_drill.py `
  --dump-key control-plane/prod/postgres-backups/20260414T103045Z/store-control-plane-prod-20260414T103045Z.dump `
  --metadata-key control-plane/prod/postgres-backups/20260414T103045Z/metadata.json `
  --target-database-url postgresql+asyncpg://store:secret@restore-db.internal:5432/store_control_plane_restore `
  --output-path C:\store-control-plane\restore-drills\20260418-prod-restore-drill-smoke.json `
  --verify-smoke `
  --yes
```

The restore-drill CLI writes a JSON artifact with:

- restore status
- source bucket and artifact keys
- redacted target database identifier
- restored manifest environment, release version, and Alembic head
- health verification result
- optional smoke verification result
- explicit failure reason when the drill fails

Treat that JSON file as the recovery evidence artifact. Console output is only a summary.

## RPO And RTO

Initial target posture:

- `RPO`: 24 hours
- `RTO`: 4 hours

If the actual environment cannot meet those targets, treat that as a release blocker for public production use.
