# V2-009 Alert Verification Foundation Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deployed operational-alert verifier that turns control-plane observability posture into machine-readable release evidence and blocks certification when alert thresholds are already breached.

**Architecture:** Add a focused `operational_alerts.py` evaluator that consumes the existing platform observability summary and deployed security verification result, then wrap it in a CLI script that writes one normalized JSON report. Thread that report into the existing release-evidence and certification scripts so alert posture becomes another first-class `V2-009` hardening lane alongside security, performance, restore drills, and vulnerability scans.

**Tech Stack:** Python 3.12, injected HTTP/script dependencies for testability, pytest, JSON report files, existing release-evidence scripts, Markdown runbooks.

---

## File Structure

### New Files

- `services/control-plane-api/store_control_plane/operational_alerts.py`
  - Owns alert-threshold defaults, alert-check evaluation, report construction, and JSON write helpers.
- `services/control-plane-api/scripts/verify_operational_alert_posture.py`
  - CLI wrapper that fetches deployed observability state, evaluates alert posture, and writes the JSON report.
- `services/control-plane-api/tests/test_operational_alerts.py`
  - Unit coverage for dead-letter, retryable, degraded-branch, backup-age, and security-result evaluation.
- `services/control-plane-api/tests/test_verify_operational_alert_posture.py`
  - CLI/report tests for the alert-verification script.

### Modified Files

- `services/control-plane-api/scripts/generate_release_candidate_evidence.py`
  - Accept optional alert-verification report input and render a new evidence section.
- `services/control-plane-api/scripts/certify_release_candidate.py`
  - Add `operational_alerts_verified` gate and optional report-loading path.
- `services/control-plane-api/tests/test_release_candidate_evidence_generation.py`
  - Extend evidence rendering expectations for missing and present alert reports.
- `services/control-plane-api/tests/test_release_candidate_certification.py`
  - Extend approval/blocking expectations for alert verification.
- `docs/runbooks/security-observability-operations.md`
  - Replace manual-only alert posture checks with the new verifier path and thresholds.
- `docs/runbooks/control-plane-production-deployment.md`
  - Add alert-verification evidence to staging/prod promotion requirements.
- `docs/WORKLOG.md`
  - Record the completed slice.

## Task 1: Build The Operational Alert Evaluator

**Files:**
- Create: `services/control-plane-api/store_control_plane/operational_alerts.py`
- Create: `services/control-plane-api/tests/test_operational_alerts.py`

- [ ] **Step 1: Write the failing evaluator tests**

Add tests in `services/control-plane-api/tests/test_operational_alerts.py` for:

```python
def test_build_operational_alert_report_fails_on_dead_letter_jobs() -> None:
    report = module.build_operational_alert_report(
        generated_at="2026-04-18T18:30:00Z",
        environment="prod",
        release_version="2026.04.18-rc3",
        observability_summary={
            "operations": {"dead_letter_count": 1, "retryable_count": 0},
            "runtime": {"degraded_branch_count": 0},
            "backup": {"status": "ok", "age_hours": 1.0},
        },
        security_result={"status": "passed"},
    )
    assert report["status"] == "failed"
    assert report["failing_checks"] == ["operations_dead_letter_clear"]


def test_build_operational_alert_report_fails_on_backup_age_breach() -> None:
    report = module.build_operational_alert_report(
        ...,
        observability_summary={
            "operations": {"dead_letter_count": 0, "retryable_count": 0},
            "runtime": {"degraded_branch_count": 0},
            "backup": {"status": "ok", "age_hours": 30.0},
        },
        security_result={"status": "passed"},
    )
    assert report["status"] == "failed"
    assert "backup_freshness_within_limit" in report["failing_checks"]


def test_build_operational_alert_report_passes_when_all_thresholds_hold() -> None:
    report = module.build_operational_alert_report(
        ...,
        observability_summary={
            "operations": {"dead_letter_count": 0, "retryable_count": 1},
            "runtime": {"degraded_branch_count": 0},
            "backup": {"status": "ok", "age_hours": 2.0},
        },
        security_result={"status": "passed"},
        thresholds={"max_retryable_count": 2, "max_degraded_branch_count": 0, "max_backup_age_hours": 26},
    )
    assert report["status"] == "passed"
```

- [ ] **Step 2: Run the evaluator tests to verify they fail**

Run:

```bash
python -m pytest services/control-plane-api/tests/test_operational_alerts.py -q
```

Expected: FAIL because the evaluator module does not exist yet.

- [ ] **Step 3: Implement the minimal evaluator**

Create `services/control-plane-api/store_control_plane/operational_alerts.py` with focused helpers:

```python
DEFAULT_ALERT_THRESHOLDS = {
    "max_retryable_count": 0,
    "max_degraded_branch_count": 0,
    "max_backup_age_hours": 26,
}


def build_alert_check(...): ...
def evaluate_operational_alerts(...): ...
def build_operational_alert_report(...): ...
def write_operational_alert_report(...): ...
```

Implementation rules:

- keep the evaluator pure where possible
- consume already-normalized observability/security dictionaries
- return `alert_checks` as a list of structured dicts with `name`, `status`, `observed_value`, `threshold`, and `reason`

- [ ] **Step 4: Run the evaluator tests again and make them pass**

Run:

```bash
python -m pytest services/control-plane-api/tests/test_operational_alerts.py -q
```

Expected: PASS for the new evaluator behavior.

- [ ] **Step 5: Commit the evaluator**

```bash
git add services/control-plane-api/store_control_plane/operational_alerts.py services/control-plane-api/tests/test_operational_alerts.py
git commit -m "feat: add operational alert evaluator"
```

## Task 2: Add The Deployed Alert Verification CLI

**Files:**
- Create: `services/control-plane-api/scripts/verify_operational_alert_posture.py`
- Create: `services/control-plane-api/tests/test_verify_operational_alert_posture.py`
- Modify: `services/control-plane-api/store_control_plane/operational_alerts.py`

- [ ] **Step 1: Write the failing script tests**

Add tests in `services/control-plane-api/tests/test_verify_operational_alert_posture.py` for:

```python
def test_verify_operational_alert_posture_writes_json_report(tmp_path: Path) -> None:
    result = module.verify_operational_alert_posture(
        base_url="https://control.staging.store.korsenex.com",
        output_path=tmp_path / "alert-report.json",
        verify_deployed=fake_verify_deployed,
        send_request=fake_send_request,
    )
    payload = json.loads((tmp_path / "alert-report.json").read_text(encoding="utf-8"))
    assert result["status"] == "passed"
    assert payload["alert_checks"][0]["name"]


def test_verify_operational_alert_posture_returns_non_zero_on_failed_posture(...) -> None:
    ...
```

Use injected fake deployed verification and fake HTTP responses for `/v1/platform/observability/summary`.

- [ ] **Step 2: Run the script tests to verify they fail**

Run:

```bash
python -m pytest services/control-plane-api/tests/test_verify_operational_alert_posture.py -q
```

Expected: FAIL because the script does not exist yet.

- [ ] **Step 3: Implement the CLI runner**

Create `services/control-plane-api/scripts/verify_operational_alert_posture.py` with:

- `--base-url`
- `--expected-environment`
- `--expected-release-version`
- `--output-path`
- `--max-retryable-count`
- `--max-degraded-branch-count`
- `--max-backup-age-hours`
- optional `--bearer-token` passthrough for future consistency if needed

Core flow:

1. call existing deployed verifier
2. fetch `/v1/platform/observability/summary`
3. call `build_operational_alert_report(...)`
4. write report JSON
5. return non-zero on failed posture

Keep HTTP requests injectable for tests.

- [ ] **Step 4: Run the script tests and CLI smoke path**

Run:

```bash
python -m pytest services/control-plane-api/tests/test_verify_operational_alert_posture.py -q
python services/control-plane-api/scripts/verify_operational_alert_posture.py --help
```

Expected:

- pytest PASS
- CLI help prints successfully

- [ ] **Step 5: Commit the deployed alert verifier**

```bash
git add services/control-plane-api/scripts/verify_operational_alert_posture.py services/control-plane-api/tests/test_verify_operational_alert_posture.py services/control-plane-api/store_control_plane/operational_alerts.py
git commit -m "feat: add alert posture verifier"
```

## Task 3: Integrate Alert Verification Into Release Evidence And Certification

**Files:**
- Modify: `services/control-plane-api/scripts/generate_release_candidate_evidence.py`
- Modify: `services/control-plane-api/scripts/certify_release_candidate.py`
- Modify: `services/control-plane-api/tests/test_release_candidate_evidence_generation.py`
- Modify: `services/control-plane-api/tests/test_release_candidate_certification.py`

- [ ] **Step 1: Extend the existing release tests first**

Add failing tests for:

```python
def test_generate_release_candidate_evidence_renders_operational_alert_posture(tmp_path: Path) -> None:
    ...
    assert "## Operational Alert Evidence" in content
    assert "overall alert status: passed" in content
    assert "backup freshness: passed" in content


def test_release_candidate_certification_blocks_failed_operational_alert_report() -> None:
    result = module.certify_release_candidate(
        ...,
        operational_alert_result={"status": "failed", "failing_checks": ["backup_freshness_within_limit"]},
        verify_deployed=fake_verify_deployed,
    )
    assert result["status"] == "blocked"
    assert result["gates"]["operational_alerts_verified"] is False
```

Also add a missing-report case that blocks by default.

- [ ] **Step 2: Run the focused release tests and verify failure**

Run:

```bash
python -m pytest services/control-plane-api/tests/test_release_candidate_evidence_generation.py services/control-plane-api/tests/test_release_candidate_certification.py -q
```

Expected: FAIL because alert-report wiring does not exist yet.

- [ ] **Step 3: Implement the release integration**

Update `generate_release_candidate_evidence.py` to:

- accept `--operational-alert-report`
- load the JSON when present
- render:

```markdown
## Operational Alert Evidence

- overall alert status: ...
- dead-letter: ...
- retryable failures: ...
- runtime degradation: ...
- backup freshness: ...
- security verification: ...
- failing checks: ...
```

Update `certify_release_candidate.py` to:

- accept `--operational-alert-report`
- load the JSON report
- add gate:

```python
"operational_alerts_verified": operational_alert_result is not None and operational_alert_result.get("status") == "passed"
```

Keep optional parameters for test injection; do not fold this logic into `verify_deployed_control_plane.py`.

- [ ] **Step 4: Run the focused release tests again**

Run:

```bash
python -m pytest services/control-plane-api/tests/test_release_candidate_evidence_generation.py services/control-plane-api/tests/test_release_candidate_certification.py -q
```

Expected: PASS with the new alert evidence and gating behavior.

- [ ] **Step 5: Commit the release integration**

```bash
git add services/control-plane-api/scripts/generate_release_candidate_evidence.py services/control-plane-api/scripts/certify_release_candidate.py services/control-plane-api/tests/test_release_candidate_evidence_generation.py services/control-plane-api/tests/test_release_candidate_certification.py
git commit -m "feat: gate certification on alert posture"
```

## Task 4: Update Runbooks, Worklog, And Final Verification

**Files:**
- Modify: `docs/runbooks/security-observability-operations.md`
- Modify: `docs/runbooks/control-plane-production-deployment.md`
- Modify: `docs/WORKLOG.md`

- [ ] **Step 1: Update the operational runbooks**

Document:

- the new verifier command
- threshold override arguments
- JSON report path
- release-evidence integration
- release-certification expectations

Add concrete examples such as:

```powershell
python services/control-plane-api/scripts/verify_operational_alert_posture.py `
  --base-url https://control.store.korsenex.com `
  --expected-environment prod `
  --expected-release-version 2026.04.18 `
  --output-path docs/launch/evidence/prod-operational-alert-report.json
```

- [ ] **Step 2: Record the slice in worklog**

Update `docs/WORKLOG.md` with:

- alert-verification foundation summary
- focused verification commands

Do not change `docs/TASK_LEDGER.md` unless the current ledger convention needs a fresh note; `V2-009` should remain in progress.

- [ ] **Step 3: Run the full focused verification set**

Run:

```bash
python -m pytest services/control-plane-api/tests/test_operational_alerts.py services/control-plane-api/tests/test_verify_operational_alert_posture.py services/control-plane-api/tests/test_release_candidate_evidence_generation.py services/control-plane-api/tests/test_release_candidate_certification.py services/control-plane-api/tests/test_verify_deployed_control_plane.py -q
python services/control-plane-api/scripts/verify_operational_alert_posture.py --help
git -c core.safecrlf=false diff --check
```

Expected:

- all focused tests PASS
- CLI help works
- diff check is clean

- [ ] **Step 4: Commit the docs and final verification state**

```bash
git add docs/runbooks/security-observability-operations.md docs/runbooks/control-plane-production-deployment.md docs/WORKLOG.md
git commit -m "docs: record alert verification foundation"
```

## Final Integration

- [ ] Merge the completed task branch back to `main`
- [ ] Run the focused verification set on merged `main`
- [ ] Push `main` to `origin/main`
- [ ] Remove the temporary worktree and feature branch
- [ ] Start the next `V2-009` slice from a fresh worktree
