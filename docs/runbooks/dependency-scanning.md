# Dependency And Image Scanning

Updated: 2026-04-18

## Purpose

`CP-025` established the baseline scan posture. `V2-009` turns that posture into a repo-owned execution path that writes normalized JSON evidence and can now block release certification when scan evidence is missing or failed.

`V2-009` also adds first-class license-compliance evaluation on top of the generated SBOM bundle so release readiness covers not just known vulnerabilities but also policy-blocking runtime licenses.

## SBOM Bundle Runner

`V2-009` also adds first-class SBOM generation for the same release surfaces.

From repo root, run:

```powershell
python services/control-plane-api/scripts/generate_sbom_bundle.py `
  --output-path docs/launch/evidence/staging-sbom-report.json `
  --raw-output-dir docs/launch/evidence/staging-sbom-artifacts `
  --image-ref store-control-plane-api:staging `
  --image-ref postgres:16
```

This runner writes:

- one normalized JSON report
- one raw CycloneDX JSON artifact per surface under the raw-output directory

## SBOM Coverage

The runner currently covers:

- `services/control-plane-api`
- `apps/platform-admin`
- `apps/owner-web`
- `apps/store-desktop`
- `apps/store-mobile`
- `apps/store-desktop/src-tauri`
- explicitly provided container image references

## SBOM Tooling

The first foundation uses `syft` as the primary generator and expects CycloneDX JSON output.

If `syft` is unavailable, the runner still writes a normalized report, but affected surfaces are marked `tool-unavailable` and release certification should block when that report is supplied or required.

## License Compliance Runner

From repo root, run:

```powershell
python services/control-plane-api/scripts/run_license_compliance.py `
  --sbom-report docs/launch/evidence/staging-sbom-report.json `
  --output-path docs/launch/evidence/staging-license-compliance-report.json `
  --policy-path docs/launch/security/license-policy.json `
  --exceptions-path docs/launch/security/license-exceptions.json
```

This runner reuses the SBOM artifact paths from the normalized SBOM report and writes one normalized JSON report with:

- `status`
- `policy`
- `surfaces`
- `failing_surfaces`
- `summary`

Each surface records:

- `component_count`
- `license_summary`
- `findings`
- `artifact_path`
- `failure_reason`

## License Policy

The repo-owned default policy lives in:

- `docs/launch/security/license-policy.json`

The first foundation treats:

- permissive licenses such as `MIT`, `Apache-2.0`, and `BSD-*` as allowed
- reciprocal or ambiguous commercial-risk licenses such as `LGPL-*`, `EPL-*`, and `CDDL-*` as review-required
- strong copyleft or source-available-only licenses such as `GPL-*`, `AGPL-*`, `SSPL-1.0`, `BUSL-1.1`, and `Commons-Clause` as denied

Unknown licenses are blocking by default.

## License Exceptions

Approved temporary exceptions live in:

- `docs/launch/security/license-exceptions.json`

Each entry must include:

- `surface`
- `package_or_identifier`
- `license`
- `expires_on`
- `reason`
- `mitigation`
- `approved_by`

Expired exceptions fail the runner.

## Primary Runner

From repo root, run:

```powershell
python services/control-plane-api/scripts/run_vulnerability_scans.py `
  --output-path docs/launch/evidence/staging-vulnerability-report.json `
  --exceptions-path docs/launch/security/vulnerability-exceptions.json `
  --image-ref store-control-plane-api:staging `
  --image-ref postgres:16
```

This runner executes the Python, Node, Rust, and image scan set and writes one normalized JSON report.

Use `--raw-output-dir <path>` when you also want the underlying scanner JSON payloads preserved for operator review.

## Release-Blocker Policy

Treat these as release blockers until explicitly triaged:

- known critical vulnerabilities in runtime dependencies
- known high-severity vulnerabilities on public-facing backend or auth-adjacent packages
- critical vulnerabilities in packaged desktop native dependencies
- container base-image vulnerabilities that affect the deployed app or Postgres images and already have a supported patched version

Document accepted exceptions in the release notes or deployment change log. Do not rely on memory.

## What The Runner Covers

The runner currently scans:

- Python runtime dependencies for `services/control-plane-api`
- Node runtime dependencies for:
  - `@store/platform-admin`
  - `@store/owner-web`
  - `@store/store-desktop`
  - `@store/store-mobile`
- Rust native dependencies for `apps/store-desktop/src-tauri`
- explicitly provided container image references

## Underlying Commands

The runner is the preferred path, but the underlying commands remain useful for debugging.

### Python Backend

From repo root:

```powershell
python -m pip install pip-audit
python -m pip_audit -r services/control-plane-api/requirements.txt
```

Use this before backend release preparation and after bumping backend dependencies.

### Node Workspaces

From repo root:

```powershell
npm audit --workspaces --omit=dev
npm audit --workspace @store/platform-admin --omit=dev
npm audit --workspace @store/owner-web --omit=dev
npm audit --workspace @store/store-desktop --omit=dev
```

If you need to inspect dev-dependency exposure during toolchain upgrades, run the same commands without `--omit=dev`.

### Rust Or Tauri Native Dependencies

Install `cargo-audit` once:

```powershell
cargo install cargo-audit
```

Then scan the packaged runtime:

```powershell
cargo audit --manifest-path apps/store-desktop/src-tauri/Cargo.toml
```

### Container Images

For self-managed VM releases, scan both the app image and any helper image you publish.

Example with Trivy:

```powershell
trivy image store-control-plane-api:staging
trivy image postgres:16
```

If your deployment stays process-based instead of container-based, still scan any base images used in CI packaging or release generation.

## Exceptions File

Approved temporary exceptions live in:

- `docs/launch/security/vulnerability-exceptions.json`

Each entry must include:

- `surface`
- `tool`
- `package_or_identifier`
- `advisory_id`
- `expires_on`
- `reason`
- `mitigation`
- `approved_by`

Expired exceptions fail the runner. Do not carry release-risk exceptions indefinitely.

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

Keep the latest runner report for the release candidate, for example:

```powershell
python services/control-plane-api/scripts/run_vulnerability_scans.py `
  --output-path docs/launch/evidence/prod-vulnerability-report.json `
  --exceptions-path docs/launch/security/vulnerability-exceptions.json `
  --image-ref store-control-plane-api:prod `
  --image-ref postgres:16
```

Then feed that report into release evidence or certification:

```powershell
python services/control-plane-api/scripts/generate_release_candidate_evidence.py `
  --base-url https://control.store.korsenex.com `
  --expected-environment prod `
  --expected-release-version 2026.04.18 `
  --vulnerability-scan-report docs/launch/evidence/prod-vulnerability-report.json

python services/control-plane-api/scripts/certify_release_candidate.py `
  --base-url https://control.store.korsenex.com `
  --expected-environment prod `
  --expected-release-version 2026.04.18 `
  --vulnerability-scan-report docs/launch/evidence/prod-vulnerability-report.json
```

Release certification should now block if the vulnerability report is missing or failed.

## Minimum SBOM Evidence For A Release

Keep the latest SBOM bundle report for the release candidate, for example:

```powershell
python services/control-plane-api/scripts/generate_sbom_bundle.py `
  --output-path docs/launch/evidence/prod-sbom-report.json `
  --raw-output-dir docs/launch/evidence/prod-sbom-artifacts `
  --image-ref store-control-plane-api:prod `
  --image-ref postgres:16
```

Then feed that report into release evidence or certification:

```powershell
python services/control-plane-api/scripts/generate_release_candidate_evidence.py `
  --base-url https://control.store.korsenex.com `
  --expected-environment prod `
  --expected-release-version 2026.04.18 `
  --sbom-report docs/launch/evidence/prod-sbom-report.json

python services/control-plane-api/scripts/certify_release_candidate.py `
  --base-url https://control.store.korsenex.com `
  --expected-environment prod `
  --expected-release-version 2026.04.18 `
  --sbom-report docs/launch/evidence/prod-sbom-report.json
```

Release certification should now block if the SBOM report is missing or failed.

## Minimum License Evidence For A Release

Keep the latest license-compliance report for the release candidate, for example:

```powershell
python services/control-plane-api/scripts/run_license_compliance.py `
  --sbom-report docs/launch/evidence/prod-sbom-report.json `
  --output-path docs/launch/evidence/prod-license-compliance-report.json `
  --policy-path docs/launch/security/license-policy.json `
  --exceptions-path docs/launch/security/license-exceptions.json
```

Then feed that report into release evidence or certification:

```powershell
python services/control-plane-api/scripts/generate_release_candidate_evidence.py `
  --base-url https://control.store.korsenex.com `
  --expected-environment prod `
  --expected-release-version 2026.04.18 `
  --license-compliance-report docs/launch/evidence/prod-license-compliance-report.json

python services/control-plane-api/scripts/certify_release_candidate.py `
  --base-url https://control.store.korsenex.com `
  --expected-environment prod `
  --expected-release-version 2026.04.18 `
  --license-compliance-report docs/launch/evidence/prod-license-compliance-report.json
```

Release certification should now block if the license-compliance report is missing or failed.
