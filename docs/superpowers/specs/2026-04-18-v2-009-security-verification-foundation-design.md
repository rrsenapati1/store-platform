# V2-009 Security Verification Foundation Design

## Goal

Add the first launch-grade security verification slice for `V2-009` by turning the current static security controls into repeatable deployed evidence:

- publish effective security-control posture from the control plane
- verify secure headers on live responses
- prove deployed auth and webhook throttling with bounded live probes
- surface the security result in release evidence and release certification

This slice is about verification and evidence, not new auth or WAF features.

## Why This Is The Right Next V2-009 Slice

The repo already has:

- `RateLimitMiddleware`
- `SecurityHeadersMiddleware`
- tests proving those controls exist locally
- deployed verification for health, authority boundary, and optional actor auth
- performance and restore-drill evidence in release reporting

What is still missing is launch-grade proof that the deployed environment still enforces those security controls after real deployment and configuration drift.

## Recommended Approach

Extend the existing deployed verification seam rather than creating a second security toolchain.

That means:

- add one explicit system read model for effective security controls
- extend `verify_deployed_control_plane.py` to inspect headers and run safe live throttle probes
- extend release evidence and certification to include security posture

This keeps release readiness centralized in the same verification lane already used for environment, cutover, performance, and recovery evidence.

## Scope

Included:

- `GET /v1/system/security-controls`
- live secure-header verification
- live auth exchange throttling probe
- live billing-webhook throttling probe
- release evidence rendering for security posture
- certification gates for security verification
- focused tests and runbook updates

Not included:

- new runtime security controls
- vulnerability scanning
- secrets rotation automation
- WAF or DDoS integrations
- penetration testing workflows

## Architecture

### 1. System Security-Controls Read Model

Add a new route:

- `GET /v1/system/security-controls`

It should return non-secret effective control posture such as:

- secure headers enabled
- HSTS enabled
- effective CSP
- auth rate-limit window and request limit
- activation rate-limit window and request limit
- webhook rate-limit window and request limit

This gives the deployed verifier an authoritative source for the active security configuration instead of hardcoded assumptions.

### 2. Deployed Security Verification

Extend `verify_deployed_control_plane.py` so it still verifies:

- health
- environment
- release version
- authority boundary
- optional authenticated actor

Then add security verification:

- fetch `/v1/system/security-controls`
- verify secure headers on `/v1/system/health`
- run bounded invalid-request probes against:
  - `/v1/auth/oidc/exchange`
  - `/v1/billing/webhooks/cashfree/payments`

The probe contract should be:

- send invalid but well-formed requests
- expect non-429 responses up to the configured limit
- expect `429` with `Retry-After` on the next request

That proves live throttling without mutating tenant state.

### 3. Release Evidence And Certification

Release evidence should render a dedicated security section showing:

- security verification status
- secure-header result
- auth throttle result
- webhook throttle result

Release certification should gain a new gate:

- `security_controls_verified`

If security verification is supplied and failed, release certification must block.

## Error Handling

Security verification failures should be explicit and structured.

Examples:

- missing secure headers
- wrong CSP or missing HSTS when enabled
- auth exchange never throttles
- webhook route never throttles
- security-controls endpoint mismatch

These should produce a `failed` security result, not a warning-only posture.

## Testing

Add focused tests for:

- `GET /v1/system/security-controls`
- deployed verifier secure-header validation
- deployed verifier auth throttle probe
- deployed verifier webhook throttle probe
- release evidence rendering with security posture
- release certification blocking on failed security verification

These tests should use injected fetchers, not real internet calls.

## Docs

Update:

- `docs/runbooks/control-plane-verification.md`
- `docs/runbooks/control-plane-production-deployment.md`

The verification runbook should document the live security probe behavior and expected rate-limit side effects.

The deployment runbook should mention security verification as part of release-candidate evidence.

## Success Criteria

This slice is complete when:

- the control plane publishes effective security-control posture
- deployed verification proves secure headers and live throttling behavior
- release evidence records security posture
- certification can block on failed security verification
- focused verification passes

