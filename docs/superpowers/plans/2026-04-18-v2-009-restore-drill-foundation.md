# V2-009 Restore-Drill Foundation Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a repeatable Postgres restore-drill workflow that restores selected backup artifacts into an explicit target database, proves the restored control plane can boot and pass health verification, optionally runs bounded smoke validation, and emits a machine-readable recovery report that release evidence can reference.

**Architecture:** Keep the current backup and restore contract intact and add one narrow orchestration layer on top of it. The new ops module should reuse `run_postgres_restore(...)`, boot the restored database through `create_app(...)` and `TestClient`, optionally call `run_control_plane_smoke(...)`, and always produce a structured JSON report. The CLI should stay thin, and release-evidence integration should be additive only: surface restore-drill status when a report is provided, but do not make it a certification gate in this slice.

**Tech Stack:** Python, FastAPI, TestClient, SQLAlchemy settings/bootstrap, pytest, argparse, Markdown runbooks

---

## File Structure

### Backend ops and CLI

- Create: `services/control-plane-api/store_control_plane/ops/postgres_restore_drill.py`
  - Own the restore-drill dataclasses, orchestration, report building, and report writing.
- Modify: `services/control-plane-api/store_control_plane/ops/__init__.py`
  - Export the new restore-drill types and entry point.
- Create: `services/control-plane-api/scripts/run_restore_drill.py`
  - Thin CLI wrapper that parses arguments, enforces destructive confirmation, calls the ops function, writes the JSON artifact, and exits non-zero on failure.

### Release evidence

- Modify: `services/control-plane-api/scripts/generate_release_candidate_evidence.py`
  - Accept an optional restore-drill report path and render a recovery-evidence section in the Markdown output.
- Modify: `services/control-plane-api/tests/test_release_candidate_evidence_generation.py`
  - Cover report rendering when restore-drill evidence is present.

### Tests

- Create: `services/control-plane-api/tests/test_postgres_restore_drill_ops.py`
  - Unit coverage for success/failure orchestration, structured reporting, and optional smoke verification.
- Create: `services/control-plane-api/tests/test_postgres_restore_drill_script.py`
  - Script-level coverage for CLI argument handling, confirmation gating, JSON output writing, and non-zero exit on failed drills.

### Docs

- Modify: `docs/runbooks/control-plane-backup-restore.md`
  - Replace the hand-written restore-drill exit criteria with the new CLI and report artifact workflow.
- Modify: `docs/runbooks/control-plane-production-deployment.md`
  - Mention attaching recent restore-drill evidence for staged recovery proof.
- Modify: `docs/TASK_LEDGER.md`
  - Advance `V2-009` only if this slice changes the visible program state.
- Modify: `docs/WORKLOG.md`
  - Record the restore-drill foundation slice and its verification commands.

## Task 1: Add failing restore-drill and evidence tests

**Files:**
- Create: `services/control-plane-api/tests/test_postgres_restore_drill_ops.py`
- Create: `services/control-plane-api/tests/test_postgres_restore_drill_script.py`
- Modify: `services/control-plane-api/tests/test_release_candidate_evidence_generation.py`

- [ ] **Step 1: Write the failing restore-drill orchestration tests**

Create `services/control-plane-api/tests/test_postgres_restore_drill_ops.py` to cover:
- successful restore drill with mandatory health verification only
- blocked environment mismatch bubbling up from `run_postgres_restore(...)`
- restore success followed by failed `/v1/system/health`
- restore success followed by failed optional smoke verification
- report payload containing:
  - `status`
  - `started_at`
  - `finished_at`
  - `duration_seconds`
  - `source`
  - `target`
  - `restored_manifest`
  - `health_result`
  - `verification_result`
  - `failure_reason`

Use injected fakes for:
- restore execution
- FastAPI app health probing
- smoke verification
- report clock/timestamps where needed

- [ ] **Step 2: Write the failing CLI runner tests**

Create `services/control-plane-api/tests/test_postgres_restore_drill_script.py` using the same `importlib.util.spec_from_file_location(...)` pattern already used by:
- `services/control-plane-api/tests/test_verify_deployed_control_plane.py`
- `services/control-plane-api/tests/test_release_candidate_evidence_generation.py`

Cover:
- non-dry-run execution rejecting missing `--yes`
- successful drill writing the JSON report and printing a concise summary
- failed drill exiting non-zero while still writing a failed report when available

- [ ] **Step 3: Extend the release-evidence test with restore-drill rendering**

Update `services/control-plane-api/tests/test_release_candidate_evidence_generation.py` to add a case where:
- a restore-drill JSON report path is supplied
- the generated Markdown includes the restore-drill command/report summary
- the final evidence document shows the restore-drill status and source artifact details

Do not add a certification gate assertion yet; this slice only surfaces evidence.

- [ ] **Step 4: Run the focused tests to verify they fail**

Run:
- `python -m pytest services/control-plane-api/tests/test_postgres_restore_drill_ops.py -q`
- `python -m pytest services/control-plane-api/tests/test_postgres_restore_drill_script.py -q`
- `python -m pytest services/control-plane-api/tests/test_release_candidate_evidence_generation.py -q`

Expected: FAIL with missing restore-drill module, missing CLI script, and missing evidence rendering support.

- [ ] **Step 5: Commit**

```bash
git add services/control-plane-api/tests/test_postgres_restore_drill_ops.py services/control-plane-api/tests/test_postgres_restore_drill_script.py services/control-plane-api/tests/test_release_candidate_evidence_generation.py
git commit -m "test: add restore drill coverage"
```

## Task 2: Implement the restore-drill ops module

**Files:**
- Create: `services/control-plane-api/store_control_plane/ops/postgres_restore_drill.py`
- Modify: `services/control-plane-api/store_control_plane/ops/__init__.py`

- [ ] **Step 1: Add the restore-drill result and report dataclasses**

Create `services/control-plane-api/store_control_plane/ops/postgres_restore_drill.py` with focused dataclasses such as:
- `RestoreDrillHealthResult`
- `RestoreDrillVerificationResult`
- `RestoreDrillReport`

The report object should expose a `to_dict()` helper that returns the JSON-safe structure expected by the tests and runbooks.

- [ ] **Step 2: Implement mandatory post-restore health probing**

In `run_postgres_restore_drill(...)`:
- call the injected or default `run_postgres_restore(...)`
- boot the restored database with `create_app(database_url=..., bootstrap_database=False, ...)`
- wrap it in `TestClient`
- call `GET /v1/system/health`
- record the payload in `health_result`

Keep this probe local and bounded. Do not invoke full suite verification here.

- [ ] **Step 3: Implement optional smoke verification**

Add a `verify_smoke: bool = False` option to `run_postgres_restore_drill(...)`.

When enabled:
- call `run_control_plane_smoke(database_url=...)`
- capture pass/fail in `verification_result`

When disabled:
- return a structured `verification_result` showing the smoke path was skipped rather than omitting the field.

- [ ] **Step 4: Build structured failure handling**

Ensure the orchestration function:
- returns `status = "passed"` only when restore, health, and optional smoke all succeed
- returns `status = "failed"` on any explicit failure
- preserves `restored_manifest` when restore succeeded
- records `failure_reason` with a stable, human-readable explanation

For environment mismatch or restore failures that happen before health probing, still build the most complete failed report possible.

- [ ] **Step 5: Write the report artifact helper**

Add a helper such as `write_restore_drill_report(report: RestoreDrillReport, output_path: Path) -> Path` that:
- creates parent directories
- writes JSON with indentation
- returns the final path

Keep file writing separate from CLI argument parsing so the ops module remains testable.

- [ ] **Step 6: Export the new ops seam**

Update `services/control-plane-api/store_control_plane/ops/__init__.py` to export:
- `RestoreDrillReport`
- `run_postgres_restore_drill`
- `write_restore_drill_report`

- [ ] **Step 7: Re-run the restore-drill ops tests**

Run:
- `python -m pytest services/control-plane-api/tests/test_postgres_restore_drill_ops.py -q`

Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add services/control-plane-api/store_control_plane/ops/postgres_restore_drill.py services/control-plane-api/store_control_plane/ops/__init__.py services/control-plane-api/tests/test_postgres_restore_drill_ops.py
git commit -m "feat: add restore drill orchestration"
```

## Task 3: Add the restore-drill CLI runner

**Files:**
- Create: `services/control-plane-api/scripts/run_restore_drill.py`
- Create: `services/control-plane-api/tests/test_postgres_restore_drill_script.py`

- [ ] **Step 1: Add the CLI argument surface**

Create `services/control-plane-api/scripts/run_restore_drill.py` with:
- `--dump-key`
- `--metadata-key`
- `--target-database-url`
- `--output-path`
- `--allow-environment-mismatch`
- `--verify-smoke`
- `--yes`

Mirror the style of `services/control-plane-api/scripts/restore_postgres.py` for:
- `SERVICE_ROOT` bootstrapping
- `Settings()` loading
- destructive confirmation rules

- [ ] **Step 2: Thread the ops call and JSON writing**

The script should:
- load `Settings()`
- call `run_postgres_restore_drill(...)`
- call `write_restore_drill_report(...)`
- print a concise result line containing:
  - `status`
  - `dump_key`
  - redacted target identifier
  - output path

- [ ] **Step 3: Exit non-zero on failed drills**

Keep the CLI behavior explicit:
- successful drill returns `0`
- failed drill raises `SystemExit(1)` or returns `1`
- missing `--yes` for destructive execution exits before any restore call

- [ ] **Step 4: Re-run the CLI tests**

Run:
- `python -m pytest services/control-plane-api/tests/test_postgres_restore_drill_script.py -q`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add services/control-plane-api/scripts/run_restore_drill.py services/control-plane-api/tests/test_postgres_restore_drill_script.py
git commit -m "feat: add restore drill runner"
```

## Task 4: Surface restore-drill evidence in release reporting

**Files:**
- Modify: `services/control-plane-api/scripts/generate_release_candidate_evidence.py`
- Modify: `services/control-plane-api/tests/test_release_candidate_evidence_generation.py`

- [ ] **Step 1: Add optional restore-drill report loading**

Update `generate_release_candidate_evidence(...)` and `parse_args()` to accept an optional:
- `restore_drill_report_path: Path | None`
- CLI flag `--restore-drill-report`

When present:
- load the JSON report
- keep it out of certification gating for now
- thread it into the rendered Markdown output

- [ ] **Step 2: Render a recovery-evidence section**

Extend `_render_markdown(...)` to show:
- restore-drill report status
- source `dump_key` and `metadata_key`
- restored manifest environment and release version
- report location or summary line

Keep the format concise and parallel to the existing verification/performance evidence sections.

- [ ] **Step 3: Re-run the release-evidence tests**

Run:
- `python -m pytest services/control-plane-api/tests/test_release_candidate_evidence_generation.py -q`

Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add services/control-plane-api/scripts/generate_release_candidate_evidence.py services/control-plane-api/tests/test_release_candidate_evidence_generation.py
git commit -m "feat: add restore drill evidence rendering"
```

## Task 5: Update runbooks and complete focused verification

**Files:**
- Modify: `docs/runbooks/control-plane-backup-restore.md`
- Modify: `docs/runbooks/control-plane-production-deployment.md`
- Modify: `docs/TASK_LEDGER.md`
- Modify: `docs/WORKLOG.md`

- [ ] **Step 1: Update the backup/restore runbook**

In `docs/runbooks/control-plane-backup-restore.md`:
- keep `restore_postgres.py` as the low-level restore command
- add the new `run_restore_drill.py` workflow
- show both:
  - restore drill without smoke
  - restore drill with `--verify-smoke`
- explain the JSON report artifact and how to read pass/fail status

- [ ] **Step 2: Update the production deployment runbook**

In `docs/runbooks/control-plane-production-deployment.md`:
- mention restore-drill evidence as a staged recovery proof
- point to the JSON report or release-evidence Markdown as the artifact to retain

- [ ] **Step 3: Update the worklog and ledger**

Record the slice in `docs/WORKLOG.md`.

Update `docs/TASK_LEDGER.md` only if this slice changes the visible `V2-009` phase or notes.

- [ ] **Step 4: Run focused verification**

Run:
- `python -m pytest services/control-plane-api/tests/test_postgres_restore_drill_ops.py services/control-plane-api/tests/test_postgres_restore_drill_script.py services/control-plane-api/tests/test_release_candidate_evidence_generation.py services/control-plane-api/tests/test_postgres_restore_ops.py services/control-plane-api/tests/test_deployment_ops.py -q`
- `python services/control-plane-api/scripts/run_restore_drill.py --help`
- `git -c core.safecrlf=false diff --check`

Expected:
- pytest PASS
- CLI help exits successfully and documents the new flags
- `diff --check` prints nothing

- [ ] **Step 5: Commit**

```bash
git add docs/runbooks/control-plane-backup-restore.md docs/runbooks/control-plane-production-deployment.md docs/TASK_LEDGER.md docs/WORKLOG.md
git commit -m "docs: record restore drill foundation"
```

