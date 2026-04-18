from __future__ import annotations

import json
from pathlib import Path


DEFAULT_ALERT_THRESHOLDS: dict[str, float | int] = {
    "max_retryable_count": 0,
    "max_degraded_branch_count": 0,
    "max_backup_age_hours": 26,
}


def build_alert_check(
    *,
    name: str,
    status: str,
    observed_value: object,
    threshold: object,
    reason: str,
) -> dict[str, object]:
    return {
        "name": name,
        "status": status,
        "observed_value": observed_value,
        "threshold": threshold,
        "reason": reason,
    }


def evaluate_operational_alerts(
    *,
    observability_summary: dict[str, object],
    security_result: dict[str, object],
    thresholds: dict[str, float | int] | None = None,
) -> list[dict[str, object]]:
    effective_thresholds = dict(DEFAULT_ALERT_THRESHOLDS)
    if thresholds:
        effective_thresholds.update(thresholds)

    operations = dict(observability_summary.get("operations") or {})
    runtime = dict(observability_summary.get("runtime") or {})
    backup = dict(observability_summary.get("backup") or {})

    dead_letter_count = int(operations.get("dead_letter_count") or 0)
    retryable_count = int(operations.get("retryable_count") or 0)
    degraded_branch_count = int(runtime.get("degraded_branch_count") or 0)
    backup_status = str(backup.get("status") or "unknown")
    backup_age_hours = backup.get("age_hours")
    security_status = str(security_result.get("status") or "failed")

    checks = [
        build_alert_check(
            name="operations_dead_letter_clear",
            status="passed" if dead_letter_count == 0 else "failed",
            observed_value=dead_letter_count,
            threshold=0,
            reason="dead-letter queue clear" if dead_letter_count == 0 else "dead-letter jobs present",
        ),
        build_alert_check(
            name="operations_retryable_within_limit",
            status="passed" if retryable_count <= int(effective_thresholds["max_retryable_count"]) else "failed",
            observed_value=retryable_count,
            threshold=int(effective_thresholds["max_retryable_count"]),
            reason="retryable jobs within threshold"
            if retryable_count <= int(effective_thresholds["max_retryable_count"])
            else "retryable job count exceeds threshold",
        ),
        build_alert_check(
            name="runtime_degradation_within_limit",
            status="passed"
            if degraded_branch_count <= int(effective_thresholds["max_degraded_branch_count"])
            else "failed",
            observed_value=degraded_branch_count,
            threshold=int(effective_thresholds["max_degraded_branch_count"]),
            reason="runtime degradation within threshold"
            if degraded_branch_count <= int(effective_thresholds["max_degraded_branch_count"])
            else "degraded branch count exceeds threshold",
        ),
        build_alert_check(
            name="backup_freshness_within_limit",
            status="passed"
            if backup_status == "ok"
            and backup_age_hours is not None
            and float(backup_age_hours) <= float(effective_thresholds["max_backup_age_hours"])
            else "failed",
            observed_value={"status": backup_status, "age_hours": backup_age_hours},
            threshold={"status": "ok", "max_backup_age_hours": float(effective_thresholds["max_backup_age_hours"])},
            reason="backup freshness within threshold"
            if backup_status == "ok"
            and backup_age_hours is not None
            and float(backup_age_hours) <= float(effective_thresholds["max_backup_age_hours"])
            else "backup freshness threshold breached",
        ),
        build_alert_check(
            name="security_verification_passed",
            status="passed" if security_status == "passed" else "failed",
            observed_value=security_status,
            threshold="passed",
            reason="security verification passed" if security_status == "passed" else "security verification failed",
        ),
    ]

    return checks


def build_operational_alert_report(
    *,
    generated_at: str,
    environment: str,
    release_version: str,
    observability_summary: dict[str, object],
    security_result: dict[str, object],
    thresholds: dict[str, float | int] | None = None,
) -> dict[str, object]:
    checks = evaluate_operational_alerts(
        observability_summary=observability_summary,
        security_result=security_result,
        thresholds=thresholds,
    )
    failing_checks = [str(check["name"]) for check in checks if check["status"] != "passed"]
    summary = (
        f"{len(checks)} alert checks passed"
        if not failing_checks
        else f"{len(failing_checks)} alert checks failed: {', '.join(failing_checks)}"
    )
    return {
        "status": "passed" if not failing_checks else "failed",
        "environment": environment,
        "release_version": release_version,
        "generated_at": generated_at,
        "alert_checks": checks,
        "failing_checks": failing_checks,
        "summary": summary,
    }


def write_operational_alert_report(report: dict[str, object], *, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
