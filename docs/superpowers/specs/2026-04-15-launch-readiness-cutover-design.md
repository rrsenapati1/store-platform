# Launch Readiness And Cutover Design

Date: 2026-04-15  
Task: `CP-028`  
Status: Approved by direct user instruction, no additional review gate requested

## Goal

Add the final repo-owned launch gate pack for Store so public release is driven by explicit evidence instead of tribal memory.

This task should make four things concrete:

- beta-readiness evidence
- legacy read retirement/acceptance
- release-candidate certification
- go-live sign-off flow

## Important Boundary

The repo can automate and document launch evidence, but it cannot fabricate real-world beta or production sign-off.

So `CP-028` should deliver:

- the launch-readiness framework
- the certification script
- the checklists/templates/registers
- the exact evidence format operators must record

It should not pretend that real beta pilots have already happened if they have not.

## Chosen Approach

Use an evidence-based launch pack with one lightweight certification script plus a dedicated `docs/launch/` documentation set.

That means:

- keep using the existing control-plane verification and deployed-verification scripts
- add one repo-owned release-candidate certification command that evaluates launch gates from deployed evidence
- add launch docs for beta exit, legacy-read acceptance, checklist sign-off, and go-live procedure

This is better than a docs-only checklist because it gives the operator one explicit machine-readable gate for the control-plane release candidate.

## Rejected Alternatives

### Docs-only launch checklist

Rejected because:

- it relies too much on manual interpretation
- it does not actually test the cutover contract
- it weakens the final release decision into “someone said it looked ready”

### Fully automated go-live from CI

Rejected because:

- you are still running a self-managed VM topology
- production promotion remains intentionally operator-controlled
- the release boundary should stay “evidence + manual sign-off” for this first public launch

## Scope

### In Scope

- release-candidate certification script
- launch-readiness docs under `docs/launch/`
- explicit beta pilot exit criteria
- explicit legacy-read acceptance register
- go-live checklist and sign-off template
- go-live runbook linking existing infra/release/security/support docs

### Out Of Scope

- automatic production cutover
- real beta pilot execution
- real production sign-off automation
- retiring the legacy retail API process from infrastructure automatically

## Documentation Set

Create a new `docs/launch/` section with:

- `launch-readiness-checklist.md`
- `beta-pilot-exit-criteria.md`
- `legacy-read-acceptance-register.md`
- `release-candidate-evidence-template.md`
- `go-live-runbook.md`

## Release-Candidate Certification Script

Add a repo-owned script near the control-plane verification tooling:

- `services/control-plane-api/scripts/certify_release_candidate.py`

The script should build on `verify_deployed_control_plane.py` and evaluate the core gates:

- deployed health is `ok`
- expected environment matches
- expected release version matches
- authority boundary reports `legacy_write_mode == cutover`
- authority boundary reports an empty legacy-only domain list

The script should emit a structured JSON summary with:

- environment
- release version
- legacy write mode
- legacy remaining domains
- per-gate pass/fail results
- overall certification status

Suggested overall states:

- `approved`
- `blocked`

## Launch Gates

### Gate 1: Verification

- full control-plane verification stack passes
- deployed verification passes for the target environment

### Gate 2: Authority/Cutover

- migrated legacy writes are in `cutover`
- legacy-only domain list is empty, or explicitly accepted in the launch register

### Gate 3: Beta Readiness

- beta-pilot exit criteria doc is completed by operators
- known blockers are either resolved or explicitly accepted

### Gate 4: Operational Sign-Off

- launch checklist is completed
- owners for backend/runtime/infra/support sign off explicitly

## Legacy Read Acceptance

The launch pack must make one thing explicit:

- either there are no remaining accepted legacy reads
- or any accepted residual legacy reads are listed intentionally with owner, rationale, and removal plan

For the current repo state, the expected starting register is:

- no accepted legacy reads

## Testing Strategy

Add backend tests for the certification script:

- healthy deployed result with `cutover` and empty legacy domains => `approved`
- `shadow` mode => `blocked`
- non-empty legacy remaining domains => `blocked`

Docs verification should ensure:

- all new launch docs exist
- the docs index references the launch section

## Exit Criteria

Repo-side `CP-028` implementation is complete when:

- the launch docs exist under `docs/launch/`
- the certification script exists and is tested
- launch-readiness, beta exit, legacy-read acceptance, and sign-off templates are documented
- the docs index links to the launch section

Real-world public-release sign-off remains an operator action after those artifacts exist.
