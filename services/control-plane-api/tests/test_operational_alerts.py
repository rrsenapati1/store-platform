from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_module():
    module_path = Path(__file__).resolve().parents[1] / "store_control_plane" / "operational_alerts.py"
    spec = importlib.util.spec_from_file_location("store_control_plane.operational_alerts", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_build_operational_alert_report_fails_on_dead_letter_jobs() -> None:
    module = _load_module()

    report = module.build_operational_alert_report(
        generated_at="2026-04-18T18:30:00Z",
        environment="prod",
        release_version="2026.04.18-rc3",
        observability_summary={
            "operations": {"dead_letter_count": 1, "retryable_count": 0},
            "runtime": {"degraded_branch_count": 0},
            "backup": {"status": "ok", "age_hours": 1.0},
        },
        security_result={"status": "passed"},
    )

    assert report["status"] == "failed"
    assert report["failing_checks"] == ["operations_dead_letter_clear"]


def test_build_operational_alert_report_fails_on_backup_age_breach() -> None:
    module = _load_module()

    report = module.build_operational_alert_report(
        generated_at="2026-04-18T18:30:00Z",
        environment="prod",
        release_version="2026.04.18-rc3",
        observability_summary={
            "operations": {"dead_letter_count": 0, "retryable_count": 0},
            "runtime": {"degraded_branch_count": 0},
            "backup": {"status": "ok", "age_hours": 30.0},
        },
        security_result={"status": "passed"},
    )

    assert report["status"] == "failed"
    assert "backup_freshness_within_limit" in report["failing_checks"]


def test_build_operational_alert_report_passes_when_all_thresholds_hold() -> None:
    module = _load_module()

    report = module.build_operational_alert_report(
        generated_at="2026-04-18T18:30:00Z",
        environment="prod",
        release_version="2026.04.18-rc3",
        observability_summary={
            "operations": {"dead_letter_count": 0, "retryable_count": 1},
            "runtime": {"degraded_branch_count": 0},
            "backup": {"status": "ok", "age_hours": 2.0},
        },
        security_result={"status": "passed"},
        thresholds={
            "max_retryable_count": 2,
            "max_degraded_branch_count": 0,
            "max_backup_age_hours": 26,
        },
    )

    assert report["status"] == "passed"
    assert report["failing_checks"] == []
