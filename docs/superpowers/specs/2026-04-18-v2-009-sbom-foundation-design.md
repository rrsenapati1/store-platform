# V2-009 SBOM Foundation Design

## Goal

Add first-class SBOM generation and release-readiness evidence so the expanded V2 suite can produce machine-readable software composition artifacts instead of relying only on vulnerability scans and manual dependency inspection.

## Boundary

This slice covers:

- normalized SBOM report generation for core Store release surfaces
- raw SBOM artifact preservation in a standard format
- release evidence rendering
- release certification gating
- operator runbook updates

This slice does not cover:

- signed attestation or provenance
- external artifact publication
- third-party vulnerability enrichment beyond existing scan lanes

## Recommended Shape

Use one repo-owned runner and one normalized report:

- domain module: `store_control_plane/sbom_generation.py`
- operator CLI: `services/control-plane-api/scripts/generate_sbom_bundle.py`
- raw artifacts: CycloneDX JSON
- normalized report: one JSON summary with surface status, component count, artifact path, and failure posture

## Surfaces

The first bundle should cover:

- `services/control-plane-api`
- `apps/platform-admin`
- `apps/owner-web`
- `apps/store-desktop`
- `apps/store-mobile`
- `apps/store-desktop/src-tauri`
- optional explicit image references passed by operators

## Tooling

Use `syft` as the primary generator and preserve raw CycloneDX JSON artifacts per surface.

If `syft` is unavailable, the surface should be marked `tool-unavailable` in the normalized report and release certification should block when the SBOM report is supplied or required.

## Release Integration

Extend:

- `generate_release_candidate_evidence.py`
- `certify_release_candidate.py`

Add:

- `--sbom-report <path>`

Certification should block by default when the SBOM report is missing or failed, matching the current direction of the other `V2-009` hardening gates.

## Success Criteria

- operators can generate one SBOM bundle report plus raw artifacts
- release evidence renders SBOM posture explicitly
- release certification blocks when SBOM posture is missing or failed
- the slice is machine-readable and composable with later provenance or attestation work
