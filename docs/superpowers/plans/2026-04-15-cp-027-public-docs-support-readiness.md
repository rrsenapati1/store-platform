# CP-027 Public Docs And Support Readiness Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a release-ready Markdown documentation pack covering tenant onboarding, Store Desktop install/update/recovery, troubleshooting, and internal support/admin playbooks.

**Architecture:** Keep the documentation split by audience and responsibility: `docs/public/` for tenant-facing guidance, `docs/support/` for internal support/admin playbooks, and existing `docs/runbooks/` as the operational source of truth for deployment and infra. Update the docs entrypoints so the new material is discoverable without adding a separate docs site.

**Tech Stack:** Markdown, repo docs index, README, runbook cross-links

---

## Planned File Structure

### Public docs

- `docs/public/product-overview.md`
- `docs/public/tenant-onboarding-guide.md`
- `docs/public/owner-web-operations-guide.md`
- `docs/public/store-desktop-installation-guide.md`
- `docs/public/store-desktop-upgrade-and-recovery.md`
- `docs/public/backup-and-recovery-guide.md`
- `docs/public/troubleshooting-guide.md`

### Support docs

- `docs/support/support-triage-playbook.md`
- `docs/support/escalation-matrix.md`
- `docs/support/tenant-lifecycle-support.md`
- `docs/support/desktop-runtime-support.md`
- `docs/support/release-consumer-known-issues.md`

### Existing docs to update

- `docs/DOCS_INDEX.md`
- `README.md`
- `docs/TASK_LEDGER.md`
- `docs/WORKLOG.md`

---

### Task 1: Add the public release docs pack

**Files:**
- Create: `docs/public/product-overview.md`
- Create: `docs/public/tenant-onboarding-guide.md`
- Create: `docs/public/owner-web-operations-guide.md`
- Create: `docs/public/store-desktop-installation-guide.md`
- Create: `docs/public/store-desktop-upgrade-and-recovery.md`
- Create: `docs/public/backup-and-recovery-guide.md`
- Create: `docs/public/troubleshooting-guide.md`

- [ ] **Step 1: Create the `docs/public/` directory and write the product overview and tenant onboarding guide**
- [ ] **Step 2: Write the owner-web operations guide and Store Desktop installation guide**
- [ ] **Step 3: Write the Store Desktop upgrade/recovery guide, backup/recovery guide, and troubleshooting guide**
- [ ] **Step 4: Review the new public docs for scope overlap and replace duplicated operational detail with links to existing runbooks**
- [ ] **Step 5: Commit**

### Task 2: Add the internal support/admin documentation pack

**Files:**
- Create: `docs/support/support-triage-playbook.md`
- Create: `docs/support/escalation-matrix.md`
- Create: `docs/support/tenant-lifecycle-support.md`
- Create: `docs/support/desktop-runtime-support.md`
- Create: `docs/support/release-consumer-known-issues.md`

- [ ] **Step 1: Create the `docs/support/` directory and write the support triage playbook plus escalation matrix**
- [ ] **Step 2: Write the tenant lifecycle support playbook and desktop/runtime support playbook**
- [ ] **Step 3: Write the release-consumer known issues guide**
- [ ] **Step 4: Review the support docs for consistent severity, evidence, and escalation language**
- [ ] **Step 5: Commit**

### Task 3: Update docs entrypoints and close the task

**Files:**
- Modify: `docs/DOCS_INDEX.md`
- Modify: `README.md`
- Modify: `docs/TASK_LEDGER.md`
- Modify: `docs/WORKLOG.md`

- [ ] **Step 1: Update `docs/DOCS_INDEX.md` with public docs and support playbook entrypoints**
- [ ] **Step 2: Update the repo `README.md` with a short release-docs starting point**
- [ ] **Step 3: Run `git diff --check`**
- [ ] **Step 4: Run a docs-integrity check that confirms every new public/support file exists and is referenced from the docs index or README**
- [ ] **Step 5: Mark `CP-027` done in the ledger and add the worklog entry**
- [ ] **Step 6: Commit**
