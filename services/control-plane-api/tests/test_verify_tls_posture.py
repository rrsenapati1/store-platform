from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "verify_tls_posture.py"
    spec = importlib.util.spec_from_file_location("verify_tls_posture_script", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_verify_tls_posture_writes_json_report(tmp_path: Path) -> None:
    module = _load_script_module()
    output_path = tmp_path / "tls-posture.json"

    result = module.verify_tls_posture(
        base_url="https://control.store.korsenex.com",
        min_days_remaining=30,
        output_path=output_path,
        inspect_tls=lambda **_: {
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
        },
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert result["status"] == "passed"
    assert payload["host"] == "control.store.korsenex.com"


def test_verify_tls_posture_returns_failed_report_when_tls_is_near_expiry(tmp_path: Path) -> None:
    module = _load_script_module()

    result = module.verify_tls_posture(
        base_url="https://control.store.korsenex.com",
        min_days_remaining=30,
        output_path=tmp_path / "tls-posture.json",
        inspect_tls=lambda **_: {
            "scheme": "https",
            "host": "control.store.korsenex.com",
            "port": 443,
            "subject_common_name": "control.store.korsenex.com",
            "san_dns_names": ["control.store.korsenex.com"],
            "protocol": "TLSv1.3",
            "cipher": "TLS_AES_256_GCM_SHA384",
            "not_before": "2026-04-01T00:00:00Z",
            "not_after": "2026-04-21T00:00:00Z",
            "days_remaining": 3,
        },
    )

    assert result["status"] == "failed"


def test_verify_tls_posture_main_returns_non_zero(monkeypatch, tmp_path: Path) -> None:
    module = _load_script_module()
    output_path = tmp_path / "tls-posture.json"
    monkeypatch.setattr(
        module,
        "verify_tls_posture",
        lambda **_: {
            "status": "failed",
            "failing_checks": ["certificate_validity_window"],
            "summary": "1 checks failed: certificate_validity_window",
            "output_path": str(output_path),
        },
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "verify_tls_posture.py",
            "--base-url",
            "https://control.store.korsenex.com",
            "--output-path",
            str(output_path),
        ],
    )

    assert module.main() == 1
