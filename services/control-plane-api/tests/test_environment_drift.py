from __future__ import annotations

import json
from pathlib import Path

from store_control_plane.environment_drift import (
    build_environment_drift_report,
    summarize_environment_drift_report,
    write_environment_drift_report,
)


def _shared_contract(**overrides: object) -> dict[str, object]:
    contract: dict[str, object] = {
        "deployment_environment": "staging",
        "public_base_url": "https://control.staging.store.korsenex.com",
        "release_version": "2026.04.18",
        "log_format": "json",
        "sentry_configured": True,
        "sentry_environment": "staging",
        "object_storage_configured": True,
        "object_storage_bucket": "store-platform-staging",
        "object_storage_prefix": "control-plane/staging",
        "operations_worker": {
            "configured": True,
            "poll_seconds": 5,
            "batch_size": 25,
            "lease_seconds": 60,
        },
        "security_controls": {
            "secure_headers_enabled": True,
            "secure_headers_hsts_enabled": True,
            "secure_headers_csp": "default-src 'self'; frame-ancestors 'none'",
            "rate_limits": {
                "window_seconds": 60,
                "auth_requests": 10,
                "activation_requests": 10,
                "webhook_requests": 30,
            },
        },
    }
    contract.update(overrides)
    return contract


def test_build_environment_drift_report_passes_for_expected_shared_posture() -> None:
    report = build_environment_drift_report(
        expected_environment="staging",
        base_url="https://control.staging.store.korsenex.com",
        release_version="2026.04.18",
        environment_contract=_shared_contract(),
        generated_at="2026-04-18T12:00:00Z",
    )

    assert report.status == "passed"
    assert report.failing_checks == []


def test_build_environment_drift_report_collects_config_failures() -> None:
    report = build_environment_drift_report(
        expected_environment="staging",
        base_url="https://control.staging.store.korsenex.com",
        release_version="2026.04.18",
        environment_contract=_shared_contract(
            log_format="plain",
            sentry_configured=False,
            object_storage_configured=False,
            security_controls={
                "secure_headers_enabled": True,
                "secure_headers_hsts_enabled": False,
                "secure_headers_csp": "",
                "rate_limits": {
                    "window_seconds": 0,
                    "auth_requests": 0,
                    "activation_requests": 0,
                    "webhook_requests": 0,
                },
            },
        ),
        generated_at="2026-04-18T12:00:00Z",
    )

    assert report.status == "failed"
    assert "log_format_json" in report.failing_checks
    assert "sentry_configured" in report.failing_checks
    assert "object_storage_configured" in report.failing_checks
    assert "secure_headers_hsts_enabled" in report.failing_checks


def test_write_environment_drift_report_writes_expected_json(tmp_path: Path) -> None:
    report = build_environment_drift_report(
        expected_environment="staging",
        base_url="https://control.staging.store.korsenex.com",
        release_version="2026.04.18",
        environment_contract=_shared_contract(),
        generated_at="2026-04-18T12:00:00Z",
    )
    output_path = tmp_path / "environment-drift.json"
    write_environment_drift_report(report, output_path=output_path)
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert payload["status"] == "passed"
    assert summarize_environment_drift_report(report) == "environment contract verified"
