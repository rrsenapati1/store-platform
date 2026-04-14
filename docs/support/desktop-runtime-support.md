# Desktop Runtime Support

Updated: 2026-04-15

## Scope

Use this playbook for packaged Store Desktop issues involving:

- install/update/reinstall
- pending device claims
- activation and sign-in
- branch-hub/spoke posture
- printer/scanner/runtime diagnostics
- offline continuity and replay posture

## Evidence Checklist

Always request:

- tenant name
- branch name
- device code or installation fingerprint
- current desktop release version
- screenshot of the runtime posture or error

## Common Support Paths

### Device Claim Never Becomes Active

Check:

- claim is visible in owner-web
- claim was approved for the correct branch
- customer is using the packaged runtime, not browser preview

### Activation Fails

Check:

- activation code is current
- code was issued for the same device
- staff user belongs to the correct branch
- tenant is not blocked commercially

### Runtime Degraded

Check:

- whether the machine is the intended branch hub
- whether spoke/runtime posture shows conflicts or outbox depth
- whether hardware diagnostics show printer/scanner issues

### Offline Continuity / Replay Review

Check:

- whether the branch is still offline
- whether replay is pending or explicitly flagged for operator review
- whether the issue is one branch or systemic

Escalate to backend/runtime ownership if reconciliation posture is unclear or repeated conflicts continue.

### Update/Reinstall Failure

Check:

- release environment/profile is correct
- update channel shows the expected pending version
- reinstall was attempted only when normal update could not recover the runtime

## Escalate When

- the runtime cannot be bound/activated with correct branch posture
- update/install failures affect more than one branch or version cohort
- runtime continuity or replay suggests a data/conflict risk
