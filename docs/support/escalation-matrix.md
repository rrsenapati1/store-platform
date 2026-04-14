# Escalation Matrix

Updated: 2026-04-15

## Purpose

Define who owns which category of Store issue after support completes first triage.

## Ownership Matrix

- `Commercial lifecycle / billing provider`
  - symptoms:
    - tenant stuck in grace/suspended unexpectedly
    - payment/provider recovery mismatch
  - escalate to:
    - billing/provider owner

- `Control-plane backend`
  - symptoms:
    - onboarding state mismatch
    - device approval inconsistency
    - lifecycle state mismatch
    - sync/runtime summary clearly wrong
  - escalate to:
    - control-plane/backend owner

- `Packaged Store Desktop runtime`
  - symptoms:
    - activation/sign-in failures with correct branch posture
    - runtime release profile issues
    - update/install regressions
    - local runtime hardware/diagnostic failures
  - escalate to:
    - desktop/runtime owner

- `Infra / deployment / recovery`
  - symptoms:
    - health/backup/deployment verification failures
    - release artifact or production environment mismatch
  - escalate to:
    - infra/operator owner

## Severity Overrides

Even if ownership is clear, escalate immediately when:

- multiple tenants are affected
- multiple branches are blocked after a release
- a live tenant is incorrectly suspended
- runtime continuity/replay posture suggests data/conflict risk
