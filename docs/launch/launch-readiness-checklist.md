# Launch Readiness Checklist

Updated: 2026-04-15

Use this checklist before declaring a release candidate operationally ready for public launch.

## Release Candidate Metadata

- Release version:
- Target environment:
- Candidate owner:
- Review date:

## Verification Gates

- [ ] Local control-plane verification passes
  - evidence:
    - `python services/control-plane-api/scripts/verify_control_plane.py`
- [ ] Deployed environment verification passes
  - evidence:
    - `python services/control-plane-api/scripts/verify_deployed_control_plane.py --base-url ... --expected-environment ... --expected-release-version ...`
- [ ] Release-candidate certification reports `approved`
  - evidence:
    - `python services/control-plane-api/scripts/certify_release_candidate.py --base-url ... --expected-environment ... --expected-release-version ...`

## Authority / Cutover Gates

- [ ] authority boundary reports `legacy_write_mode = cutover`
- [ ] authority boundary reports an empty `legacy_remaining_domains` list, or accepted exceptions are documented in `legacy-read-acceptance-register.md`
- [ ] legacy retail API write blocking was spot-checked during cutover validation

## Security / Operations Gates

- [ ] security/observability posture is healthy
  - secure headers
  - rate limiting
  - Sentry/project wiring
  - platform observability summary
- [ ] backup freshness is acceptable
- [ ] release artifacts exist and match the target version

## Product / Runtime Gates

- [ ] owner-web works on the target environment
- [ ] platform-admin works on the target environment
- [ ] packaged Store Desktop install/activation works on the target environment
- [ ] runtime print/scanner critical path was validated on a real packaged runtime
- [ ] offline continuity/replay posture was reviewed for the target branch-hub runtime

## Beta Exit Gates

- [ ] beta pilot exit criteria are satisfied
- [ ] no unresolved severity-1 launch blockers remain
- [ ] accepted severity-2/severity-3 issues are documented with owner and follow-up release target

## Documentation / Support Gates

- [ ] public docs pack is current
- [ ] support/admin playbooks are current
- [ ] known issues list is current
- [ ] support escalation ownership is confirmed

## Final Sign-Off

- [ ] backend owner
- [ ] desktop/runtime owner
- [ ] infra/operator owner
- [ ] support owner
- [ ] release owner

## Outcome

- Final decision:
  - `go`
  - `hold`
- Notes:
