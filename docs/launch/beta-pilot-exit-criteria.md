# Beta Pilot Exit Criteria

Updated: 2026-04-19

Use this document to decide whether beta/pilot operation is strong enough to move into public release.

For `V2-010`, record the pilot and sign-off inputs in [v2-launch-readiness-manifest.template.json](./v2-launch-readiness-manifest.template.json) and validate them with:

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
  --target-database-url postgresql+asyncpg://store:***@db.internal:5432/store_restore
```

## Beta Exit Conditions

All of these should be true before public launch is approved:

- at least one real tenant/branch flow completed using the current release candidate
- packaged Store Desktop install and activation worked on real hardware
- owner-web onboarding and first-branch setup were completed successfully
- no unresolved severity-1 blockers remain
- any accepted severity-2 issues have explicit owner, workaround, and follow-up target
- billing/commercial lifecycle posture has been exercised enough to prove grace/suspension handling is understandable and supportable

## Minimum Beta Evidence

Record at least:

- tenant identifier
- branch identifier
- release version used
- desktop release profile used
- installer path/channel used
- onboarding outcome
- branch runtime outcome
- print/scanner/runtime notes if relevant
- offline continuity or replay notes if exercised
- operator who ran the pilot
- runtime hardware validation outcome
- whether the pilot is being accepted as `passed` or held for follow-up

## Failure Conditions

Do not exit beta if:

- onboarding fails unpredictably
- device claim/activation fails without a clear support path
- commercial lifecycle state blocks expected customer behavior incorrectly
- runtime continuity/replay behavior is unclear enough that support cannot route incidents reliably
- release/update publication is not repeatable

## Sign-Off Record

- Beta owner:
- Date:
- Candidate version:
- Result:
  - `pass`
  - `hold`
- Notes:

In the repo-owned `V2-010` flow, these same values should also appear in the launch-readiness manifest so the beta exit decision can be validated and bundled together with the strict release-gate evidence.
