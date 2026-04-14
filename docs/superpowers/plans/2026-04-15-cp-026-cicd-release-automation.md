# CP-026 CI/CD And Release Automation Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add GitHub-based PR verification, tag-based release artifact builds, and repo-owned release packaging for backend, web, and packaged desktop surfaces.

**Architecture:** Keep deployment promotion manual, but make verification and artifact creation reproducible inside GitHub Actions. Use repo-owned scripts for release packaging so workflows stay thin and testable, split CI jobs by backend/web/desktop responsibility, and publish release artifacts on tags without giving GitHub direct VM or object-storage authority.

**Tech Stack:** GitHub Actions, Node.js, npm workspaces, Python, pytest, Rust, Tauri, Markdown runbooks

---

## Planned File Structure

### Release packaging scripts

- `scripts/release-archive-utils.mjs`
  - shared archive helpers and exclusion rules
- `scripts/package-control-plane-release.mjs`
  - create the `services/control-plane-api` release bundle
- `scripts/package-web-release.mjs`
  - archive built `dist/` output for `owner-web` and `platform-admin`
- `scripts/stage-store-desktop-release-artifacts.mjs`
  - collect built installer and signature into a stable artifact directory

### Release script tests

- `scripts/package-control-plane-release.test.mjs`
- `scripts/package-web-release.test.mjs`
- `scripts/stage-store-desktop-release-artifacts.test.mjs`
- `scripts/github-workflows.test.mjs`

### Workflow configuration

- `.github/workflows/ci.yml`
- `.github/workflows/release-artifacts.yml`

### Repo command surface

- `package.json`
  - add stable CI/release npm scripts used by GitHub Actions

### Runbooks and release docs

- `docs/runbooks/github-actions-release-automation.md`
- `docs/runbooks/control-plane-production-deployment.md`
- `docs/runbooks/store-desktop-packaging-distribution.md`
- `docs/TASK_LEDGER.md`
- `docs/WORKLOG.md`

---

### Task 1: Add repo-owned backend and web release packaging scripts

**Files:**
- Create: `scripts/release-archive-utils.mjs`
- Create: `scripts/package-control-plane-release.mjs`
- Create: `scripts/package-web-release.mjs`
- Create: `scripts/package-control-plane-release.test.mjs`
- Create: `scripts/package-web-release.test.mjs`

- [ ] **Step 1: Write failing Node tests for control-plane bundle contents, exclusion rules, and web dist archive packaging**
- [ ] **Step 2: Run `node --test scripts/package-control-plane-release.test.mjs scripts/package-web-release.test.mjs` and confirm red**
- [ ] **Step 3: Implement shared archive helpers with deterministic output structure and exclusion rules**
- [ ] **Step 4: Implement the control-plane release bundle CLI with versioned output naming**
- [ ] **Step 5: Implement the web release archive CLI for `platform-admin` and `owner-web`**
- [ ] **Step 6: Re-run `node --test scripts/package-control-plane-release.test.mjs scripts/package-web-release.test.mjs` and confirm green**
- [ ] **Step 7: Commit**

### Task 2: Add desktop release artifact staging and automation command surface

**Files:**
- Create: `scripts/stage-store-desktop-release-artifacts.mjs`
- Create: `scripts/stage-store-desktop-release-artifacts.test.mjs`
- Modify: `package.json`

- [ ] **Step 1: Write a failing Node test for collecting the built installer, signature, and release metadata into a stable artifact directory**
- [ ] **Step 2: Run `node --test scripts/stage-store-desktop-release-artifacts.test.mjs` and confirm red**
- [ ] **Step 3: Implement the desktop artifact staging CLI against the current Tauri bundle layout**
- [ ] **Step 4: Add root npm scripts for backend, web, desktop, and release-automation verification so workflows use stable repo commands**
- [ ] **Step 5: Re-run `node --test scripts/stage-store-desktop-release-artifacts.test.mjs` and confirm green**
- [ ] **Step 6: Commit**

### Task 3: Add GitHub Actions workflows with testable contract checks

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `.github/workflows/release-artifacts.yml`
- Create: `scripts/github-workflows.test.mjs`

- [ ] **Step 1: Write a failing Node test that asserts the workflow files contain the expected triggers, jobs, and command boundaries**
- [ ] **Step 2: Run `node --test scripts/github-workflows.test.mjs` and confirm red**
- [ ] **Step 3: Implement the PR verification workflow with backend, web, desktop, and automation jobs**
- [ ] **Step 4: Implement the tag/manual release workflow with backend bundle, web artifacts, desktop installer build, artifact upload, and GitHub-release attachment on tags**
- [ ] **Step 5: Re-run `node --test scripts/github-workflows.test.mjs` and confirm green**
- [ ] **Step 6: Commit**

### Task 4: Add runbooks and close the task with full verification

**Files:**
- Create: `docs/runbooks/github-actions-release-automation.md`
- Modify: `docs/runbooks/control-plane-production-deployment.md`
- Modify: `docs/runbooks/store-desktop-packaging-distribution.md`
- Modify: `docs/TASK_LEDGER.md`
- Modify: `docs/WORKLOG.md`

- [ ] **Step 1: Document the PR verification workflow, release-tag workflow, required GitHub secrets, and the manual promotion boundary**
- [ ] **Step 2: Update the control-plane and desktop runbooks to explain how GitHub artifacts hand off into the existing operator deployment flows**
- [ ] **Step 3: Run `node --test scripts/package-control-plane-release.test.mjs scripts/package-web-release.test.mjs scripts/stage-store-desktop-release-artifacts.test.mjs scripts/github-workflows.test.mjs`**
- [ ] **Step 4: Run `python -m pytest services/control-plane-api/tests -q`**
- [ ] **Step 5: Run `npm run test --workspace @store/platform-admin`**
- [ ] **Step 6: Run `npm run test --workspace @store/owner-web`**
- [ ] **Step 7: Run `npm run test --workspace @store/store-desktop`**
- [ ] **Step 8: Run `npm run typecheck --workspace @store/platform-admin`**
- [ ] **Step 9: Run `npm run typecheck --workspace @store/owner-web`**
- [ ] **Step 10: Run `npm run typecheck --workspace @store/store-desktop`**
- [ ] **Step 11: Run `npm run build --workspace @store/platform-admin`**
- [ ] **Step 12: Run `npm run build --workspace @store/owner-web`**
- [ ] **Step 13: Run `npm run build --workspace @store/store-desktop`**
- [ ] **Step 14: Run `cargo test --manifest-path apps/store-desktop/src-tauri/Cargo.toml --lib`**
- [ ] **Step 15: Run `node scripts/package-control-plane-release.mjs --help`**
- [ ] **Step 16: Run `node scripts/package-web-release.mjs --help`**
- [ ] **Step 17: Run `node scripts/stage-store-desktop-release-artifacts.mjs --help`**
- [ ] **Step 18: Mark `CP-026` done in the ledger and add the worklog entry**
- [ ] **Step 19: Commit**
