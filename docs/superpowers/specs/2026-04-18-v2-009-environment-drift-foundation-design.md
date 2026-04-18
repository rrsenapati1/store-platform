# V2-009 Environment Drift Verification Foundation Design

Date: 2026-04-18
Task: `V2-009`
Status: Drafted

## Goal

Add the first repo-owned environment drift verification lane so `V2-009` can produce machine-readable evidence that a deployed staging or production control plane still matches the repo’s declared environment contract.

This slice is about config and runtime posture drift, not infrastructure inventory discovery.

## Why This Is The Right Next Slice

`V2-009` now has evidence for:

- local performance
- deployed HTTP load
- security controls
- operational alerts
- restore drills
- rollback eligibility
- vulnerability scans

What it still lacks is a bounded answer to:

- whether the deployed environment still matches the repo’s required shared-environment posture
- whether a release candidate is being certified against a drifted runtime

Right now that check is implicit in runbooks. That is too soft for launch-grade hardening.

## Chosen Model

The accepted model is:

- one control-plane `environment contract` read model
- one repo-owned drift evaluator
- one deployed verifier CLI
- one JSON drift report
- release-evidence rendering
- release-certification gate when a drift report is supplied

This keeps the slice bounded around what the control plane can actually know about itself.

## Scope

### In Scope

- effective environment-contract read model from the control plane
- drift evaluation against repo-owned staging/prod expectations
- machine-readable JSON drift report
- release-evidence integration
- release-certification integration
- runbook updates

### Out Of Scope

- VM inventory discovery
- systemd unit inspection over SSH
- nginx file parsing on the target host
- firewall rule inspection
- third-party secret-manager inspection
- desktop client drift detection

Those require host-level or external-system access and are intentionally out of scope for the first slice.

## Read Model Boundary

Add a new system read model, exposed as:

- `GET /v1/system/environment-contract`

It should return effective control-plane-owned deployment posture such as:

- `deployment_environment`
- `public_base_url`
- `release_version`
- `log_format`
- `sentry_configured`
- `sentry_environment`
- `object_storage_configured`
- `object_storage_bucket`
- `object_storage_prefix`
- `operations_worker`
  - configured
  - poll_seconds
  - batch_size
  - lease_seconds
- `security_controls`
  - secure headers enabled
  - HSTS enabled
  - CSP
  - rate-limit values

This endpoint should summarize only the values the control plane already knows from its effective settings.

## Drift Rules

The first rule set should stay explicit and conservative.

For shared `staging` and `prod` environments, verify:

- `deployment_environment` matches the expected environment
- `public_base_url` matches the verifier base URL
- `log_format == json`
- `sentry_configured == true`
- `sentry_environment == expected environment`
- `object_storage_configured == true`
- `object_storage_bucket` is non-empty
- `object_storage_prefix` contains the expected environment segment
- `operations_worker.configured == true`
- `operations_worker.batch_size > 0`
- `operations_worker.lease_seconds > 0`
- `secure_headers_enabled == true`
- `secure_headers_hsts_enabled == true`
- `secure_headers_csp` is non-empty
- `rate_limit_window_seconds > 0`
- auth, activation, and webhook rate limits are all positive

For `dev`, the drift verifier does not need a full contract in this first slice.

## Report Contract

The verifier should write one JSON report shaped like:

- `status`
  - `passed`
  - `failed`
- `environment`
- `release_version`
- `generated_at`
- `checks`
- `failing_checks`
- `summary`

Each check should include:

- `name`
- `status`
  - `passed`
  - `failed`
- `observed_value`
- `expected_value`
- `reason`

## Release Integration

Extend:

- [generate_release_candidate_evidence.py](/d:/codes/projects/store/services/control-plane-api/scripts/generate_release_candidate_evidence.py)
- [certify_release_candidate.py](/d:/codes/projects/store/services/control-plane-api/scripts/certify_release_candidate.py)

So they can consume:

- an optional environment drift report

Release evidence should render:

- overall drift status
- failing checks
- compact check lines for the most important posture categories

Release certification should expose:

- `environment_drift_verified`

This gate should stay optional for compatibility, but a supplied failed drift report must block approval.

## Testing

The slice should cover:

- environment-contract route behavior
- drift evaluator pass/fail behavior
- verifier CLI report writing and exit status
- release-evidence rendering
- release-certification gate behavior

## Success Criteria

This slice is complete when:

- the control plane exposes its effective environment contract as a read model
- the repo can generate a normalized drift report for staging/prod
- release evidence can render drift posture
- release certification can gate on drift posture when supplied
- docs explain that this verifies control-plane-owned config posture, not host inventory
