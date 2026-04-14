# CI/CD And Release Automation Design

Date: 2026-04-15  
Task: `CP-026`  
Status: Approved by direct user instruction, no additional review gate requested

## Goal

Add the first GitHub-based automation layer for Store so pull requests run consistent verification, release tags produce reproducible artifacts, and deployment promotion follows one documented handoff from GitHub artifacts to the self-managed VM runbooks.

This task is not meant to fully automate production deployment onto the VMs. It closes the automation gap around verification, build reproducibility, packaging, and release artifact publication.

## Chosen Delivery Model

The accepted model is:

- `pull requests`
  - verification only
  - no desktop installer publishing
  - no VM deployment
- `tagged releases`
  - build release artifacts
  - attach artifacts to a GitHub release
  - keep promotion to object storage and VMs manual through the existing runbooks

This is the right first slice because it increases automation without turning GitHub Actions into your deployment authority before the VM estate is mature enough for that.

## Rejected Alternatives

### Full GitHub-to-VM deployment

Rejected for this slice because:

- it would require SSH deployment authority, secret sprawl, and rollback semantics now
- it would blur `CP-024` operational runbooks and `CP-026` build automation
- a self-managed two-VM topology is safer with operator-controlled promotion until release automation is stable

### Build desktop installers on every pull request

Rejected because:

- Windows Tauri packaging is slower and more secret-sensitive than normal verification
- signed installer creation should stay tied to release intent
- PRs need fast signal, not installer publication

## Scope

### In Scope

- GitHub Actions workflow for pull-request verification
- GitHub Actions workflow for tag-based release artifacts
- repo-owned release bundle creation for:
  - `services/control-plane-api`
  - `apps/platform-admin`
  - `apps/owner-web`
  - `apps/store-desktop` packaged installers and signatures
- artifact publication to GitHub Actions artifacts and GitHub Releases
- repo-owned npm or script entrypoints so CI commands are not large inline shell fragments
- runbook updates for:
  - how PR verification works
  - how tagged releases produce artifacts
  - how operators download artifacts and continue the manual promotion flow

### Out Of Scope

- automatic upload to your object storage
- automatic SSH deployment to app or DB VMs
- automatic staging or production promotion
- full release-notes generation
- cross-platform desktop installer matrix beyond the current Windows-first contract

## Workflow Topology

### PR Verification Workflow

One GitHub Actions workflow should run on:

- `pull_request`
- optionally `push` to `main` for branch health

Jobs should be split by responsibility:

- `backend`
  - Python setup
  - install backend dependencies
  - run control-plane backend pytest
- `web`
  - Node setup
  - install workspace dependencies
  - run owner-web and platform-admin tests, typecheck, and build
- `desktop`
  - Windows runner
  - Node and Rust setup
  - run store-desktop tests, typecheck, build, native cargo tests, and release-script tests
- `release-automation`
  - validate the repo-owned release-bundle scripts and workflow expectations with lightweight tests

The pull-request workflow must not require signing secrets.

### Release Artifact Workflow

One separate workflow should run on:

- push tags matching release intent
- manual `workflow_dispatch`

It should produce:

- control-plane release bundle archive
- owner-web dist archive
- platform-admin dist archive
- signed Store Desktop NSIS installer and signature

On tag builds:

- attach those artifacts to a GitHub Release

On manual dispatch:

- upload workflow artifacts even if a GitHub Release is not created

## Release Artifact Contract

### Control Plane

The control-plane release artifact should be a `.tar.gz` bundle built from `services/control-plane-api/` with a stable file name:

- `store-control-plane-<version>.tar.gz`

The archive should include:

- application source
- Alembic config and migrations
- operator scripts
- ops examples
- requirements and documentation needed by the app VM

It must exclude:

- virtual environments
- test caches
- local databases
- node modules

### Web Apps

Each web app should build first, then archive its `dist/` output as:

- `platform-admin-<version>.tar.gz`
- `owner-web-<version>.tar.gz`

These artifacts are for reproducible deployment promotion or CDN upload later. They do not replace the existing application runbooks; they give the release process a deterministic payload.

### Store Desktop

The existing Windows-first release script remains the build authority:

- `scripts/build-store-desktop-release.mjs`

CI should stage the release outputs into a predictable artifact folder that contains:

- NSIS installer
- matching `.sig`
- release metadata summary

Static update-manifest generation remains operator-controlled after artifact publication because the final installer URL is not known until the artifact is promoted to the chosen update channel.

## Release Versioning And Tagging

Start with one release tag shape:

- `v<semver>`

Examples:

- `v0.2.0`
- `v1.0.0`

Use the same version string for:

- GitHub release
- control-plane release bundle name
- web dist archive names
- desktop artifact folder naming

The desktop Tauri app version remains controlled by its own package and Tauri metadata. `CP-026` does not try to make Git tags rewrite version files automatically.

## Secrets And Trust Boundary

### PR Workflow

Allowed to run without release secrets.

### Release Workflow

Requires only the secrets needed for signed desktop artifacts:

- `TAURI_SIGNING_PRIVATE_KEY`
- `TAURI_SIGNING_PRIVATE_KEY_PASSWORD`
- optional desktop release override values if used in your packaging contract

The workflow must not receive VM SSH credentials or object-storage write credentials in this first slice.

## Documentation Boundary

`CP-026` should add one dedicated runbook describing:

- PR verification workflow
- tag-based release artifact workflow
- required GitHub secrets
- how operators download artifacts from GitHub
- how operators continue with the manual deployment runbooks from `CP-024` and `CP-022`

Existing runbooks should be updated only where the automation handoff matters:

- control-plane production deployment
- store-desktop packaging and distribution

## Testing Strategy

This task should test repo-owned automation logic, not GitHub itself.

Required local regression coverage:

- control-plane release archive script
- web dist archive script
- desktop release artifact staging script
- workflow file smoke assertions for expected triggers, jobs, and commands

Workflow YAML should be validated indirectly by tests that read the workflow files and assert the expected command boundaries and triggers. This keeps the automation contract reviewable inside the repo without introducing a large extra toolchain.

## Exit Criteria

`CP-026` is complete when:

- pull requests have a GitHub verification workflow covering backend, web, desktop, and automation boundaries
- tagged releases produce backend, web, and desktop artifacts in GitHub Actions
- signed desktop installers are built only in the release workflow
- operator docs clearly explain the artifact-to-deployment handoff
- the ledger and worklog capture the new automation boundary
