# V2-009 Performance And Load Validation Foundation Design

## Goal

Start `V2-009` with a real performance-validation lane that measures the broadened V2 control-plane hot paths, evaluates explicit launch budgets, and feeds machine-readable results into release-candidate evidence and certification.

This slice is not a full infra-scale benchmark farm. It is the first authoritative harness that turns performance posture into repeatable release evidence instead of ad-hoc “the tests felt fast enough” judgment.

## Why This Is The Right First V2-009 Slice

The repo already has:

- local control-plane verification
- deployed environment verification
- backup and restore scripts
- release-candidate evidence generation
- release-candidate certification

What it does not have is any explicit latency, throughput, or error-budget signal for the much larger V2 suite. That makes the current release evidence operationally incomplete for launch.

Before deeper security, recovery, or cutover hardening, the platform needs one bounded answer to:

- which hot paths matter most right now
- what budget each path is expected to meet
- where those results are recorded for release decisions

## Recommended Approach

Add one reusable performance-validation seam rather than scattering timing checks across unrelated scripts.

The slice should include:

- a reusable scenario and budget engine
- one script that runs the launch-foundation scenario set and writes JSON evidence
- a bounded in-process workload runner for today’s highest-risk V2 paths
- release evidence integration
- release certification integration

This keeps the first implementation honest and small:

- no external load-testing cluster
- no synthetic dashboard separate from release evidence
- no second verification framework

## Scope

Included:

- launch-foundation performance scenario model
- scenario budgets for the current V2 hot paths
- in-process performance runner for local/release evidence generation
- machine-readable JSON performance report
- release-candidate evidence markdown including performance posture
- release-candidate certification gate for performance budgets when the result is available
- runbook updates

Not included:

- internet-scale external traffic generation
- production traffic replay
- per-tenant statistical baselining
- autoscaling decisions
- distributed tracing-based latency attribution
- continuous scheduled performance automation

## Architecture

### 1. Performance Budget Engine

Add a focused backend module that owns:

- scenario definitions
- budget thresholds
- percentile and throughput calculations
- pass/fail evaluation

Each scenario result should include:

- `scenario_name`
- `iterations`
- `success_count`
- `failure_count`
- `error_rate`
- `throughput_ops_per_sec`
- `p50_latency_ms`
- `p95_latency_ms`
- `status`
- `failure_reasons`

The overall report should include:

- `status`
  - `passed`
  - `failed`
- `scenario_set`
- `generated_at`
- aggregate counts
- failing scenario names
- per-scenario records

### 2. Launch-Foundation Scenario Set

The first scenario set should cover the highest-value V2 hot paths already present in the repo:

- `checkout_price_preview`
- `direct_sale_creation`
- `checkout_payment_session_creation`
- `offline_sale_replay`
- `reviewed_receiving_creation`
- `restock_task_lifecycle`
- `reviewed_stock_count_lifecycle`
- `branch_reporting_dashboard_read`

Those scenarios match the current product risk:

- pricing and checkout are customer-facing latency-sensitive paths
- offline replay is a continuity-risk path
- receiving/restock/count are serious daily-operations flows
- reporting/dashboard reads matter for manager posture and decision support

### 3. Scenario Runner Boundary

The first runner should be in-process and deterministic:

- bootstrap a temporary control-plane app with stub identity
- seed the required tenant/branch/catalog/supplier/runtime context once
- run each scenario for a bounded iteration count
- measure elapsed time with a monotonic clock
- record success/failure and timing

This avoids external network and deployment variability in the first slice while still producing real route-level performance evidence against the actual code paths.

The runner boundary should stay reusable so a later slice can add external HTTP or staged-environment execution without rewriting the budget logic.

### 4. Release Evidence Integration

Extend `generate_release_candidate_evidence.py` so it can:

- run the new performance-validation script alongside local verification
- include the performance summary in the markdown evidence
- pass the resulting performance posture into release certification

Extend `certify_release_candidate.py` so it can:

- gate on performance results when provided
- expose a new certification gate:
  - `performance_budgets_passed`

The certification flow must remain backward-compatible for callers that do not yet provide performance data, but `V2-010` should use the performance-aware path.

## Initial Budgets

The first budgets should be explicit but conservative enough for stable local verification:

- `checkout_price_preview`
  - `p95_latency_ms <= 250`
  - `error_rate <= 0.0`
  - `throughput_ops_per_sec >= 4.0`
- `direct_sale_creation`
  - `p95_latency_ms <= 300`
  - `error_rate <= 0.0`
  - `throughput_ops_per_sec >= 3.0`
- `checkout_payment_session_creation`
  - `p95_latency_ms <= 350`
  - `error_rate <= 0.0`
  - `throughput_ops_per_sec >= 2.0`
- `offline_sale_replay`
  - `p95_latency_ms <= 400`
  - `error_rate <= 0.0`
  - `throughput_ops_per_sec >= 2.0`
- `reviewed_receiving_creation`
  - `p95_latency_ms <= 350`
  - `error_rate <= 0.0`
  - `throughput_ops_per_sec >= 2.0`
- `restock_task_lifecycle`
  - `p95_latency_ms <= 300`
  - `error_rate <= 0.0`
  - `throughput_ops_per_sec >= 2.0`
- `reviewed_stock_count_lifecycle`
  - `p95_latency_ms <= 325`
  - `error_rate <= 0.0`
  - `throughput_ops_per_sec >= 2.0`
- `branch_reporting_dashboard_read`
  - `p95_latency_ms <= 250`
  - `error_rate <= 0.0`
  - `throughput_ops_per_sec >= 4.0`

These are launch-foundation budgets, not final production SLOs.

## Error Handling

The harness must fail loudly and structurally.

If a scenario fails:

- record the failure in the scenario result
- include the failure reason
- continue evaluating the rest of the scenario set
- mark the overall report `failed`

If the harness itself cannot bootstrap:

- exit non-zero
- return a report with `status = failed`
- include a top-level error summary

Release evidence should never hide a failed performance lane behind “not run” wording unless the operator explicitly skipped it.

## Testing

Backend tests should cover:

- percentile, throughput, and error-rate evaluation
- overall pass/fail aggregation
- JSON report writing
- release evidence markdown integration
- release certification gate behavior when performance passes or fails

The first implementation does not need frontend changes. This is a control-plane and release-ops slice.

## Success Criteria

This slice is complete when:

- the repo has a reusable performance-validation engine
- the launch-foundation scenario set produces machine-readable results
- release evidence includes performance posture
- release certification can consume performance posture
- docs explain how to run the new lane
- verification passes on the merged implementation
