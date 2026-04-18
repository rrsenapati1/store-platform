# V2-009 Rollback Verification Foundation Implementation Plan

Date: 2026-04-18
Task: `V2-009`
Spec: [2026-04-18-v2-009-rollback-verification-foundation-design.md](/d:/codes/projects/store/.worktrees/korsenex-v2-009-rollback-verification-foundation/docs/superpowers/specs/2026-04-18-v2-009-rollback-verification-foundation-design.md)

## Goal

Add bundle-manifest-backed rollback verification evidence so a staged release can prove whether rollback to an earlier control-plane bundle is schema-compatible.

## Architecture

Keep the slice bounded around existing seams:

- extend the control-plane bundle builder to emit a manifest
- extend system health with `alembic_head`
- add a new rollback-verification module and CLI
- thread the resulting JSON report into release evidence and certification

## Task 1: Add failing bundle-manifest tests

Extend:

- `scripts/package-control-plane-release.test.mjs`

Expect:

- manifest sidecar JSON is written
- manifest is included inside the tarball
- manifest records `release_version`, `bundle_name`, and `alembic_head`

Run and confirm failure.

## Task 2: Implement bundle manifest generation

Modify:

- `scripts/package-control-plane-release.mjs`

Add:

- manifest file creation
- sidecar JSON emission
- staging into the release archive

Re-run the packaging tests until green.

## Task 3: Add failing system-health tests

Extend:

- `services/control-plane-api/tests/test_system_routes.py`

Expect:

- `GET /v1/system/health` includes `alembic_head`

Run and confirm failure.

## Task 4: Implement deployed schema-head exposure

Modify:

- `services/control-plane-api/store_control_plane/schemas/system.py`
- relevant system service/route implementation

Use the existing `resolve_alembic_head()` helper instead of inventing a second source of truth.

## Task 5: Add failing rollback-verifier tests

Create:

- `services/control-plane-api/tests/test_rollback_verification.py`
- `services/control-plane-api/tests/test_verify_release_rollback.py`

Cover:

- schema-compatible rollback passes
- mismatched head fails with `restore_required`
- missing manifest fails
- invalid target release ordering fails
- CLI writes JSON and exits non-zero on failure

Run and confirm failure.

## Task 6: Implement rollback-verification module and CLI

Create:

- `services/control-plane-api/store_control_plane/rollback_verification.py`
- `services/control-plane-api/scripts/verify_release_rollback.py`

Requirements:

- read target bundle manifest
- reuse deployed verification
- compare release versions and schema heads
- write one JSON report

## Task 7: Add failing release integration tests

Extend:

- `services/control-plane-api/tests/test_release_candidate_evidence_generation.py`
- `services/control-plane-api/tests/test_release_candidate_certification.py`

Expect:

- rollback evidence section renders
- certification exposes `rollback_verified`
- supplied failed rollback report blocks approval

Run and confirm failure.

## Task 8: Integrate release evidence and certification

Modify:

- `services/control-plane-api/scripts/generate_release_candidate_evidence.py`
- `services/control-plane-api/scripts/certify_release_candidate.py`

Add:

- optional `--rollback-report`
- rollback rendering
- rollback gate propagation

## Task 9: Update docs and verify

Update:

- `docs/runbooks/control-plane-production-deployment.md`
- `docs/runbooks/github-actions-release-automation.md`
- `docs/WORKLOG.md`

Run:

```powershell
python -m pytest `
  services/control-plane-api/tests/test_system_routes.py `
  services/control-plane-api/tests/test_rollback_verification.py `
  services/control-plane-api/tests/test_verify_release_rollback.py `
  services/control-plane-api/tests/test_release_candidate_evidence_generation.py `
  services/control-plane-api/tests/test_release_candidate_certification.py -q

node --test scripts/package-control-plane-release.test.mjs
python services/control-plane-api/scripts/verify_release_rollback.py --help
git -c core.safecrlf=false diff --check
```

## Completion

When verified:

1. commit the branch
2. merge to root `main`
3. rerun the focused merged-state verification
4. push `origin/main`
5. remove the finished worktree and branch
6. continue to the next `V2-009` slice automatically
