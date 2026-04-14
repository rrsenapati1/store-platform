# Go-Live Runbook

Updated: 2026-04-15

This runbook ties together the final launch gate for Store. It does not replace the detailed deployment/security/support runbooks; it tells release operators what order to use them in.

## Inputs

Before go-live:

- release artifacts exist for the target version
- launch readiness checklist is prepared
- beta exit criteria have been reviewed
- legacy-read acceptance register is still accurate

## Recommended Order

1. Confirm release artifacts and release version.
2. Run local verification for the release candidate.
3. Deploy to staging and verify staging.
4. Run the release-candidate certification command against staging.
5. Review beta evidence and known issues.
6. Deploy to production.
7. Run deployed verification and release-candidate certification against production.
8. Complete launch-readiness checklist sign-off.

## Commands

### Local verification

```powershell
python services/control-plane-api/scripts/verify_control_plane.py
```

### Deployed verification

```powershell
python services/control-plane-api/scripts/verify_deployed_control_plane.py `
  --base-url https://control.store.korsenex.com `
  --expected-environment prod `
  --expected-release-version <version>
```

### Release-candidate certification

```powershell
python services/control-plane-api/scripts/certify_release_candidate.py `
  --base-url https://control.store.korsenex.com `
  --expected-environment prod `
  --expected-release-version <version>
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

- the certification script returns `approved`
- the beta evidence is recorded
- the launch checklist sign-offs are completed

If any of those are missing, the correct status is `hold`, not `go`.
