from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path


@dataclass(slots=True)
class DeployedLoadBudget:
    scenario_name: str
    max_p95_latency_ms: float
    max_error_rate: float
    min_throughput_ops_per_sec: float


@dataclass(slots=True)
class DeployedLoadSample:
    duration_ms: float
    success: bool
    error_message: str | None = None


@dataclass(slots=True)
class DeployedLoadScenarioResult:
    scenario_name: str
    status: str
    request_count: int
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
class DeployedLoadReport:
    status: str
    scenario_set: str
    environment: str | None
    release_version: str | None
    generated_at: str
    concurrency: int
    iterations_per_worker: int
    scenario_results: list[DeployedLoadScenarioResult]
    failing_scenarios: list[str]
    total_requests: int
    total_failures: int

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "scenario_set": self.scenario_set,
            "environment": self.environment,
            "release_version": self.release_version,
            "generated_at": self.generated_at,
            "concurrency": self.concurrency,
            "iterations_per_worker": self.iterations_per_worker,
            "scenario_results": [result.to_dict() for result in self.scenario_results],
            "failing_scenarios": list(self.failing_scenarios),
            "total_requests": self.total_requests,
            "total_failures": self.total_failures,
        }


def deployed_load_foundation_budgets() -> list[DeployedLoadBudget]:
    return [
        DeployedLoadBudget("system_health_http", max_p95_latency_ms=250.0, max_error_rate=0.0, min_throughput_ops_per_sec=4.0),
        DeployedLoadBudget("observability_summary_http", max_p95_latency_ms=500.0, max_error_rate=0.0, min_throughput_ops_per_sec=2.0),
        DeployedLoadBudget("checkout_price_preview_http", max_p95_latency_ms=650.0, max_error_rate=0.0, min_throughput_ops_per_sec=2.0),
        DeployedLoadBudget("branch_management_dashboard_http", max_p95_latency_ms=600.0, max_error_rate=0.0, min_throughput_ops_per_sec=2.0),
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


def evaluate_deployed_load_scenario(
    *,
    budget: DeployedLoadBudget,
    samples: list[DeployedLoadSample],
) -> DeployedLoadScenarioResult:
    if not samples:
        raise ValueError(f"deployed load scenario {budget.scenario_name} requires at least one sample")

    latencies = [sample.duration_ms for sample in samples]
    failures = [sample.error_message or "request_failed" for sample in samples if not sample.success]
    request_count = len(samples)
    failure_count = len(failures)
    success_count = request_count - failure_count
    error_rate = failure_count / request_count
    total_duration_ms = sum(latencies)
    throughput_ops_per_sec = request_count / (total_duration_ms / 1000.0) if total_duration_ms > 0 else float(request_count)
    p50_latency_ms = _percentile(latencies, 50)
    p95_latency_ms = _percentile(latencies, 95)

    failure_reasons: list[str] = []
    if p95_latency_ms > budget.max_p95_latency_ms:
        failure_reasons.append("p95_latency_ms_exceeded")
    if error_rate > budget.max_error_rate:
        failure_reasons.append("error_rate_exceeded")
    if throughput_ops_per_sec < budget.min_throughput_ops_per_sec:
        failure_reasons.append("throughput_below_budget")

    return DeployedLoadScenarioResult(
        scenario_name=budget.scenario_name,
        status="passed" if not failure_reasons else "failed",
        request_count=request_count,
        success_count=success_count,
        failure_count=failure_count,
        error_rate=error_rate,
        throughput_ops_per_sec=throughput_ops_per_sec,
        p50_latency_ms=p50_latency_ms,
        p95_latency_ms=p95_latency_ms,
        failure_reasons=failure_reasons,
        failures=failures,
    )


def build_deployed_load_report(
    *,
    scenario_set: str,
    generated_at: str,
    environment: str | None,
    release_version: str | None,
    concurrency: int,
    iterations_per_worker: int,
    budgets: list[DeployedLoadBudget],
    scenario_samples: dict[str, list[DeployedLoadSample]],
) -> DeployedLoadReport:
    results = [
        evaluate_deployed_load_scenario(budget=budget, samples=scenario_samples[budget.scenario_name])
        for budget in budgets
    ]
    failing_scenarios = [result.scenario_name for result in results if result.status != "passed"]
    return DeployedLoadReport(
        status="passed" if not failing_scenarios else "failed",
        scenario_set=scenario_set,
        environment=environment,
        release_version=release_version,
        generated_at=generated_at,
        concurrency=concurrency,
        iterations_per_worker=iterations_per_worker,
        scenario_results=results,
        failing_scenarios=failing_scenarios,
        total_requests=sum(result.request_count for result in results),
        total_failures=sum(result.failure_count for result in results),
    )


def write_deployed_load_report(report: DeployedLoadReport, *, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")


def summarize_deployed_load_report(report: DeployedLoadReport) -> str:
    if report.status == "passed":
        return f"{len(report.scenario_results)} scenarios passed"
    failing = ", ".join(report.failing_scenarios) if report.failing_scenarios else "unknown"
    return f"{len(report.failing_scenarios)} scenarios failed: {failing}"
