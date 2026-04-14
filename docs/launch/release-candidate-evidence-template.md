# Release Candidate Evidence Template

Updated: 2026-04-15

Use this template to capture the evidence for a specific release candidate.

If you want the repo to pre-fill the verification sections, run:

```powershell
python services/control-plane-api/scripts/generate_release_candidate_evidence.py `
  --base-url https://control.store.korsenex.com `
  --expected-environment prod `
  --expected-release-version <version> `
  --release-owner ops@store.korsenex.com
```

## Candidate Metadata

- Version:
- Environment:
- Release owner:
- Date:

## Verification Evidence

- Local verification command:
  - result:
- Deployed verification command:
  - result:
- Release-candidate certification command:
  - result:

## Authority / Cutover Evidence

- `legacy_write_mode`:
- `legacy_remaining_domains`:
- legacy cutover validation notes:

## Release Artifact Evidence

- control-plane bundle:
- owner-web artifact:
- platform-admin artifact:
- Store Desktop installer/signature:

## Beta Evidence

- pilot tenant/branch:
- outcome:
- known issues:

## Operational Notes

- backup posture:
- observability posture:
- support readiness:

## Final Decision

- Status:
  - `approved`
  - `blocked`
- Sign-off owner:
- Notes:
