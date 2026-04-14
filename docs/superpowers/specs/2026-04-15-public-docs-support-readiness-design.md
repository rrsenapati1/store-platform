# Public Docs And Support Readiness Design

Date: 2026-04-15  
Task: `CP-027`  
Status: Approved by direct user instruction, no additional review gate requested

## Goal

Create the first release-ready documentation pack for Store so:

- a new tenant can understand the product and complete onboarding from docs alone
- Store Desktop install, upgrade, and recovery behavior are documented for release consumers
- support/admin operators have explicit triage, escalation, lifecycle, and runtime playbooks

This task is not meant to build a separate docs website. It is a repo-Markdown release documentation pass.

## Chosen Documentation Model

The accepted approach is a single Markdown docs pack inside the repo with two main audiences:

- `public-facing release docs`
- `internal support/admin playbooks`

This is the fastest way to reach launch-ready documentation without adding a docs publishing platform before the content is stable.

## Scope

### In Scope

- public product overview
- tenant onboarding guide
- owner-web daily operations guide
- Store Desktop installation, update, and recovery guidance
- troubleshooting guide for release consumers
- support triage workflow
- escalation matrix
- tenant lifecycle support playbook
- Store Desktop/runtime support playbook
- docs index and README updates pointing readers to the new documentation

### Out Of Scope

- a generated docs site
- public marketing copy or landing-page content
- deep architecture walkthroughs already covered by canonical docs
- future mobile-app documentation
- RMS-specific support documentation

## Audience Split

### Public Docs

These documents should explain what to do, not how the internals are implemented.

They must cover:

- what each Store surface is for
  - platform-admin
  - owner-web
  - Store Desktop
- how a tenant reaches first usable branch operations
- how packaged Store Desktop is installed, approved, activated, updated, and recovered
- what common operational errors mean
- when a user can resolve something locally versus when they should contact support

### Support/Admin Docs

These documents should explain how to diagnose and route incidents.

They must cover:

- support intake and severity
- required evidence to collect
- tenant lifecycle state handling
  - trial
  - active
  - grace
  - suspended
- packaged runtime and branch runtime issue handling
- who owns which escalation path

## Documentation Set

### Public Docs

- `docs/public/product-overview.md`
- `docs/public/tenant-onboarding-guide.md`
- `docs/public/owner-web-operations-guide.md`
- `docs/public/store-desktop-installation-guide.md`
- `docs/public/store-desktop-upgrade-and-recovery.md`
- `docs/public/backup-and-recovery-guide.md`
- `docs/public/troubleshooting-guide.md`

### Support/Admin Docs

- `docs/support/support-triage-playbook.md`
- `docs/support/escalation-matrix.md`
- `docs/support/tenant-lifecycle-support.md`
- `docs/support/desktop-runtime-support.md`
- `docs/support/release-consumer-known-issues.md`

### Existing Docs To Update

- `docs/DOCS_INDEX.md`
- `README.md`
- `docs/TASK_LEDGER.md`
- `docs/WORKLOG.md`

## Content Boundary

### Public Docs Must Cover

- product surface orientation
- onboarding sequence from tenant to first branch
- device claim/approval and staff activation at a high level
- Store Desktop install and update expectations
- backup/recovery posture for release consumers
- common failure modes:
  - pending device claim
  - activation denied
  - billing grace/suspension
  - degraded runtime
  - offline replay pending review

### Support Docs Must Cover

- first-response intake
- severity guidance
- evidence checklist:
  - tenant
  - branch
  - device code or installation fingerprint
  - release version
  - screenshots
  - observability status
- commercial lifecycle support actions
- Store Desktop and branch-runtime incident handling
- escalation ownership

### Leave Out

- deep implementation details already covered in canonical docs
- speculative future product surfaces
- internal-only engineering design material that does not help operators or customers

## Organization Rules

- keep user-facing docs in `docs/public/`
- keep support playbooks in `docs/support/`
- keep deployment/security/infra procedures in `docs/runbooks/`
- link to existing runbooks rather than duplicating operational steps
- update the docs index so readers can find the new content without repo archaeology

## Exit Criteria

`CP-027` is complete when:

- the repo contains a coherent public docs pack for onboarding, install, upgrade, recovery, and troubleshooting
- the repo contains a coherent support/admin docs pack for triage, escalation, lifecycle support, and desktop/runtime incidents
- `DOCS_INDEX.md` and `README.md` point readers to the right starting documents
- the ledger and worklog reflect the new release documentation boundary
