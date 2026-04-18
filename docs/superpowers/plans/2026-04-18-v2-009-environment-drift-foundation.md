# V2-009 Environment Drift Verification Foundation Implementation Plan

Date: 2026-04-18
Task: `V2-009`
Spec: [2026-04-18-v2-009-environment-drift-foundation-design.md](/d:/codes/projects/store/.worktrees/korsenex-v2-009-environment-drift-foundation/docs/superpowers/specs/2026-04-18-v2-009-environment-drift-foundation-design.md)

## Goal

Add a control-plane-owned environment contract plus a deployed drift verifier so shared environment posture can be recorded as machine-readable release evidence.

## Architecture

Keep the slice bounded around current seams:

- add one new system route for effective environment contract
- add one drift-evaluation module
- add one deployed verifier CLI
- thread the resulting report into release evidence and certification

## Task 1: Add failing environment-contract route tests

Extend:

- `services/control-plane-api/tests/test_system_routes.py`

Expect:

- `GET /v1/system/environment-contract` returns effective deployment posture:
  - environment
  - base URL
  - log format
  - sentry posture
  - object-storage posture
  - worker posture
  - security controls

Run and confirm failure.

## Task 2: Implement environment-contract read model

Modify:

- `services/control-plane-api/store_control_plane/schemas/system.py`
- `services/control-plane-api/store_control_plane/routes/system.py`
- any helper needed under `services/`

Reuse current settings instead of inventing a second config source.

## Task 3: Add failing drift-evaluator and CLI tests

Create:

- `services/control-plane-api/tests/test_environment_drift.py`
- `services/control-plane-api/tests/test_verify_environment_drift.py`

Cover:

- shared-env pass case
- drift failures for:
  - plain logs
  - missing Sentry
  - missing object storage
  - disabled HSTS
- CLI JSON report output
- non-zero exit on failed posture

Run and confirm failure.

## Task 4: Implement drift module and verifier CLI

Create:

- `services/control-plane-api/store_control_plane/environment_drift.py`
- `services/control-plane-api/scripts/verify_environment_drift.py`

Requirements:

- fetch system health and environment-contract state
- evaluate drift against repo-owned expected profiles
- write one JSON report
- exit non-zero on failed posture

## Task 5: Add failing release integration tests

Extend:

- `services/control-plane-api/tests/test_release_candidate_evidence_generation.py`
- `services/control-plane-api/tests/test_release_candidate_certification.py`

Expect:

- drift evidence section renders
- certification exposes `environment_drift_verified`
- supplied failed drift report blocks approval

Run and confirm failure.

## Task 6: Integrate release evidence and certification

Modify:

- `services/control-plane-api/scripts/generate_release_candidate_evidence.py`
- `services/control-plane-api/scripts/certify_release_candidate.py`

Add:

- optional `--environment-drift-report`
- drift rendering
- drift gate propagation

## Task 7: Update docs and verify

Update:

- `docs/runbooks/control-plane-production-deployment.md`
- `docs/runbooks/control-plane-verification.md`
- `docs/WORKLOG.md`

Run:

```powershell
python -m pytest `
  services/control-plane-api/tests/test_system_routes.py `
  services/control-plane-api/tests/test_environment_drift.py `
  services/control-plane-api/tests/test_verify_environment_drift.py `
  services/control-plane-api/tests/test_release_candidate_evidence_generation.py `
  services/control-plane-api/tests/test_release_candidate_certification.py -q

python services/control-plane-api/scripts/verify_environment_drift.py --help
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
