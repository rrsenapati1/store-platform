# SBOM Foundation Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate normalized SBOM evidence with raw CycloneDX artifacts and make it a release-candidate gate.

**Architecture:** Add one SBOM domain module plus one CLI runner, then thread the resulting JSON report into release evidence rendering and certification. Keep the first slice narrow: repo-owned artifact generation, no external publication or signing.

**Tech Stack:** Python, `syft`, JSON, existing release-evidence scripts, pytest.

---

### Task 1: Add SBOM domain module

**Files:**
- Create: `services/control-plane-api/store_control_plane/sbom_generation.py`
- Test: `services/control-plane-api/tests/test_sbom_generation.py`

- [ ] Write failing SBOM report tests.
- [ ] Run the focused SBOM domain tests and confirm import failure.
- [ ] Implement normalized SBOM surface evaluation and JSON writing.
- [ ] Re-run the SBOM domain tests and confirm they pass.

### Task 2: Add operator CLI

**Files:**
- Create: `services/control-plane-api/scripts/generate_sbom_bundle.py`
- Test: `services/control-plane-api/tests/test_generate_sbom_bundle_script.py`

- [ ] Write failing CLI tests.
- [ ] Run the focused CLI tests and confirm failure.
- [ ] Implement the CLI wrapper and exit-code behavior.
- [ ] Re-run the CLI tests and confirm they pass.

### Task 3: Integrate release evidence and certification

**Files:**
- Modify: `services/control-plane-api/scripts/generate_release_candidate_evidence.py`
- Modify: `services/control-plane-api/scripts/certify_release_candidate.py`
- Test: `services/control-plane-api/tests/test_release_candidate_evidence_generation.py`
- Test: `services/control-plane-api/tests/test_release_candidate_certification.py`

- [ ] Add failing evidence and certification tests for `--sbom-report`.
- [ ] Run the focused release tests and confirm failure.
- [ ] Implement SBOM rendering and `sbom_verified` gating.
- [ ] Update existing approval fixtures to include passing SBOM posture.
- [ ] Re-run the focused release tests and confirm they pass.

### Task 4: Update docs and verify

**Files:**
- Modify: `docs/runbooks/dependency-scanning.md`
- Modify: `docs/runbooks/control-plane-verification.md`
- Modify: `docs/runbooks/control-plane-production-deployment.md`
- Modify: `docs/WORKLOG.md`

- [ ] Document the SBOM runner and release-gate usage.
- [ ] Run:
  - `python -m pytest services/control-plane-api/tests/test_sbom_generation.py services/control-plane-api/tests/test_generate_sbom_bundle_script.py services/control-plane-api/tests/test_release_candidate_evidence_generation.py services/control-plane-api/tests/test_release_candidate_certification.py -q`
  - `python services/control-plane-api/scripts/generate_sbom_bundle.py --help`
  - `git -c core.safecrlf=false diff --check`
- [ ] Commit the slice.
