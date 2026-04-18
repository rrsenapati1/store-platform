from __future__ import annotations

import json
from pathlib import Path

from store_control_plane.tls_verification import (
    build_tls_posture_report,
    summarize_tls_posture_report,
    write_tls_posture_report,
)


def _inspection(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "scheme": "https",
        "host": "control.store.korsenex.com",
        "port": 443,
        "subject_common_name": "control.store.korsenex.com",
        "san_dns_names": ["control.store.korsenex.com"],
        "protocol": "TLSv1.3",
        "cipher": "TLS_AES_256_GCM_SHA384",
        "not_before": "2026-04-01T00:00:00Z",
        "not_after": "2026-06-01T00:00:00Z",
        "days_remaining": 44,
    }
    payload.update(overrides)
    return payload


def test_build_tls_posture_report_passes_for_valid_https_certificate() -> None:
    report = build_tls_posture_report(
        expected_hostname="control.store.korsenex.com",
        min_days_remaining=30,
        inspection=_inspection(),
        generated_at="2026-04-18T12:00:00Z",
    )

    assert report.status == "passed"
    assert report.failing_checks == []


def test_build_tls_posture_report_collects_expiry_and_hostname_failures() -> None:
    report = build_tls_posture_report(
        expected_hostname="control.store.korsenex.com",
        min_days_remaining=30,
        inspection=_inspection(
            scheme="http",
            subject_common_name="wrong.store.korsenex.com",
            san_dns_names=["wrong.store.korsenex.com"],
            days_remaining=3,
        ),
        generated_at="2026-04-18T12:00:00Z",
    )

    assert report.status == "failed"
    assert "https_required" in report.failing_checks
    assert "hostname_match" in report.failing_checks
    assert "certificate_validity_window" in report.failing_checks


def test_write_tls_posture_report_writes_expected_json(tmp_path: Path) -> None:
    report = build_tls_posture_report(
        expected_hostname="control.store.korsenex.com",
        min_days_remaining=30,
        inspection=_inspection(),
        generated_at="2026-04-18T12:00:00Z",
    )
    output_path = tmp_path / "tls-posture.json"
    write_tls_posture_report(report, output_path=output_path)
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert payload["status"] == "passed"
    assert summarize_tls_posture_report(report) == "tls posture verified"
