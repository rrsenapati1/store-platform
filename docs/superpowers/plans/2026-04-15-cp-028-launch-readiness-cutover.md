# CP-028 Launch Readiness And Cutover Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the final repo-owned launch gate pack with release-candidate certification, beta/cutover docs, and explicit go-live sign-off artifacts.

**Architecture:** Extend the existing control-plane verification boundary instead of inventing a new automation stack. Add one lightweight certification script that consumes deployed verification and authority-boundary data, create a new `docs/launch/` documentation section for beta/cutover/go-live evidence, and wire the launch docs into the main docs index without pretending real beta/prod sign-off has already happened.

**Tech Stack:** Python, existing control-plane verification scripts, pytest, Markdown docs

---

## Planned File Structure

### Launch certification

- `services/control-plane-api/scripts/certify_release_candidate.py`
- `services/control-plane-api/tests/test_release_candidate_certification.py`

### Launch docs

- `docs/launch/launch-readiness-checklist.md`
- `docs/launch/beta-pilot-exit-criteria.md`
- `docs/launch/legacy-read-acceptance-register.md`
- `docs/launch/release-candidate-evidence-template.md`
- `docs/launch/go-live-runbook.md`

### Existing docs to update

- `docs/DOCS_INDEX.md`
- `docs/TASK_LEDGER.md`
- `docs/WORKLOG.md`

---

### Task 1: Add release-candidate certification script and tests

**Files:**
- Create: `services/control-plane-api/scripts/certify_release_candidate.py`
- Create: `services/control-plane-api/tests/test_release_candidate_certification.py`

- [ ] **Step 1: Write failing tests for approved certification, blocked shadow-mode certification, and blocked legacy-domain certification**
- [ ] **Step 2: Run `python -m pytest services/control-plane-api/tests/test_release_candidate_certification.py -q` and confirm red**
- [ ] **Step 3: Implement the release-candidate certification function and CLI on top of deployed verification**
- [ ] **Step 4: Re-run `python -m pytest services/control-plane-api/tests/test_release_candidate_certification.py -q` and confirm green**
- [ ] **Step 5: Commit**

### Task 2: Add the launch readiness docs pack

**Files:**
- Create: `docs/launch/launch-readiness-checklist.md`
- Create: `docs/launch/beta-pilot-exit-criteria.md`
- Create: `docs/launch/legacy-read-acceptance-register.md`
- Create: `docs/launch/release-candidate-evidence-template.md`
- Create: `docs/launch/go-live-runbook.md`

- [ ] **Step 1: Create `docs/launch/` and write the launch-readiness checklist plus beta-pilot exit criteria**
- [ ] **Step 2: Write the legacy-read acceptance register and release-candidate evidence template**
- [ ] **Step 3: Write the go-live runbook, linking the existing deployment, security, support, and packaging runbooks instead of duplicating them**
- [ ] **Step 4: Review the launch docs for consistent terminology around cutover, beta, and operator sign-off**
- [ ] **Step 5: Commit**

### Task 3: Update docs entrypoints and verify launch-pack integrity

**Files:**
- Modify: `docs/DOCS_INDEX.md`
- Modify: `docs/TASK_LEDGER.md`
- Modify: `docs/WORKLOG.md`

- [ ] **Step 1: Update `docs/DOCS_INDEX.md` with the new `launch/` section and start-here guidance**
- [ ] **Step 2: Run `git diff --check`**
- [ ] **Step 3: Run `python -m pytest services/control-plane-api/tests/test_release_candidate_certification.py -q`**
- [ ] **Step 4: Run `python services/control-plane-api/scripts/certify_release_candidate.py --help`**
- [ ] **Step 5: Run a launch-docs integrity check that confirms each launch doc exists and `DOCS_INDEX.md` references the `launch/` section**
- [ ] **Step 6: Update the ledger/worklog honestly: mark the repo-side launch pack implemented, and note that real beta/go-live sign-off remains an operator action**
- [ ] **Step 7: Commit**
