from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "verify_operational_alert_posture.py"
    spec = importlib.util.spec_from_file_location("verify_operational_alert_posture_script", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_verify_operational_alert_posture_writes_json_report(tmp_path: Path) -> None:
    module = _load_script_module()
    output_path = tmp_path / "alert-report.json"

    def fake_verify_deployed(**_: object) -> dict[str, object]:
        return {
            "status": "ok",
            "environment": "staging",
            "release_version": "2026.04.18-rc3",
            "security_result": {"status": "passed"},
        }

    def fake_send_request(method: str, url: str, **_: object) -> dict[str, object]:
        assert method == "GET"
        assert url.endswith("/v1/platform/observability/summary")
        return {
            "status_code": 200,
            "json": {
                "operations": {"dead_letter_count": 0, "retryable_count": 0},
                "runtime": {"degraded_branch_count": 0},
                "backup": {"status": "ok", "age_hours": 1.0},
            },
        }

    result = module.verify_operational_alert_posture(
        base_url="https://control.staging.store.korsenex.com",
        output_path=output_path,
        verify_deployed=fake_verify_deployed,
        send_request=fake_send_request,
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert result["status"] == "passed"
    assert payload["alert_checks"][0]["name"]
    assert payload["environment"] == "staging"


def test_verify_operational_alert_posture_returns_non_zero_on_failed_posture(tmp_path: Path) -> None:
    module = _load_script_module()
    output_path = tmp_path / "alert-report.json"

    def fake_verify_deployed(**_: object) -> dict[str, object]:
        return {
            "status": "ok",
            "environment": "prod",
            "release_version": "2026.04.18-rc3",
            "security_result": {"status": "failed"},
        }

    def fake_send_request(method: str, url: str, **_: object) -> dict[str, object]:
        return {
            "status_code": 200,
            "json": {
                "operations": {"dead_letter_count": 0, "retryable_count": 0},
                "runtime": {"degraded_branch_count": 0},
                "backup": {"status": "ok", "age_hours": 1.0},
            },
        }

    result = module.verify_operational_alert_posture(
        base_url="https://control.store.korsenex.com",
        output_path=output_path,
        verify_deployed=fake_verify_deployed,
        send_request=fake_send_request,
    )

    assert result["status"] == "failed"


def test_verify_operational_alert_posture_main_returns_non_zero(monkeypatch, tmp_path: Path) -> None:
    module = _load_script_module()
    output_path = tmp_path / "alert-report.json"
    monkeypatch.setattr(
        module,
        "verify_operational_alert_posture",
        lambda **_: {
            "status": "failed",
            "failing_checks": ["security_verification_passed"],
            "output_path": str(output_path),
            "summary": "1 alert checks failed: security_verification_passed",
        },
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "verify_operational_alert_posture.py",
            "--base-url",
            "https://control.store.korsenex.com",
            "--output-path",
            str(output_path),
        ],
    )

    assert module.main() == 1
