# Support Triage Playbook

Updated: 2026-04-15

## Goal

Provide a consistent first-response workflow for Store support/admin operators.

## Intake Checklist

Always collect:

- tenant name
- branch name
- reporter name and role
- affected surface
  - owner-web
  - Store Desktop
  - billing/commercial
  - release/update
- screenshot or copied error text
- current release version if desktop-related
- installation fingerprint or device code if device-related

## Severity Guidance

- `SEV-1`
  - onboarding blocked for a live customer
  - branch checkout/runtime broadly unavailable
  - billing/commercial state incorrectly suspends a live tenant
- `SEV-2`
  - a branch is degraded but not fully down
  - a packaged desktop update/regression affects one branch or a limited user set
- `SEV-3`
  - isolated user issue, confusing UX, or recoverable workflow problem

## Triage Flow

1. identify the affected surface
2. collect the minimum evidence
3. check whether the issue matches a known problem or runbook
4. decide whether support can resolve directly or must escalate

## Immediate Routing

- commercial lifecycle problem
  - check [tenant-lifecycle-support.md](./tenant-lifecycle-support.md)
- packaged desktop/runtime problem
  - check [desktop-runtime-support.md](./desktop-runtime-support.md)
- release/install/update problem
  - check [release-consumer-known-issues.md](./release-consumer-known-issues.md)

## Evidence Standards

Do not escalate vague reports such as “desktop is not working” without:

- tenant and branch
- current desktop release version if applicable
- screenshot or error text
- whether the issue is one machine or the whole branch

## Escalation Trigger

Escalate when:

- support cannot identify the correct owner domain
- the issue is severity 1
- the issue implies backend inconsistency, billing inconsistency, or release regression
- the issue requires control-plane or packaged-runtime code investigation
