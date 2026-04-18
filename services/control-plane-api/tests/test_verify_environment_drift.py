from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "verify_environment_drift.py"
    spec = importlib.util.spec_from_file_location("verify_environment_drift_script", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_verify_environment_drift_writes_json_report(tmp_path: Path) -> None:
    module = _load_script_module()
    output_path = tmp_path / "environment-drift.json"

    def fake_verify_deployed(**_: object) -> dict[str, object]:
        return {
            "status": "ok",
            "environment": "staging",
            "release_version": "2026.04.18",
        }

    def fake_send_request(method: str, url: str, **_: object) -> dict[str, object]:
        assert method == "GET"
        if url.endswith("/v1/system/environment-contract"):
            return {
                "status_code": 200,
                "json": {
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
                },
            }
        raise AssertionError(f"unexpected {method} {url}")

    result = module.verify_environment_drift(
        base_url="https://control.staging.store.korsenex.com",
        expected_environment="staging",
        expected_release_version="2026.04.18",
        output_path=output_path,
        verify_deployed=fake_verify_deployed,
        send_request=fake_send_request,
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert result["status"] == "passed"
    assert payload["environment"] == "staging"


def test_verify_environment_drift_returns_failed_report_when_contract_drift_exists(tmp_path: Path) -> None:
    module = _load_script_module()

    result = module.verify_environment_drift(
        base_url="https://control.staging.store.korsenex.com",
        expected_environment="staging",
        expected_release_version="2026.04.18",
        output_path=tmp_path / "environment-drift.json",
        verify_deployed=lambda **_: {
            "status": "ok",
            "environment": "staging",
            "release_version": "2026.04.18",
        },
        send_request=lambda method, url, **kwargs: {
            "status_code": 200,
            "json": {
                "deployment_environment": "staging",
                "public_base_url": "https://control.staging.store.korsenex.com",
                "release_version": "2026.04.18",
                "log_format": "plain",
                "sentry_configured": False,
                "sentry_environment": "staging",
                "object_storage_configured": False,
                "object_storage_bucket": None,
                "object_storage_prefix": None,
                "operations_worker": {
                    "configured": True,
                    "poll_seconds": 5,
                    "batch_size": 25,
                    "lease_seconds": 60,
                },
                "security_controls": {
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
            },
        },
    )

    assert result["status"] == "failed"


def test_verify_environment_drift_main_returns_non_zero(monkeypatch, tmp_path: Path) -> None:
    module = _load_script_module()
    output_path = tmp_path / "environment-drift.json"
    monkeypatch.setattr(
        module,
        "verify_environment_drift",
        lambda **_: {
            "status": "failed",
            "failing_checks": ["log_format_json"],
            "summary": "1 checks failed: log_format_json",
            "output_path": str(output_path),
        },
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "verify_environment_drift.py",
            "--base-url",
            "https://control.staging.store.korsenex.com",
            "--expected-environment",
            "staging",
            "--expected-release-version",
            "2026.04.18",
            "--output-path",
            str(output_path),
        ],
    )

    assert module.main() == 1
