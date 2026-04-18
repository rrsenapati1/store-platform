# V2-009 Rollback Verification Foundation Design

Date: 2026-04-18
Task: `V2-009`
Status: Drafted

## Goal

Add the first repo-owned rollback verification lane so `V2-009` can produce machine-readable evidence that a staged release can be reverted safely to a specific earlier control-plane bundle.

This slice is about proving rollback eligibility, not automating a live downgrade.

## Why This Is The Right Next Slice

`V2-009` already has evidence for:

- local hot-path performance
- deployed HTTP load posture
- restore drills
- deployed security verification
- vulnerability scanning
- operational alert posture

What it still lacks is a bounded answer to:

- which earlier release bundle is the intended rollback target
- whether that bundle is schema-compatible with the currently deployed environment
- where rollback posture is recorded for release approval

Right now rollback is only a runbook note. That is not enough for enterprise launch hardening.

## Chosen Model

The accepted model is:

- release bundles carry an explicit manifest
- deployed verification exposes the current `alembic_head`
- one rollback verifier compares deployed posture to a target bundle
- one JSON rollback report feeds release evidence and certification

This keeps rollback verification honest without pretending the repo can safely perform arbitrary database downgrades.

## Scope

### In Scope

- control-plane release bundle manifest generation
- deployed system-health exposure of `alembic_head`
- rollback-verification CLI
- machine-readable rollback report
- release-evidence rendering
- release-certification gate when rollback evidence is supplied
- runbook updates

### Out Of Scope

- automatic live rollback execution
- database downgrade automation
- multi-hop rollback planning
- desktop rollback orchestration
- production auto-revert triggers

## Safety Boundary

The first slice should approve rollback only for `app-layer rollback` where the target bundle is schema-compatible with the deployed database.

For this slice, that means:

- target bundle `alembic_head == deployed alembic_head`

If the heads differ, rollback verification must fail and direct the operator toward:

- restore-forward fixes, or
- backup restore procedures

This matches the existing runbook posture that app-only rollback is not always safe after schema movement.

## Release Bundle Manifest

Control-plane bundle packaging should emit a manifest with at least:

- `release_version`
- `alembic_head`
- `built_at`
- `bundle_name`

The manifest should be staged into the release archive and also emitted as a sidecar JSON file near the archive so operators and automation do not need to unpack the full tarball just to inspect rollback metadata.

## Deployed State Boundary

The deployed control-plane verification path should expose:

- `environment`
- `release_version`
- `alembic_head`

The cleanest boundary is extending `GET /v1/system/health` so the deployed verifier can reuse the current health path instead of adding a second deployment-state endpoint.

## Rollback Report Contract

The rollback verifier should write one JSON report shaped like:

- `status`
  - `passed`
  - `failed`
- `environment`
- `current_release_version`
- `current_alembic_head`
- `target_release_version`
- `target_alembic_head`
- `rollback_mode`
  - `app_only`
  - `restore_required`
- `generated_at`
- `summary`
- `failure_reason | null`

## Verification Rules

The first rollback verifier should:

1. verify the deployed environment through the existing deployed verifier
2. load the target bundle manifest
3. compare deployed `release_version` to target `release_version`
4. compare deployed `alembic_head` to target `alembic_head`
5. return:
   - `passed` with `rollback_mode=app_only` when the target release is older and the schema heads match
   - `failed` with `rollback_mode=restore_required` when schema heads differ

It should also fail when:

- the target bundle manifest is missing
- the target bundle version matches the currently deployed version
- the target bundle version is newer than the deployed version

## Release Integration

Extend:

- [generate_release_candidate_evidence.py](/d:/codes/projects/store/services/control-plane-api/scripts/generate_release_candidate_evidence.py)
- [certify_release_candidate.py](/d:/codes/projects/store/services/control-plane-api/scripts/certify_release_candidate.py)

So they can consume:

- an optional rollback verification report

Release evidence should render:

- overall rollback status
- current release/head
- target release/head
- rollback mode
- failure reason

Release certification should expose:

- `rollback_verified`

This gate should stay optional for compatibility until `V2-010` makes it part of the final launch evidence set.

## Testing

The slice should cover:

- bundle manifest generation tests
- system health schema and route tests for `alembic_head`
- rollback verifier tests for:
  - compatible rollback
  - mismatched head
  - missing manifest
  - invalid target version
- release-evidence rendering
- release-certification gate behavior

## Success Criteria

This slice is complete when:

- control-plane release bundles carry explicit manifest metadata
- deployed health exposes the current schema head
- the repo can generate machine-readable rollback verification evidence
- release evidence can render rollback posture
- release certification can gate on rollback posture when supplied
- docs explain that this is a schema-compatible rollback verifier, not a DB downgrade engine
