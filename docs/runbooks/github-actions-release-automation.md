# GitHub Actions Release Automation

Updated: 2026-04-18

## Purpose

`CP-026` adds the first GitHub-based automation boundary for Store:

- pull-request verification
- tag-based release artifact builds
- GitHub Release attachment for backend, web, and desktop artifacts

This automation does **not** deploy directly to your VMs and does **not** publish to object storage. Operators still control promotion from GitHub artifacts into the existing `CP-024` and `CP-022` deployment runbooks.

## Workflows

### `ci`

Path:

- `.github/workflows/ci.yml`

Triggers:

- `pull_request`
- `push` to `main`

Responsibilities:

- backend verification on Ubuntu
- owner-web and platform-admin verification on Ubuntu
- store-desktop verification on Windows
- release-automation script and workflow-contract checks on Ubuntu

Expected job boundaries:

- `backend`
- `web`
- `desktop`
- `release-automation`

### `release-artifacts`

Path:

- `.github/workflows/release-artifacts.yml`

Triggers:

- push tags matching `v*`
- `workflow_dispatch`

Responsibilities:

- build `store-control-plane-<version>.tar.gz`
- emit `store-control-plane-<version>.manifest.json`
- emit `store-control-plane-<version>.provenance.json`
- build and archive `platform-admin` and `owner-web` dist artifacts
- build signed Windows Store Desktop installer artifacts
- attach artifacts to a GitHub Release when triggered from a tag

## Required GitHub Secrets

Only the release workflow needs secrets, and only for desktop signing or release-profile overrides.

Required:

- `TAURI_SIGNING_PRIVATE_KEY`

Optional:

- `TAURI_SIGNING_PRIVATE_KEY_PASSWORD`
- `STORE_DESKTOP_RELEASE_CONTROL_PLANE_BASE_URL`
- `STORE_DESKTOP_RELEASE_UPDATER_ENDPOINT`
- `STORE_DESKTOP_RELEASE_UPDATER_PUBLIC_KEY`

This workflow intentionally does **not** use:

- VM SSH credentials
- object-storage write credentials
- database credentials

## PR Verification Contract

A pull request is expected to pass:

- backend pytest
- owner-web tests, typecheck, and build
- platform-admin tests, typecheck, and build
- store-desktop tests, typecheck, build, and native cargo tests
- release-automation script tests and workflow contract assertions

If a release-related script changes, the automation tests must change with it. The workflow should not be the only place that “knows” how release packaging works.

## Release Tag Contract

Use tags in the form:

- `v0.1.0`
- `v1.0.0`

Tag pushes trigger:

- control-plane release bundle build
- owner-web and platform-admin artifact build
- Store Desktop signed installer build with `prod` desktop profile
- GitHub Release artifact attachment

Manual `workflow_dispatch` allows:

- ad hoc release artifact generation
- staging desktop-profile artifact creation
- verification of packaging without publishing a GitHub Release

## Artifact Handoff

GitHub Actions produces artifacts. Operators promote them.

### Control Plane

Download:

- `store-control-plane-<version>.tar.gz`
- `store-control-plane-<version>.manifest.json`
- `store-control-plane-<version>.provenance.json`

Then continue with:

- [control-plane-production-deployment.md](./control-plane-production-deployment.md)

The manifest is the operator-visible rollback metadata source for:

- `release_version`
- `alembic_head`
- bundle name
- build timestamp

The provenance sidecar is the operator-visible artifact-attestation source for:

- archive and manifest SHA-256 hashes
- source commit, tree, ref, and origin remote
- source worktree cleanliness at packaging time

### Web Apps

Download:

- `platform-admin-<version>.tar.gz`
- `owner-web-<version>.tar.gz`

Then promote those artifacts through your existing hosting pipeline or static asset deployment process.

### Store Desktop

Download:

- Windows NSIS installer
- matching `.sig`
- release metadata JSON

Then continue with:

- [store-desktop-packaging-distribution.md](./store-desktop-packaging-distribution.md)

The update manifest is still generated after the artifact reaches its final update-channel URL.

## Failure Posture

- If `ci` fails on a pull request, do not bypass it with manual “looks good” review.
- If `release-artifacts` fails on a tag, fix the workflow or packaging script and re-tag according to your release policy.
- If desktop signing secrets are missing, the release workflow must fail instead of publishing an unsigned desktop payload.
- If GitHub artifact publication succeeds but manual promotion fails, treat that as an operator handoff failure, not as CI success for deployment.

## Manual Promotion Boundary

This task deliberately stops before:

- SSHing into the app VM from GitHub
- uploading to object storage from GitHub
- applying migrations from GitHub Actions
- restarting production services from GitHub Actions

That boundary remains manual until you explicitly choose to trust GitHub as part of the deployment authority path.
