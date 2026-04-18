from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path


@dataclass(slots=True)
class EnvironmentDriftCheck:
    name: str
    status: str
    observed_value: object
    expected_value: object
    reason: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class EnvironmentDriftReport:
    status: str
    environment: str | None
    release_version: str | None
    generated_at: str
    checks: list[EnvironmentDriftCheck]
    failing_checks: list[str]
    summary: str

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "environment": self.environment,
            "release_version": self.release_version,
            "generated_at": self.generated_at,
            "checks": [check.to_dict() for check in self.checks],
            "failing_checks": list(self.failing_checks),
            "summary": self.summary,
        }


def _build_check(
    *,
    name: str,
    observed_value: object,
    expected_value: object,
    passed: bool,
    reason: str,
) -> EnvironmentDriftCheck:
    return EnvironmentDriftCheck(
        name=name,
        status="passed" if passed else "failed",
        observed_value=observed_value,
        expected_value=expected_value,
        reason=reason,
    )


def _positive_int_check(
    *,
    name: str,
    value: object,
    reason: str,
) -> EnvironmentDriftCheck:
    numeric_value = int(value or 0)
    return _build_check(
        name=name,
        observed_value=numeric_value,
        expected_value="> 0",
        passed=numeric_value > 0,
        reason=reason if numeric_value > 0 else f"{reason} is not configured",
    )


def build_environment_drift_report(
    *,
    expected_environment: str,
    base_url: str,
    release_version: str | None,
    environment_contract: dict[str, object],
    generated_at: str,
) -> EnvironmentDriftReport:
    operations_worker = dict(environment_contract.get("operations_worker") or {})
    security_controls = dict(environment_contract.get("security_controls") or {})
    rate_limits = dict(security_controls.get("rate_limits") or {})

    checks = [
        _build_check(
            name="deployment_environment_match",
            observed_value=environment_contract.get("deployment_environment"),
            expected_value=expected_environment,
            passed=str(environment_contract.get("deployment_environment") or "") == expected_environment,
            reason="deployment environment matches expected target",
        ),
        _build_check(
            name="public_base_url_match",
            observed_value=environment_contract.get("public_base_url"),
            expected_value=base_url,
            passed=str(environment_contract.get("public_base_url") or "") == base_url,
            reason="public base URL matches verifier target",
        ),
        _build_check(
            name="release_version_match",
            observed_value=environment_contract.get("release_version"),
            expected_value=release_version,
            passed=release_version is None
            or str(environment_contract.get("release_version") or "") == release_version,
            reason="release version matches expected target",
        ),
        _build_check(
            name="log_format_json",
            observed_value=environment_contract.get("log_format"),
            expected_value="json",
            passed=str(environment_contract.get("log_format") or "") == "json",
            reason="structured JSON logging enabled",
        ),
        _build_check(
            name="sentry_configured",
            observed_value=bool(environment_contract.get("sentry_configured")),
            expected_value=True,
            passed=bool(environment_contract.get("sentry_configured")),
            reason="Sentry DSN configured",
        ),
        _build_check(
            name="sentry_environment_match",
            observed_value=environment_contract.get("sentry_environment"),
            expected_value=expected_environment,
            passed=str(environment_contract.get("sentry_environment") or "") == expected_environment,
            reason="Sentry environment matches deployment environment",
        ),
        _build_check(
            name="object_storage_configured",
            observed_value=bool(environment_contract.get("object_storage_configured")),
            expected_value=True,
            passed=bool(environment_contract.get("object_storage_configured")),
            reason="object storage configured",
        ),
        _build_check(
            name="object_storage_bucket_present",
            observed_value=environment_contract.get("object_storage_bucket"),
            expected_value="non-empty",
            passed=bool(environment_contract.get("object_storage_bucket")),
            reason="object storage bucket present",
        ),
        _build_check(
            name="object_storage_prefix_environment_segment",
            observed_value=environment_contract.get("object_storage_prefix"),
            expected_value=f"contains {expected_environment}",
            passed=expected_environment in str(environment_contract.get("object_storage_prefix") or ""),
            reason="object storage prefix contains environment segment",
        ),
        _build_check(
            name="operations_worker_configured",
            observed_value=bool(operations_worker.get("configured")),
            expected_value=True,
            passed=bool(operations_worker.get("configured")),
            reason="operations worker configured",
        ),
        _positive_int_check(
            name="operations_worker_batch_size",
            value=operations_worker.get("batch_size"),
            reason="operations worker batch size",
        ),
        _positive_int_check(
            name="operations_worker_lease_seconds",
            value=operations_worker.get("lease_seconds"),
            reason="operations worker lease seconds",
        ),
        _build_check(
            name="secure_headers_enabled",
            observed_value=bool(security_controls.get("secure_headers_enabled")),
            expected_value=True,
            passed=bool(security_controls.get("secure_headers_enabled")),
            reason="secure headers enabled",
        ),
        _build_check(
            name="secure_headers_hsts_enabled",
            observed_value=bool(security_controls.get("secure_headers_hsts_enabled")),
            expected_value=True,
            passed=bool(security_controls.get("secure_headers_hsts_enabled")),
            reason="HSTS enabled",
        ),
        _build_check(
            name="secure_headers_csp_present",
            observed_value=security_controls.get("secure_headers_csp"),
            expected_value="non-empty",
            passed=bool(str(security_controls.get("secure_headers_csp") or "").strip()),
            reason="CSP policy configured",
        ),
        _positive_int_check(
            name="rate_limit_window_seconds",
            value=rate_limits.get("window_seconds"),
            reason="rate limit window",
        ),
        _positive_int_check(
            name="rate_limit_auth_requests",
            value=rate_limits.get("auth_requests"),
            reason="auth rate limit",
        ),
        _positive_int_check(
            name="rate_limit_activation_requests",
            value=rate_limits.get("activation_requests"),
            reason="activation rate limit",
        ),
        _positive_int_check(
            name="rate_limit_webhook_requests",
            value=rate_limits.get("webhook_requests"),
            reason="webhook rate limit",
        ),
    ]

    failing_checks = [check.name for check in checks if check.status != "passed"]
    summary = summarize_environment_drift_checks(failing_checks=failing_checks, total_checks=len(checks))
    return EnvironmentDriftReport(
        status="passed" if not failing_checks else "failed",
        environment=str(environment_contract.get("deployment_environment") or expected_environment),
        release_version=str(environment_contract.get("release_version") or release_version or ""),
        generated_at=generated_at,
        checks=checks,
        failing_checks=failing_checks,
        summary=summary,
    )


def summarize_environment_drift_checks(*, failing_checks: list[str], total_checks: int) -> str:
    if not failing_checks:
        return "environment contract verified"
    return f"{len(failing_checks)} checks failed: {', '.join(failing_checks)}"


def summarize_environment_drift_report(report: EnvironmentDriftReport) -> str:
    return summarize_environment_drift_checks(
        failing_checks=report.failing_checks,
        total_checks=len(report.checks),
    )


def write_environment_drift_report(report: EnvironmentDriftReport, *, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
