# V2-009 Alert Verification Foundation Design

Date: 2026-04-18
Task: `V2-009`
Status: Drafted after design approval

## Goal

Turn the existing documented alert thresholds into a repo-owned verification path that produces machine-readable operational-readiness evidence and can block release certification when the deployed environment is already outside acceptable alert posture.

This slice closes the current gap between:

- documented threshold policy in [security-observability-operations.md](/d:/codes/projects/store/docs/runbooks/security-observability-operations.md)
- deployed verification in [verify_deployed_control_plane.py](/d:/codes/projects/store/services/control-plane-api/scripts/verify_deployed_control_plane.py)
- release evidence and certification in:
  - [generate_release_candidate_evidence.py](/d:/codes/projects/store/services/control-plane-api/scripts/generate_release_candidate_evidence.py)
  - [certify_release_candidate.py](/d:/codes/projects/store/services/control-plane-api/scripts/certify_release_candidate.py)

Right now the repo can verify health, security posture, performance, restore drills, and vulnerability scans, but alert-readiness is still mostly a human reading a runbook and making a judgment call. That is too soft for the final `V2-009` hardening path.

## Chosen Model

The accepted model is:

- one normalized operational-alert evaluator
- one CLI verifier for deployed alert posture
- one JSON report contract
- release evidence that renders the alert posture
- release certification that can block on failed or missing alert verification

This is intentionally narrower than a full alerting platform. It verifies whether the deployed environment already violates the platform’s own alert thresholds; it does not implement hosted alert delivery.

## Scope

### In Scope

- explicit evaluation of current operational alert thresholds from deployed control-plane state
- machine-readable JSON alert verification report
- release-evidence integration
- release-certification gate integration
- runbook updates for operational readiness verification

### Out Of Scope

- PagerDuty, Slack, Teams, or email alert delivery
- Sentry incident ingestion APIs
- hosted monitoring dashboards
- metrics backend rollout
- automatic remediation or restart logic
- alert acknowledgement workflow

Those can follow later if the launch program still needs them.

## Data Sources

The alert verifier should stay inside the current control-plane authority boundary.

Use:

- `/v1/platform/observability/summary`
  - operations posture
  - runtime degradation posture
  - backup freshness posture
- deployed security verification result from [verify_deployed_control_plane.py](/d:/codes/projects/store/services/control-plane-api/scripts/verify_deployed_control_plane.py)
  - secure headers
  - auth/webhook rate-limit posture

This avoids creating a new dependency on third-party monitoring systems for the first slice.

## Report Contract

The verifier should write one JSON report shaped like:

- `status`
  - `passed`
  - `failed`
- `environment`
- `release_version`
- `generated_at`
- `alert_checks`
- `failing_checks`
- `summary`

Each `alert_checks` entry should include:

- `name`
- `status`
  - `passed`
  - `failed`
  - `not-run`
- `observed_value`
- `threshold`
- `reason`

Important boundary:

- the report is the operational-readiness artifact
- not just console output
- it should be suitable for both release evidence rendering and certification gating

## Initial Alert Checks

The first slice should enforce the documented thresholds that are already meaningful and release-relevant.

### Operations Dead Letter

Check:

- `operations_dead_letter_clear`

Rule:

- fail when `dead_letter_count > 0`

Reasoning:

- dead-lettered jobs already indicate unresolved control-plane failures, not just transient noise

### Retryable Failures

Check:

- `operations_retryable_within_limit`

Rule:

- fail when `retryable_count` exceeds a configurable threshold

Recommended defaults:

- `staging`: small non-zero allowance
- `prod`: stricter, ideally `0` for certification

### Runtime Degradation

Check:

- `runtime_degradation_within_limit`

Rule:

- fail when `degraded_branch_count` exceeds threshold

Recommended default:

- `prod`: `0` for certification

### Backup Freshness

Check:

- `backup_freshness_within_limit`

Rule:

- fail when:
  - backup status is not `ok`, or
  - backup age exceeds allowed hours

Recommended default:

- `<= 26` hours

### Security Verification

Check:

- `security_verification_passed`

Rule:

- fail when the already-computed security verification result is not `passed`

This keeps alert verification aligned with the broader `V2-009` hardening posture instead of allowing a release to ignore a known security failure.

## Threshold Configuration

The first slice should allow the verifier to accept threshold overrides, but it should ship with conservative defaults so operators can run it without building a custom config system first.

Suggested inputs:

- `max_retryable_count`
- `max_degraded_branch_count`
- `max_backup_age_hours`

Keep these as script arguments or function parameters in the first slice. Do not add a persisted admin UI for them yet.

## Verifier Flow

The alert verifier should:

1. normalize base URL and expected environment inputs
2. load deployed security verification using the existing deployed verifier
3. fetch `/v1/platform/observability/summary`
4. evaluate each alert check against thresholds
5. build a normalized JSON report
6. write the report to disk
7. exit non-zero on failure

The evaluator should be testable without live network calls by injecting the deployed-verification function and HTTP request function in tests.

## Release Evidence Integration

[generate_release_candidate_evidence.py](/d:/codes/projects/store/services/control-plane-api/scripts/generate_release_candidate_evidence.py) should accept an optional alert-verification report path and render a dedicated section:

- overall alert verification status
- dead-letter status
- retryable-failure status
- runtime-degradation status
- backup-freshness status
- security-verification status
- failing checks

If the report is omitted, evidence should show `not-run` explicitly.

## Release Certification Integration

[certify_release_candidate.py](/d:/codes/projects/store/services/control-plane-api/scripts/certify_release_candidate.py) should add a gate:

- `operational_alerts_verified`

Recommended rule:

- certification is blocked when the alert report is missing for a release that expects it
- certification is blocked when the report status is `failed`

This is the enterprise value of the slice. Without the gate, the alert report is only advisory.

## Implementation Boundaries

Add:

- `services/control-plane-api/store_control_plane/operational_alerts.py`
- `services/control-plane-api/scripts/verify_operational_alert_posture.py`

Extend:

- `services/control-plane-api/scripts/generate_release_candidate_evidence.py`
- `services/control-plane-api/scripts/certify_release_candidate.py`
- `docs/runbooks/security-observability-operations.md`
- `docs/runbooks/control-plane-production-deployment.md`

Do not redesign:

- the platform observability summary API
- the security verifier
- the performance or restore-drill evidence lanes

This slice should compose with those existing mechanisms.

## Testing Expectations

Backend tests should cover:

- dead-letter failure
- retryable-threshold failure
- degraded-branch failure
- backup-age breach
- security-result propagation
- passed posture when all checks are within threshold

Script tests should cover:

- JSON report output
- non-zero exit on failed posture
- `--help`

Release tests should cover:

- alert section rendering in release evidence
- `operational_alerts_verified` blocking in certification

Tests must not require a live deployed environment.

## Exit Criteria

`V2-009` alert verification foundation is complete when:

- the repo can verify deployed operational alert posture through one script and get a normalized JSON report
- release evidence renders alert posture explicitly
- release certification can block on failed or missing alert verification
- runbooks point operators to one repeatable verification path instead of a manual checklist only
