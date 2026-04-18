# Launch Readiness Checklist

Updated: 2026-04-19

Use this checklist before declaring a release candidate operationally ready for public launch.

## Release Candidate Metadata

- Release version:
- Target environment:
- Candidate owner:
- Review date:

## Verification Gates

- [ ] One-shot `V2` launch gate reports `ready`
  - evidence:
    - `python services/control-plane-api/scripts/run_v2_launch_gate.py --base-url ... --expected-environment ... --expected-release-version ... --launch-manifest ...`
- [ ] Launch-readiness report is published with the final launch evidence pack
  - evidence:
    - `published/<environment>-<version>.publication.json`

## Authority / Cutover Gates

- [ ] authority boundary reports `legacy_write_mode = cutover`
- [ ] authority boundary reports an empty `legacy_remaining_domains` list, or accepted exceptions are documented in `legacy-read-acceptance-register.md`
- [ ] legacy retail API write blocking was spot-checked during cutover validation

## Security / Operations Gates

- [ ] strict technical gate inside the V2 launch gate includes healthy security, vulnerability, load, rollback, restore-drill, SBOM, license, TLS, environment-drift, and evidence-retention posture
- [ ] release artifacts exist and match the target version used in the launch-readiness manifest

## Product / Runtime Gates

- [ ] owner-web works on the target environment
- [ ] platform-admin works on the target environment
- [ ] packaged Store Desktop install/activation works on the target environment
- [ ] runtime print/scanner critical path was validated on a real packaged runtime
- [ ] offline continuity/replay posture was reviewed for the target branch-hub runtime

## Beta Exit Gates

- [ ] beta pilot exit criteria are satisfied
- [ ] at least one packaged branch pilot is recorded in the launch-readiness manifest
- [ ] no unresolved severity-1 launch blockers remain
- [ ] accepted severity-2/severity-3 issues are documented with owner and follow-up release target

## Documentation / Support Gates

- [ ] public docs pack is current
- [ ] support/admin playbooks are current
- [ ] known issues list is current
- [ ] support escalation ownership is confirmed

## Final Sign-Off

- [ ] backend owner
- [ ] runtime owner
- [ ] infra/operator owner
- [ ] support owner
- [ ] release owner

## Outcome

- Final decision:
  - `go`
  - `hold`
- Notes:
