from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "verify_release_rollback.py"
    spec = importlib.util.spec_from_file_location("verify_release_rollback_script", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_verify_release_rollback_writes_json_report(tmp_path: Path) -> None:
    module = _load_script_module()
    manifest_path = tmp_path / "store-control-plane-2026.04.17.manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "release_version": "2026.04.17",
                "alembic_head": "20260418_0049_rollback_verification_foundation",
                "bundle_name": "store-control-plane-2026.04.17",
                "built_at": "2026-04-17T04:00:00Z",
            }
        ),
        encoding="utf-8",
    )
    output_path = tmp_path / "rollback-report.json"

    def fake_verify_deployed(**_: object) -> dict[str, object]:
        return {
            "status": "ok",
            "environment": "staging",
            "release_version": "2026.04.18",
            "alembic_head": "20260418_0049_rollback_verification_foundation",
        }

    result = module.verify_release_rollback(
        base_url="https://control.staging.store.korsenex.com",
        target_bundle_manifest_path=manifest_path,
        output_path=output_path,
        verify_deployed=fake_verify_deployed,
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert result["status"] == "passed"
    assert payload["target_release_version"] == "2026.04.17"


def test_verify_release_rollback_returns_failed_report_for_schema_mismatch(tmp_path: Path) -> None:
    module = _load_script_module()
    manifest_path = tmp_path / "store-control-plane-2026.04.17.manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "release_version": "2026.04.17",
                "alembic_head": "20260417_0048_previous_head",
                "bundle_name": "store-control-plane-2026.04.17",
                "built_at": "2026-04-17T04:00:00Z",
            }
        ),
        encoding="utf-8",
    )

    result = module.verify_release_rollback(
        base_url="https://control.staging.store.korsenex.com",
        target_bundle_manifest_path=manifest_path,
        output_path=tmp_path / "rollback-report.json",
        verify_deployed=lambda **_: {
            "status": "ok",
            "environment": "staging",
            "release_version": "2026.04.18",
            "alembic_head": "20260418_0049_rollback_verification_foundation",
        },
    )

    assert result["status"] == "failed"
    assert result["rollback_mode"] == "restore_required"


def test_verify_release_rollback_main_returns_non_zero(monkeypatch, tmp_path: Path) -> None:
    module = _load_script_module()
    output_path = tmp_path / "rollback-report.json"
    manifest_path = tmp_path / "store-control-plane-2026.04.17.manifest.json"
    manifest_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        module,
        "verify_release_rollback",
        lambda **_: {
            "status": "failed",
            "rollback_mode": "restore_required",
            "summary": "target bundle schema head differs from deployed schema head",
            "output_path": str(output_path),
        },
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "verify_release_rollback.py",
            "--base-url",
            "https://control.staging.store.korsenex.com",
            "--target-bundle-manifest",
            str(manifest_path),
            "--output-path",
            str(output_path),
        ],
    )

    assert module.main() == 1
