# Dependency And Image Scanning

Updated: 2026-04-15

## Purpose

`CP-025` does not add a full CI vulnerability platform. It does establish a repo-owned minimum scanning posture that must run before public release and before high-risk dependency upgrades are shipped.

## Release-Blocker Policy

Treat these as release blockers until explicitly triaged:

- known critical vulnerabilities in runtime dependencies
- known high-severity vulnerabilities on public-facing backend or auth-adjacent packages
- critical vulnerabilities in packaged desktop native dependencies
- container base-image vulnerabilities that affect the deployed app or Postgres images and already have a supported patched version

Document accepted exceptions in the release notes or deployment change log. Do not rely on memory.

## Python Backend

From repo root:

```powershell
python -m pip install pip-audit
python -m pip_audit -r services/control-plane-api/requirements.txt
```

Use this before backend release preparation and after bumping backend dependencies.

## Node Workspaces

From repo root:

```powershell
npm audit --workspaces --omit=dev
npm audit --workspace @store/platform-admin --omit=dev
npm audit --workspace @store/owner-web --omit=dev
npm audit --workspace @store/store-desktop --omit=dev
```

If you need to inspect dev-dependency exposure during toolchain upgrades, run the same commands without `--omit=dev`.

## Rust Or Tauri Native Dependencies

Install `cargo-audit` once:

```powershell
cargo install cargo-audit
```

Then scan the packaged runtime:

```powershell
cargo audit --manifest-path apps/store-desktop/src-tauri/Cargo.toml
```

## Container Images

For self-managed VM releases, scan both the app image and any helper image you publish.

Example with Trivy:

```powershell
trivy image store-control-plane-api:staging
trivy image postgres:16
```

If your deployment stays process-based instead of container-based, still scan any base images used in CI packaging or release generation.

## When To Run

Run the baseline scan set:

- before each staging promotion
- before each prod promotion
- after dependency bumps in backend, web, or desktop native surfaces
- after upgrading nginx, Postgres, or the app VM base image

## Triage Guidance

1. confirm the vulnerable package is actually in the runtime path
2. check whether a patched supported version exists
3. patch first when the upgrade risk is reasonable
4. if not patching immediately, document:
   - package and version
   - affected surface
   - severity
   - rationale
   - mitigation
   - target fix release

## Minimum Evidence For A Release

Keep the latest scan outputs or operator notes for:

- backend Python audit
- Node workspace audit
- desktop native audit
- deployed app or base image scan

This is the minimum posture until CI automation lands under `CP-026`.
