from __future__ import annotations

import json
from pathlib import Path

from store_control_plane.performance_validation import (
    PerformanceBudget,
    PerformanceSample,
    build_performance_report,
    evaluate_scenario_result,
    write_performance_report,
)


def test_evaluate_scenario_result_passes_when_all_budgets_are_met() -> None:
    budget = PerformanceBudget(
        scenario_name="checkout_price_preview",
        max_p95_latency_ms=250.0,
        max_error_rate=0.0,
        min_throughput_ops_per_sec=4.0,
    )
    samples = [
        PerformanceSample(duration_ms=100.0, success=True),
        PerformanceSample(duration_ms=120.0, success=True),
        PerformanceSample(duration_ms=140.0, success=True),
        PerformanceSample(duration_ms=160.0, success=True),
    ]

    result = evaluate_scenario_result(budget=budget, samples=samples)

    assert result.status == "passed"
    assert result.error_rate == 0.0
    assert result.failure_count == 0
    assert result.throughput_ops_per_sec >= 4.0
    assert result.p95_latency_ms == 160.0
    assert result.failure_reasons == []


def test_evaluate_scenario_result_fails_when_latency_budget_is_exceeded() -> None:
    budget = PerformanceBudget(
        scenario_name="direct_sale_creation",
        max_p95_latency_ms=300.0,
        max_error_rate=0.0,
        min_throughput_ops_per_sec=2.0,
    )
    samples = [
        PerformanceSample(duration_ms=120.0, success=True),
        PerformanceSample(duration_ms=150.0, success=True),
        PerformanceSample(duration_ms=410.0, success=True),
    ]

    result = evaluate_scenario_result(budget=budget, samples=samples)

    assert result.status == "failed"
    assert "p95_latency_ms_exceeded" in result.failure_reasons


def test_evaluate_scenario_result_fails_when_error_rate_budget_is_exceeded() -> None:
    budget = PerformanceBudget(
        scenario_name="offline_sale_replay",
        max_p95_latency_ms=400.0,
        max_error_rate=0.0,
        min_throughput_ops_per_sec=1.0,
    )
    samples = [
        PerformanceSample(duration_ms=150.0, success=True),
        PerformanceSample(duration_ms=155.0, success=False, error_message="conflict"),
    ]

    result = evaluate_scenario_result(budget=budget, samples=samples)

    assert result.status == "failed"
    assert result.error_rate == 0.5
    assert "error_rate_exceeded" in result.failure_reasons


def test_evaluate_scenario_result_fails_when_throughput_budget_is_missed() -> None:
    budget = PerformanceBudget(
        scenario_name="branch_reporting_dashboard_read",
        max_p95_latency_ms=250.0,
        max_error_rate=0.0,
        min_throughput_ops_per_sec=5.0,
    )
    samples = [
        PerformanceSample(duration_ms=500.0, success=True),
        PerformanceSample(duration_ms=500.0, success=True),
    ]

    result = evaluate_scenario_result(budget=budget, samples=samples)

    assert result.status == "failed"
    assert result.throughput_ops_per_sec == 2.0
    assert "throughput_below_budget" in result.failure_reasons


def test_write_performance_report_persists_machine_readable_json(tmp_path: Path) -> None:
    budgets = [
        PerformanceBudget(
            scenario_name="checkout_price_preview",
            max_p95_latency_ms=250.0,
            max_error_rate=0.0,
            min_throughput_ops_per_sec=4.0,
        )
    ]
    scenario_samples = {
        "checkout_price_preview": [
            PerformanceSample(duration_ms=100.0, success=True),
            PerformanceSample(duration_ms=120.0, success=True),
            PerformanceSample(duration_ms=140.0, success=True),
            PerformanceSample(duration_ms=160.0, success=True),
        ]
    }

    report = build_performance_report(
        scenario_set="launch-foundation",
        budgets=budgets,
        scenario_samples=scenario_samples,
        generated_at="2026-04-18T12:00:00Z",
    )
    output_path = tmp_path / "performance-report.json"

    write_performance_report(report, output_path=output_path)

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["status"] == "passed"
    assert payload["scenario_set"] == "launch-foundation"
    assert payload["scenario_results"][0]["scenario_name"] == "checkout_price_preview"
