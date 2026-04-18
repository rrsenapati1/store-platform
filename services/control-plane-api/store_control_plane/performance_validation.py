from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path


@dataclass(slots=True)
class PerformanceBudget:
    scenario_name: str
    max_p95_latency_ms: float
    max_error_rate: float
    min_throughput_ops_per_sec: float


@dataclass(slots=True)
class PerformanceSample:
    duration_ms: float
    success: bool
    error_message: str | None = None


@dataclass(slots=True)
class PerformanceScenarioResult:
    scenario_name: str
    status: str
    iterations: int
    success_count: int
    failure_count: int
    error_rate: float
    throughput_ops_per_sec: float
    p50_latency_ms: float
    p95_latency_ms: float
    failure_reasons: list[str]
    failures: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class PerformanceValidationReport:
    status: str
    scenario_set: str
    generated_at: str
    scenario_results: list[PerformanceScenarioResult]
    passing_scenarios: list[str]
    failing_scenarios: list[str]
    total_iterations: int
    total_failures: int

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "scenario_set": self.scenario_set,
            "generated_at": self.generated_at,
            "scenario_results": [result.to_dict() for result in self.scenario_results],
            "passing_scenarios": list(self.passing_scenarios),
            "failing_scenarios": list(self.failing_scenarios),
            "total_iterations": self.total_iterations,
            "total_failures": self.total_failures,
        }


def launch_foundation_budgets() -> list[PerformanceBudget]:
    return [
        PerformanceBudget("checkout_price_preview", max_p95_latency_ms=250.0, max_error_rate=0.0, min_throughput_ops_per_sec=4.0),
        PerformanceBudget("direct_sale_creation", max_p95_latency_ms=300.0, max_error_rate=0.0, min_throughput_ops_per_sec=3.0),
        PerformanceBudget("checkout_payment_session_creation", max_p95_latency_ms=350.0, max_error_rate=0.0, min_throughput_ops_per_sec=2.0),
        PerformanceBudget("offline_sale_replay", max_p95_latency_ms=400.0, max_error_rate=0.0, min_throughput_ops_per_sec=2.0),
        PerformanceBudget("reviewed_receiving_creation", max_p95_latency_ms=350.0, max_error_rate=0.0, min_throughput_ops_per_sec=2.0),
        PerformanceBudget("restock_task_lifecycle", max_p95_latency_ms=300.0, max_error_rate=0.0, min_throughput_ops_per_sec=2.0),
        PerformanceBudget("reviewed_stock_count_lifecycle", max_p95_latency_ms=325.0, max_error_rate=0.0, min_throughput_ops_per_sec=2.0),
        PerformanceBudget("branch_reporting_dashboard_read", max_p95_latency_ms=250.0, max_error_rate=0.0, min_throughput_ops_per_sec=4.0),
    ]


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = math.ceil((percentile / 100.0) * len(ordered)) - 1
    rank = max(0, min(rank, len(ordered) - 1))
    return ordered[rank]


def evaluate_scenario_result(
    *,
    budget: PerformanceBudget,
    samples: list[PerformanceSample],
) -> PerformanceScenarioResult:
    if not samples:
        raise ValueError(f"performance scenario {budget.scenario_name} requires at least one sample")

    latencies = [sample.duration_ms for sample in samples]
    failures = [sample.error_message or "scenario_failed" for sample in samples if not sample.success]
    failure_count = len(failures)
    iterations = len(samples)
    success_count = iterations - failure_count
    error_rate = failure_count / iterations
    total_duration_ms = sum(latencies)
    throughput_ops_per_sec = iterations / (total_duration_ms / 1000.0) if total_duration_ms > 0 else float(iterations)
    p50_latency_ms = _percentile(latencies, 50)
    p95_latency_ms = _percentile(latencies, 95)

    failure_reasons: list[str] = []
    if p95_latency_ms > budget.max_p95_latency_ms:
        failure_reasons.append("p95_latency_ms_exceeded")
    if error_rate > budget.max_error_rate:
        failure_reasons.append("error_rate_exceeded")
    if throughput_ops_per_sec < budget.min_throughput_ops_per_sec:
        failure_reasons.append("throughput_below_budget")

    return PerformanceScenarioResult(
        scenario_name=budget.scenario_name,
        status="passed" if not failure_reasons else "failed",
        iterations=iterations,
        success_count=success_count,
        failure_count=failure_count,
        error_rate=error_rate,
        throughput_ops_per_sec=throughput_ops_per_sec,
        p50_latency_ms=p50_latency_ms,
        p95_latency_ms=p95_latency_ms,
        failure_reasons=failure_reasons,
        failures=failures,
    )


def build_performance_report(
    *,
    scenario_set: str,
    budgets: list[PerformanceBudget],
    scenario_samples: dict[str, list[PerformanceSample]],
    generated_at: str,
) -> PerformanceValidationReport:
    results = [
        evaluate_scenario_result(budget=budget, samples=scenario_samples[budget.scenario_name])
        for budget in budgets
    ]
    failing_scenarios = [result.scenario_name for result in results if result.status != "passed"]
    passing_scenarios = [result.scenario_name for result in results if result.status == "passed"]
    return PerformanceValidationReport(
        status="passed" if not failing_scenarios else "failed",
        scenario_set=scenario_set,
        generated_at=generated_at,
        scenario_results=results,
        passing_scenarios=passing_scenarios,
        failing_scenarios=failing_scenarios,
        total_iterations=sum(result.iterations for result in results),
        total_failures=sum(result.failure_count for result in results),
    )


def write_performance_report(report: PerformanceValidationReport, *, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")


def summarize_performance_report(report: PerformanceValidationReport) -> str:
    if report.status == "passed":
        return f"{len(report.passing_scenarios)} scenarios passed"
    failing = ", ".join(report.failing_scenarios) if report.failing_scenarios else "unknown"
    return f"{len(report.failing_scenarios)} scenarios failed: {failing}"
