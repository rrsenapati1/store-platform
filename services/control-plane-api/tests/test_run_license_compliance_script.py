from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "run_license_compliance.py"
    spec = importlib.util.spec_from_file_location("run_license_compliance_script", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_run_license_compliance_writes_json_report(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    module = _load_script_module()
    output_path = tmp_path / "license-report.json"
    sbom_report_path = tmp_path / "sbom-report.json"

    def fake_run_license_compliance(**_: object) -> dict[str, object]:
        output_path.write_text(
            json.dumps(
                {
                    "status": "passed",
                    "surfaces": {
                        "control_plane_api": {
                            "status": "passed",
                            "artifact_path": str(tmp_path / "control-plane.cdx.json"),
                            "component_count": 42,
                            "license_summary": {"allowed": 42, "review_required": 0, "denied": 0, "unknown": 0},
                            "findings": [],
                            "failure_reason": None,
                        }
                    },
                    "failing_surfaces": [],
                }
            ),
            encoding="utf-8",
        )
        return {
            "status": "passed",
            "surfaces": {
                "control_plane_api": {
                    "status": "passed",
                    "artifact_path": str(tmp_path / "control-plane.cdx.json"),
                    "component_count": 42,
                    "license_summary": {"allowed": 42, "review_required": 0, "denied": 0, "unknown": 0},
                    "findings": [],
                    "failure_reason": None,
                }
            },
            "failing_surfaces": [],
            "output_path": str(output_path),
            "summary": "all license compliance surfaces passed",
        }

    monkeypatch.setattr(module, "run_license_compliance", fake_run_license_compliance)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_license_compliance.py",
            "--sbom-report",
            str(sbom_report_path),
            "--output-path",
            str(output_path),
        ],
    )

    exit_code = module.main()

    assert exit_code == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["status"] == "passed"
    assert payload["surfaces"]["control_plane_api"]["license_summary"]["allowed"] == 42


def test_run_license_compliance_exits_non_zero_on_failed_posture(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    module = _load_script_module()
    output_path = tmp_path / "license-report.json"
    sbom_report_path = tmp_path / "sbom-report.json"

    monkeypatch.setattr(
        module,
        "run_license_compliance",
        lambda **_: {
            "status": "failed",
            "surfaces": {},
            "failing_surfaces": ["control_plane_api"],
            "output_path": str(output_path),
            "summary": "1 surfaces failed: control_plane_api",
        },
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_license_compliance.py",
            "--sbom-report",
            str(sbom_report_path),
            "--output-path",
            str(output_path),
        ],
    )

    assert module.main() == 1
