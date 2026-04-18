from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "verify_deployed_load_posture.py"
    spec = importlib.util.spec_from_file_location("verify_deployed_load_posture_script", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_verify_deployed_load_posture_writes_json_report(tmp_path: Path) -> None:
    module = _load_script_module()
    output_path = tmp_path / "deployed-load-report.json"

    def fake_verify_deployed(**_: object) -> dict[str, object]:
        return {
            "status": "ok",
            "environment": "staging",
            "release_version": "2026.04.18-rc4",
        }

    def fake_send_request(method: str, url: str, **_: object) -> dict[str, object]:
        return {"status_code": 200, "json": {"status": "ok"}}

    result = module.verify_deployed_load_posture(
        base_url="https://control.staging.store.korsenex.com",
        expected_environment="staging",
        expected_release_version="2026.04.18-rc4",
        admin_bearer_token="admin-token",
        branch_bearer_token="branch-token",
        tenant_id="tenant-1",
        branch_id="branch-1",
        product_id="product-1",
        output_path=output_path,
        concurrency=2,
        iterations_per_worker=2,
        verify_deployed=fake_verify_deployed,
        send_request=fake_send_request,
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert result["status"] == "passed"
    assert payload["environment"] == "staging"
    assert payload["scenario_results"][0]["scenario_name"]


def test_verify_deployed_load_posture_requires_fixture_inputs(tmp_path: Path) -> None:
    module = _load_script_module()

    try:
        module.verify_deployed_load_posture(
            base_url="https://control.staging.store.korsenex.com",
            output_path=tmp_path / "deployed-load-report.json",
            admin_bearer_token=None,
            branch_bearer_token="branch-token",
            tenant_id="tenant-1",
            branch_id="branch-1",
            product_id="product-1",
            verify_deployed=lambda **_: {
                "status": "ok",
                "environment": "staging",
                "release_version": "2026.04.18-rc4",
            },
            send_request=lambda *args, **kwargs: {"status_code": 200, "json": {"status": "ok"}},
        )
    except ValueError as exc:
        assert "admin_bearer_token" in str(exc)
    else:
        raise AssertionError("expected missing fixture validation to fail")


def test_verify_deployed_load_posture_main_returns_non_zero(monkeypatch, tmp_path: Path) -> None:
    module = _load_script_module()
    output_path = tmp_path / "deployed-load-report.json"
    monkeypatch.setattr(
        module,
        "verify_deployed_load_posture",
        lambda **_: {
            "status": "failed",
            "failing_scenarios": ["checkout_price_preview_http"],
            "output_path": str(output_path),
            "summary": "1 scenarios failed: checkout_price_preview_http",
        },
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "verify_deployed_load_posture.py",
            "--base-url",
            "https://control.staging.store.korsenex.com",
            "--output-path",
            str(output_path),
            "--admin-bearer-token",
            "admin-token",
            "--branch-bearer-token",
            "branch-token",
            "--tenant-id",
            "tenant-1",
            "--branch-id",
            "branch-1",
            "--product-id",
            "product-1",
        ],
    )

    assert module.main() == 1
