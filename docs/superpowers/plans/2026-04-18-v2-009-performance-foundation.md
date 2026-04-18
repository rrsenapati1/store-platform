# V2-009 Performance And Load Validation Foundation Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a reusable control-plane performance-validation harness, launch-foundation hot-path budgets, and release-evidence/certification integration for the first V2-009 hardening slice.

**Architecture:** Keep the implementation centered on one pure budget-evaluation module plus one in-process workload runner and one CLI script. Reuse the existing release evidence and certification scripts by extending them with performance results instead of inventing a parallel reporting path. Keep this slice backend-only apart from docs.

**Tech Stack:** Python, FastAPI, httpx/TestClient, pytest, Markdown runbooks

---

## File Structure

### Backend

- Create: `services/control-plane-api/store_control_plane/performance_validation.py`
  - Pure dataclasses and helpers for scenario budgets, percentile calculations, throughput calculations, and overall result aggregation.
- Create: `services/control-plane-api/store_control_plane/performance_workloads.py`
  - In-process launch-foundation workload bootstrap and scenario runners for checkout, payment, offline replay, receiving, restock, stock count, and reporting reads.
- Create: `services/control-plane-api/scripts/validate_performance_foundation.py`
  - CLI entrypoint that runs the launch-foundation scenario set and writes a JSON report.
- Modify: `services/control-plane-api/scripts/generate_release_candidate_evidence.py`
  - Run or accept performance validation results and render them into markdown evidence.
- Modify: `services/control-plane-api/scripts/certify_release_candidate.py`
  - Add the optional performance-budget gate when performance results are available.

### Tests

- Create: `services/control-plane-api/tests/test_performance_validation.py`
  - Covers budget evaluation, scenario aggregation, JSON report writing, and script-level result handling.
- Modify: `services/control-plane-api/tests/test_release_candidate_evidence_generation.py`
  - Cover performance summary rendering and skipped/performed performance lanes.
- Modify: `services/control-plane-api/tests/test_release_candidate_certification.py`
  - Cover the performance certification gate in pass/fail cases.

### Docs

- Modify: `docs/runbooks/control-plane-verification.md`
  - Document the performance-validation command and how it fits into release evidence.
- Modify: `docs/TASK_LEDGER.md`
  - Advance `V2-009` to `In Progress`.
- Modify: `docs/WORKLOG.md`
  - Record the V2-009 performance/load validation foundation slice and verification commands.

## Task 1: Write failing performance-validation tests

**Files:**
- Create: `services/control-plane-api/tests/test_performance_validation.py`
- Modify: `services/control-plane-api/tests/test_release_candidate_evidence_generation.py`
- Modify: `services/control-plane-api/tests/test_release_candidate_certification.py`

- [ ] **Step 1: Add failing budget-evaluation tests**

Create `services/control-plane-api/tests/test_performance_validation.py` covering:

- scenario passes when p95, error rate, and throughput all meet budget
- scenario fails when p95 exceeds budget
- scenario fails when error rate exceeds budget
- scenario fails when throughput falls below budget
- report writer persists a machine-readable JSON result

- [ ] **Step 2: Add failing evidence-generation integration tests**

Extend `services/control-plane-api/tests/test_release_candidate_evidence_generation.py` so it expects:

- a performance-validation command/result summary in the markdown evidence
- performance scenario names or a compact failure summary
- final evidence output still rendered correctly when performance validation is skipped

- [ ] **Step 3: Add failing certification tests**

Extend `services/control-plane-api/tests/test_release_candidate_certification.py` to cover:

- certification approval when provided performance results are passing
- certification blocking when provided performance results are failing

- [ ] **Step 4: Run focused tests to verify RED**

Run:

- `python -m pytest services/control-plane-api/tests/test_performance_validation.py -q`
- `python -m pytest services/control-plane-api/tests/test_release_candidate_evidence_generation.py -q`
- `python -m pytest services/control-plane-api/tests/test_release_candidate_certification.py -q`

Expected: FAIL with missing performance-validation module/script fields and missing certification/evidence support.

## Task 2: Build the pure performance budget engine

**Files:**
- Create: `services/control-plane-api/store_control_plane/performance_validation.py`

- [ ] **Step 1: Add budget and result dataclasses**

Implement focused dataclasses for:

- scenario budget
- scenario sample
- scenario result
- overall report

- [ ] **Step 2: Add pure evaluation helpers**

Implement helpers for:

- percentile calculation
- throughput calculation
- error-rate calculation
- scenario pass/fail determination
- overall report aggregation

- [ ] **Step 3: Re-run the budget-evaluation tests**

Run:

- `python -m pytest services/control-plane-api/tests/test_performance_validation.py -q`

Expected: scenario evaluation tests pass, script/evidence tests still fail.

## Task 3: Build launch-foundation workload runners and CLI script

**Files:**
- Create: `services/control-plane-api/store_control_plane/performance_workloads.py`
- Create: `services/control-plane-api/scripts/validate_performance_foundation.py`

- [ ] **Step 1: Add reusable launch-foundation bootstrap helpers**

Create one bootstrap path that:

- starts an in-process app with stub identity
- seeds tenant/branch/product/supplier/device state
- returns reusable IDs and headers for each scenario runner

- [ ] **Step 2: Add scenario runners for the initial hot paths**

Implement bounded runners for:

- checkout price preview
- direct sale creation
- checkout payment-session creation
- offline sale replay
- reviewed receiving creation
- restock task lifecycle
- reviewed stock count lifecycle
- branch reporting dashboard read

- [ ] **Step 3: Add the CLI wrapper**

Implement `validate_performance_foundation.py` so it:

- accepts `--database-url`
- accepts `--iterations`
- accepts `--output-path`
- runs the launch-foundation scenario set
- writes JSON
- prints the structured result
- exits non-zero on failure

- [ ] **Step 4: Re-run focused performance tests**

Run:

- `python -m pytest services/control-plane-api/tests/test_performance_validation.py -q`

Expected: the new module/script tests pass.

## Task 4: Integrate performance results into release evidence and certification

**Files:**
- Modify: `services/control-plane-api/scripts/generate_release_candidate_evidence.py`
- Modify: `services/control-plane-api/scripts/certify_release_candidate.py`
- Modify: `services/control-plane-api/tests/test_release_candidate_evidence_generation.py`
- Modify: `services/control-plane-api/tests/test_release_candidate_certification.py`

- [ ] **Step 1: Extend evidence generation**

Add support for:

- running performance validation by default alongside local verification
- skipping it explicitly
- rendering performance result details into the markdown evidence

- [ ] **Step 2: Extend certification**

Add support for:

- optional performance input
- gate `performance_budgets_passed`
- blocked certification when performance data is supplied and failing

- [ ] **Step 3: Re-run focused integration tests**

Run:

- `python -m pytest services/control-plane-api/tests/test_release_candidate_evidence_generation.py -q`
- `python -m pytest services/control-plane-api/tests/test_release_candidate_certification.py -q`

Expected: PASS.

## Task 5: Update docs and verify the whole slice

**Files:**
- Modify: `docs/runbooks/control-plane-verification.md`
- Modify: `docs/TASK_LEDGER.md`
- Modify: `docs/WORKLOG.md`

- [ ] **Step 1: Document the new command path**

Update the verification runbook with:

- the performance-validation command
- output expectations
- the relation to release evidence generation

- [ ] **Step 2: Update ledger and worklog**

Mark `V2-009` as `In Progress` and log the slice with verification commands.

- [ ] **Step 3: Run end-to-end verification**

Run:

- `python -m pytest services/control-plane-api/tests/test_performance_validation.py services/control-plane-api/tests/test_release_candidate_evidence_generation.py services/control-plane-api/tests/test_release_candidate_certification.py services/control-plane-api/tests/test_verify_deployed_control_plane.py services/control-plane-api/tests/test_deployment_ops.py -q`
- `git -c core.safecrlf=false diff --check`

If the harness is stable enough locally, also run:

- `python services/control-plane-api/scripts/validate_performance_foundation.py --database-url <local verification database url> --iterations 3`

- [ ] **Step 4: Commit**

```bash
git add services/control-plane-api/store_control_plane/performance_validation.py services/control-plane-api/store_control_plane/performance_workloads.py services/control-plane-api/scripts/validate_performance_foundation.py services/control-plane-api/tests/test_performance_validation.py services/control-plane-api/tests/test_release_candidate_evidence_generation.py services/control-plane-api/tests/test_release_candidate_certification.py docs/runbooks/control-plane-verification.md docs/TASK_LEDGER.md docs/WORKLOG.md
git commit -m "feat: add v2-009 performance validation foundation"
```
