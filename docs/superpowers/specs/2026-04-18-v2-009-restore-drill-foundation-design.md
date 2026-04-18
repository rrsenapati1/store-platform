# V2-009 Restore-Drill Automation Foundation Design

## Goal

Add the first real recovery-evidence slice for `V2-009` by turning the existing backup and restore scripts into a repeatable restore-drill workflow that:

- restores a selected backup into an explicit target database
- boots the control plane against that restored target
- verifies post-restore health, with optional bounded smoke validation
- writes a machine-readable drill report for release and operations evidence

This slice is about proving recoverability, not just documenting it.

## Why This Is The Right Next V2-009 Slice

The repo already has:

- `backup_postgres.py`
- `restore_postgres.py`
- backup and restore runbooks
- tests for backup artifact creation and restore safety checks

What is still missing is the actual recovery proof path:

- no script currently composes restore plus application boot verification
- no structured restore-drill artifact exists for release evidence
- no bounded way exists to prove a backup is restorable into a working control plane

That makes staged restore-drill automation the strongest next hardening slice after the new performance-validation foundation.

## Recommended Approach

Build one focused restore-drill seam on top of the current ops layer instead of redesigning backup or restore itself.

That seam should include:

- an ops-level restore-drill orchestration module
- one CLI script that runs the drill end-to-end
- a JSON drill report artifact
- runbook updates describing the new contract

The restore drill should reuse:

- the existing restore plan and safety checks
- the existing control-plane health boundary
- optional bounded smoke verification from the current verification module

## Scope

Included:

- explicit restore-drill orchestration
- post-restore control-plane boot and health verification
- optional bounded smoke verification
- machine-readable drill report JSON
- tests for success and failure cases
- runbook updates

Not included:

- whole-VM or whole-environment provisioning
- scheduled restore automation across all environments
- full disaster failover orchestration
- production traffic replay
- redesign of backup metadata or object-storage layout

## Architecture

### 1. Restore-Drill Ops Module

Add a new ops-level module:

- `store_control_plane/ops/postgres_restore_drill.py`

Its responsibility is to orchestrate:

1. restore artifact selection
2. restore execution
3. post-restore app verification
4. report construction

It should not own backup creation and should not duplicate `run_postgres_restore(...)`.

### 2. Runner Flow

The restore drill should run in this order:

1. accept explicit `dump_key`
2. accept explicit `metadata_key`
3. accept explicit `target_database_url`
4. call `run_postgres_restore(...)`
5. boot a temporary control-plane app against the restored database
6. run mandatory health verification
7. optionally run bounded smoke verification
8. write a JSON drill report
9. exit non-zero on failure

The “optional smoke verification” part matters because not every routine drill needs the full smoke path, but every real drill must at least prove the restored database can boot a healthy app.

### 3. Drill Report Shape

The drill report should be a JSON artifact with this structure:

- `status`
  - `passed`
  - `failed`
- `started_at`
- `finished_at`
- `duration_seconds`
- `source`
  - `bucket`
  - `dump_key`
  - `metadata_key`
- `target`
  - redacted target database identifier or URL
- `restored_manifest`
  - `environment`
  - `release_version`
  - `alembic_head`
- `health_result`
- `verification_result`
- `failure_reason`

This report is the key product of the slice. The CLI output can be brief, but the JSON artifact is what later release evidence should consume.

### 4. Verification Posture

For the first slice:

- health verification is mandatory
- bounded smoke verification is optional

Recommended behavior:

- `--verify-smoke` opt-in flag on the CLI
- default fast drill does restore + health only
- stronger proof drill adds smoke verification

This keeps the automation useful for frequent checks without making every drill as expensive as a full control-plane verification run.

## CLI Boundary

Add:

- `services/control-plane-api/scripts/run_restore_drill.py`

Inputs:

- `--dump-key`
- `--metadata-key`
- `--target-database-url`
- `--output-path`
- `--allow-environment-mismatch`
- `--verify-smoke`
- `--yes` or equivalent destructive acknowledgement

Behavior:

- compose restore + verification
- write JSON artifact
- print concise result summary
- return non-zero on failure

## Error Handling

Failure cases should remain explicit and structured.

Examples:

- environment mismatch during restore
- restore command failure
- restored app health failure
- optional smoke verification failure

In all of those cases:

- the drill report should still be written when possible
- `status` should be `failed`
- `failure_reason` should be explicit

No silent fallback and no “manual inspection required” as the default outcome.

## Testing

Add focused backend tests for:

- successful restore drill with passing health verification
- blocked environment mismatch without override
- restore completes but health verification fails
- restore completes but smoke verification fails
- report JSON includes expected source, target, and restored-manifest fields

These tests should stay at the orchestration level, using injected fake storage, fake restore execution, and fake verification functions. The slice does not need a real Postgres restore in unit tests.

## Docs

Update:

- `docs/runbooks/control-plane-backup-restore.md`
- `docs/runbooks/control-plane-production-deployment.md`

The backup/restore runbook should explain how to run and interpret the drill.

The production deployment runbook should mention the drill as recovery evidence for staged or pre-release operations where appropriate.

## Success Criteria

This slice is complete when:

- the repo can run a real restore drill from selected backup artifacts
- the drill proves the restored database can boot a healthy control plane
- optional smoke verification is supported
- a machine-readable drill report is written
- the runbooks document the path
- focused verification passes
