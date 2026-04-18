# V2-009 Deployed Load Verification Foundation Implementation Plan

Date: 2026-04-18
Task: `V2-009`
Spec: [2026-04-18-v2-009-deployed-load-verification-foundation-design.md](/d:/codes/projects/store/.worktrees/korsenex-v2-009-deployed-load-foundation/docs/superpowers/specs/2026-04-18-v2-009-deployed-load-verification-foundation-design.md)

## Goal

Add a repo-owned deployed load verifier that exercises bounded concurrent HTTP traffic against staging-style environments, writes machine-readable evidence, and threads that evidence into release reporting and certification.

## Architecture

Add a small deployed-load domain module and CLI instead of expanding the local performance harness directly:

- `store_control_plane/deployed_load_verification.py`
- `scripts/verify_deployed_load_posture.py`

Then extend:

- `generate_release_candidate_evidence.py`
- `certify_release_candidate.py`

So deployed load posture becomes another optional but first-class release evidence lane.

## Task 1: Add failing deployed-load domain tests

Create:

- `services/control-plane-api/tests/test_deployed_load_verification.py`

Cover:

- scenario aggregation pass/fail
- report building
- failing scenario collection
- summary generation

Run and confirm failure:

```powershell
python -m pytest services/control-plane-api/tests/test_deployed_load_verification.py -q
```

## Task 2: Implement deployed-load domain module

Create:

- `services/control-plane-api/store_control_plane/deployed_load_verification.py`

Add:

- scenario result model helpers
- budget evaluation
- report serialization
- summary formatting

Re-run Task 1 tests until green.

## Task 3: Add failing CLI tests

Create:

- `services/control-plane-api/tests/test_verify_deployed_load_posture.py`

Cover:

- JSON report writing
- non-zero exit on failed posture
- fixture validation

Run and confirm failure.

## Task 4: Implement deployed-load verifier CLI

Create:

- `services/control-plane-api/scripts/verify_deployed_load_posture.py`

Requirements:

- accept base URL, expected environment, expected release version
- accept required fixture IDs and bearer token
- run bounded concurrent HTTP scenarios
- write one JSON report
- exit non-zero on failed posture

Verify:

```powershell
python -m pytest services/control-plane-api/tests/test_verify_deployed_load_posture.py -q
python services/control-plane-api/scripts/verify_deployed_load_posture.py --help
```

## Task 5: Add failing release-evidence and certification tests

Extend:

- `services/control-plane-api/tests/test_release_candidate_evidence_generation.py`
- `services/control-plane-api/tests/test_release_candidate_certification.py`

Expect:

- deployed load evidence section renders
- certification exposes `deployed_load_verified`
- failed deployed load report blocks when supplied

Run and confirm failure.

## Task 6: Integrate release evidence and certification

Extend:

- `services/control-plane-api/scripts/generate_release_candidate_evidence.py`
- `services/control-plane-api/scripts/certify_release_candidate.py`

Add:

- optional `--deployed-load-report`
- evidence rendering
- certification gate propagation

Re-run focused tests until green.

## Task 7: Update docs and verify

Update:

- `docs/runbooks/control-plane-verification.md`
- `docs/runbooks/control-plane-production-deployment.md`
- `docs/WORKLOG.md`

Run:

```powershell
python -m pytest `
  services/control-plane-api/tests/test_deployed_load_verification.py `
  services/control-plane-api/tests/test_verify_deployed_load_posture.py `
  services/control-plane-api/tests/test_release_candidate_evidence_generation.py `
  services/control-plane-api/tests/test_release_candidate_certification.py -q

python services/control-plane-api/scripts/verify_deployed_load_posture.py --help
git -c core.safecrlf=false diff --check
```

## Completion

When verified:

1. commit the branch
2. merge to root `main`
3. re-run the focused merged-state verification
4. push `origin/main`
5. remove the finished worktree and branch
6. continue to the next `V2-009` slice automatically
