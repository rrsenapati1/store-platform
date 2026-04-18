from __future__ import annotations

import json
from pathlib import Path

from store_control_plane.deployed_load_verification import (
    DeployedLoadBudget,
    DeployedLoadSample,
    build_deployed_load_report,
    evaluate_deployed_load_scenario,
    summarize_deployed_load_report,
    write_deployed_load_report,
)


def test_evaluate_deployed_load_scenario_passes_when_budget_holds() -> None:
    budget = DeployedLoadBudget(
        scenario_name="checkout_price_preview_http",
        max_p95_latency_ms=650.0,
        max_error_rate=0.0,
        min_throughput_ops_per_sec=2.0,
    )

    result = evaluate_deployed_load_scenario(
        budget=budget,
        samples=[
            DeployedLoadSample(duration_ms=120.0, success=True),
            DeployedLoadSample(duration_ms=150.0, success=True),
            DeployedLoadSample(duration_ms=180.0, success=True),
        ],
    )

    assert result.status == "passed"
    assert result.failure_count == 0
    assert result.failure_reasons == []


def test_evaluate_deployed_load_scenario_collects_budget_failures() -> None:
    budget = DeployedLoadBudget(
        scenario_name="observability_summary_http",
        max_p95_latency_ms=500.0,
        max_error_rate=0.0,
        min_throughput_ops_per_sec=4.0,
    )

    result = evaluate_deployed_load_scenario(
        budget=budget,
        samples=[
            DeployedLoadSample(duration_ms=900.0, success=True),
            DeployedLoadSample(duration_ms=950.0, success=False, error_message="503 service unavailable"),
        ],
    )

    assert result.status == "failed"
    assert result.failure_count == 1
    assert "p95_latency_ms_exceeded" in result.failure_reasons
    assert "error_rate_exceeded" in result.failure_reasons
    assert "throughput_below_budget" in result.failure_reasons


def test_build_deployed_load_report_tracks_failing_scenarios_and_writes_json(tmp_path: Path) -> None:
    report = build_deployed_load_report(
        scenario_set="deployed-load-foundation",
        generated_at="2026-04-18T12:00:00Z",
        environment="staging",
        release_version="2026.04.18-rc4",
        concurrency=4,
        iterations_per_worker=5,
        budgets=[
            DeployedLoadBudget("system_health_http", 250.0, 0.0, 4.0),
            DeployedLoadBudget("branch_management_dashboard_http", 600.0, 0.0, 2.0),
        ],
        scenario_samples={
            "system_health_http": [
                DeployedLoadSample(duration_ms=50.0, success=True),
                DeployedLoadSample(duration_ms=70.0, success=True),
            ],
            "branch_management_dashboard_http": [
                DeployedLoadSample(duration_ms=900.0, success=False, error_message="timeout"),
            ],
        },
    )

    output_path = tmp_path / "deployed-load.json"
    write_deployed_load_report(report, output_path=output_path)
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert report.status == "failed"
    assert report.failing_scenarios == ["branch_management_dashboard_http"]
    assert payload["concurrency"] == 4
    assert payload["iterations_per_worker"] == 5
    assert summarize_deployed_load_report(report) == "1 scenarios failed: branch_management_dashboard_http"
