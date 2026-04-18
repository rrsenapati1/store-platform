# Go-Live Runbook

Updated: 2026-04-19

This runbook ties together the final launch gate for Store. It does not replace the detailed deployment/security/support runbooks; it tells release operators what order to use them in.

## Inputs

Before go-live:

- release artifacts exist for the target version
- launch-readiness manifest is prepared
- launch-readiness checklist is prepared
- beta exit criteria have been reviewed
- legacy-read acceptance register is still accurate

## Recommended Order

1. Confirm release artifacts and release version.
2. Record or refresh the beta/sign-off manifest for the candidate.
3. Run the one-shot `V2` launch gate against staging.
4. Review the launch-readiness report, known issues, and sign-offs.
5. Deploy to production.
6. Run the one-shot `V2` launch gate against production.
7. Complete launch-readiness checklist sign-off.

The older two-step path of `run_release_gate.py` plus `build_launch_readiness_report.py` still works and remains useful for debugging, but `V2-010` promotes the one-shot launch gate as the primary operator path.

## Commands

### One-shot V2 launch gate

```powershell
python services/control-plane-api/scripts/run_v2_launch_gate.py `
  --base-url https://control.store.korsenex.com `
  --expected-environment prod `
  --expected-release-version <version> `
  --release-owner ops@store.korsenex.com `
  --output-dir D:/ops/v2-launch-gate/<version> `
  --launch-manifest docs/launch/v2-launch-readiness-manifest.json `
  --admin-bearer-token <admin-token> `
  --branch-bearer-token <branch-token> `
  --tenant-id <tenant-id> `
  --branch-id <branch-id> `
  --product-id <product-id> `
  --dump-key control-plane/prod/postgres-backups/restore.dump `
  --metadata-key control-plane/prod/postgres-backups/metadata.json `
  --target-database-url postgresql+asyncpg://store:***@db.internal:5432/store_restore `
  --retain-evidence-offsite `
  --verify-retained-evidence
```

### Technical gate only

```powershell
python services/control-plane-api/scripts/run_release_gate.py `
  --base-url https://control.store.korsenex.com `
  --expected-environment prod `
  --expected-release-version <version> `
  --release-owner ops@store.korsenex.com `
  --output-dir D:/ops/release-gate/<version> `
  --admin-bearer-token <admin-token> `
  --branch-bearer-token <branch-token> `
  --tenant-id <tenant-id> `
  --branch-id <branch-id> `
  --product-id <product-id> `
  --dump-key control-plane/prod/postgres-backups/restore.dump `
  --metadata-key control-plane/prod/postgres-backups/metadata.json `
  --target-database-url postgresql+asyncpg://store:***@db.internal:5432/store_restore
```

### Launch-readiness report only

```powershell
python services/control-plane-api/scripts/build_launch_readiness_report.py `
  --launch-manifest docs/launch/v2-launch-readiness-manifest.json `
  --release-gate-report D:/ops/release-gate/<version>/release-gate-report.json `
  --output-path docs/launch/evidence/prod-<version>-launch-readiness.json `
  --markdown-output-path docs/launch/evidence/prod-<version>-launch-readiness.md
```

## Supporting Runbooks

- deployment:
  - [../runbooks/control-plane-production-deployment.md](../runbooks/control-plane-production-deployment.md)
- backup/restore:
  - [../runbooks/control-plane-backup-restore.md](../runbooks/control-plane-backup-restore.md)
- security/observability:
  - [../runbooks/security-observability-operations.md](../runbooks/security-observability-operations.md)
- desktop packaging/distribution:
  - [../runbooks/store-desktop-packaging-distribution.md](../runbooks/store-desktop-packaging-distribution.md)
- support readiness:
  - [../support/support-triage-playbook.md](../support/support-triage-playbook.md)
  - [../support/escalation-matrix.md](../support/escalation-matrix.md)

## Honest Launch Gate Rule

Do not mark the release candidate operationally approved until:

- the one-shot `V2` launch gate reports `ready`
- the launch checklist sign-offs are completed

If any of those are missing, the correct status is `hold`, not `go`.
