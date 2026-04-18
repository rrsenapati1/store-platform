# V2-009 Security Verification Foundation Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deployed security verification for effective security controls, secure headers, and bounded live throttling probes, then thread that result into release evidence and certification.

**Architecture:** Extend the existing control-plane verification stack instead of creating a separate security tool. Publish effective security controls through a new system route, use those settings to drive safe live auth and webhook throttling probes in `verify_deployed_control_plane.py`, and treat the resulting security posture as a first-class release-evidence input and certification gate.

**Tech Stack:** FastAPI, Pydantic, Python scripts, pytest, Markdown runbooks

---

## Task 1: Add failing tests

**Files:**
- Modify: `services/control-plane-api/tests/test_system_routes.py`
- Modify: `services/control-plane-api/tests/test_verify_deployed_control_plane.py`
- Modify: `services/control-plane-api/tests/test_release_candidate_evidence_generation.py`
- Modify: `services/control-plane-api/tests/test_release_candidate_certification.py`

- [ ] Add a failing system-route test for `/v1/system/security-controls`.
- [ ] Add failing deployed-verifier tests for secure headers, auth throttling, and webhook throttling.
- [ ] Add failing release-evidence rendering coverage for security posture.
- [ ] Add failing certification coverage for a blocked security result.
- [ ] Run the focused tests and confirm they fail for missing security verification behavior.

## Task 2: Publish effective security controls

**Files:**
- Modify: `services/control-plane-api/store_control_plane/schemas/system.py`
- Modify: `services/control-plane-api/store_control_plane/schemas/__init__.py`
- Modify: `services/control-plane-api/store_control_plane/routes/system.py`

- [ ] Add response models for effective security controls and throttle buckets.
- [ ] Add `GET /v1/system/security-controls`.
- [ ] Return non-secret effective settings for secure headers and rate limits.
- [ ] Re-run system-route tests and confirm they pass.

## Task 3: Implement deployed security verification

**Files:**
- Modify: `services/control-plane-api/scripts/verify_deployed_control_plane.py`

- [ ] Add header-aware and status-aware HTTP helpers for deployed verification.
- [ ] Fetch `/v1/system/security-controls` during deployed verification.
- [ ] Verify secure headers on `/v1/system/health`.
- [ ] Run bounded invalid auth-exchange probes until the configured auth limit is exceeded.
- [ ] Run bounded invalid billing-webhook probes until the configured webhook limit is exceeded.
- [ ] Return structured `security_result` data from the verifier.
- [ ] Re-run the deployed-verifier tests and confirm they pass.

## Task 4: Integrate security posture into evidence and certification

**Files:**
- Modify: `services/control-plane-api/scripts/generate_release_candidate_evidence.py`
- Modify: `services/control-plane-api/scripts/certify_release_candidate.py`

- [ ] Render a dedicated security section in release-candidate evidence.
- [ ] Add a `security_controls_verified` gate to certification.
- [ ] Block certification when a supplied security result failed.
- [ ] Re-run the release-evidence and certification tests and confirm they pass.

## Task 5: Update docs and verify

**Files:**
- Modify: `docs/runbooks/control-plane-verification.md`
- Modify: `docs/runbooks/control-plane-production-deployment.md`
- Modify: `docs/WORKLOG.md`
- Modify: `docs/TASK_LEDGER.md`

- [ ] Document the new `/v1/system/security-controls` route and live throttling probes.
- [ ] Document security verification as part of release evidence.
- [ ] Update the worklog and only adjust the task ledger if the visible `V2-009` state changes.
- [ ] Run focused verification:
  - `python -m pytest services/control-plane-api/tests/test_system_routes.py services/control-plane-api/tests/test_verify_deployed_control_plane.py services/control-plane-api/tests/test_release_candidate_evidence_generation.py services/control-plane-api/tests/test_release_candidate_certification.py services/control-plane-api/tests/test_rate_limiting.py services/control-plane-api/tests/test_security_headers.py -q`
  - `python services/control-plane-api/scripts/verify_deployed_control_plane.py --help`
  - `git -c core.safecrlf=false diff --check`

