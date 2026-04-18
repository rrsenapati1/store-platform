# V2-009 Deployed Load Verification Foundation Design

Date: 2026-04-18
Task: `V2-009`
Status: Drafted

## Goal

Add the first repo-owned deployed load verification lane so `V2-009` can produce machine-readable scale evidence against a real environment, not only the current in-process local harness.

This slice should verify that a staging-style deployed stack can sustain bounded concurrent traffic across the most important V2 read and checkout-preview paths while staying inside explicit latency and error budgets.

## Why This Is The Right Next Slice

`V2-009` already has:

- in-process performance validation
- restore-drill evidence
- deployed security verification
- vulnerability scan evidence
- operational alert verification

What it still lacks is a release-safe answer to:

- how the real deployed stack behaves through HTTP
- whether nginx, app boot, Postgres, and deployment wiring hold under concurrent request pressure
- where that deployed scale posture is recorded for release decisions

The current local performance harness is useful, but it cannot prove deployed stack behavior because it skips:

- live HTTP transport
- actual deployment configuration
- reverse proxy behavior
- real environment wiring

That gap matters for enterprise launch hardening.

## Chosen Model

The accepted model is:

- one bounded deployed load runner
- one JSON report contract for deployed load posture
- staging-safe scenario execution only
- release-evidence rendering
- release-certification gating when deployed load evidence is provided

This is intentionally narrower than a full load-testing farm.

## Scope

### In Scope

- repo-owned deployed load verification CLI
- bounded concurrent HTTP scenario execution
- machine-readable JSON deployed load report
- release-evidence integration
- release-certification gate integration
- runbook updates for staged load verification

### Out Of Scope

- internet-scale or multi-minute soak testing
- production traffic replay
- auto-scaling decisions
- provider-level payment throughput testing
- destructive sales or inventory mutation against shared production data
- dashboarding outside release evidence

## Environment Boundary

This verifier should target:

- `staging`, or
- a dedicated pre-prod environment, or
- an isolated release-candidate environment

It should not be a default `prod` gate.

Production use should require explicit operator intent later, if ever.

## Scenario Boundary

The first deployed load slice should stay on low-risk and bounded paths:

- `system_health_http`
- `observability_summary_http`
- `checkout_price_preview_http`
- `branch_reporting_dashboard_http`

Optional later expansion can add synthetic write lanes once the repo has a dedicated seeded load tenant and cleanup contract.

## Report Contract

The deployed load verifier should write one JSON report shaped like:

- `status`
  - `passed`
  - `failed`
- `environment`
- `release_version`
- `generated_at`
- `scenario_set`
  - `deployed-load-foundation`
- `concurrency`
- `iterations_per_worker`
- `scenario_results`
- `failing_scenarios`
- `summary`

Each scenario result should include:

- `scenario_name`
- `request_count`
- `success_count`
- `failure_count`
- `error_rate`
- `throughput_ops_per_sec`
- `p50_latency_ms`
- `p95_latency_ms`
- `status`
- `failure_reasons`

## Budget Model

The first deployed budgets should be stricter on correctness than throughput ambition.

Recommended initial defaults:

- `system_health_http`
  - `p95_latency_ms <= 250`
  - `error_rate <= 0.0`
- `observability_summary_http`
  - `p95_latency_ms <= 500`
  - `error_rate <= 0.0`
- `checkout_price_preview_http`
  - `p95_latency_ms <= 650`
  - `error_rate <= 0.0`
- `branch_reporting_dashboard_http`
  - `p95_latency_ms <= 600`
  - `error_rate <= 0.0`

Suggested runner defaults:

- `concurrency = 4`
- `iterations_per_worker = 5`

These are release-foundation budgets, not long-term production SLOs.

## Fixture Model

The deployed verifier should not invent data inline on every request.

Instead it should accept explicit fixture inputs:

- `bearer_token`
- `tenant_id`
- `branch_id`
- `branch_staff_actor`
- `catalog_product_id`

For checkout preview it should use a stable pre-seeded product fixture.

If required fixture inputs are missing, the verifier should fail early with a clear configuration error instead of silently skipping the scenario.

## Release Integration

Extend:

- [generate_release_candidate_evidence.py](/d:/codes/projects/store/services/control-plane-api/scripts/generate_release_candidate_evidence.py)
- [certify_release_candidate.py](/d:/codes/projects/store/services/control-plane-api/scripts/certify_release_candidate.py)

So they can consume:

- an optional deployed load report

Release evidence should render:

- overall deployed load status
- concurrency settings
- scenario outcomes
- failing scenario list

Release certification should expose:

- `deployed_load_verified`

This gate should be optional for compatibility at first, but `V2-010` should use the evidence-aware path.

## Testing

Backend tests should cover:

- deployed load budget evaluation
- report writing
- HTTP scenario aggregation with fake request executors
- release-evidence rendering
- certification gate behavior when deployed load passes or fails

The first slice does not need owner-web or store-desktop changes.

## Success Criteria

This slice is complete when:

- the repo can run bounded HTTP load verification against a deployed environment
- the verifier writes a normalized JSON report
- release evidence can render deployed load posture
- release certification can gate on deployed load posture when supplied
- docs explain when and where operators should run the new verifier
