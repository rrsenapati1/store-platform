from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "generate_sbom_bundle.py"
    spec = importlib.util.spec_from_file_location("generate_sbom_bundle_script", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_generate_sbom_bundle_writes_json_report(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    module = _load_script_module()
    output_path = tmp_path / "sbom-report.json"

    def fake_generate_sbom_bundle(**_: object) -> dict[str, object]:
        output_path.write_text(
            json.dumps(
                {
                    "status": "passed",
                    "surfaces": {
                        "control_plane_api": {
                            "status": "passed",
                            "format": "cyclonedx-json",
                            "component_count": 42,
                            "artifact_path": str(tmp_path / "control-plane-api.cdx.json"),
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
                    "format": "cyclonedx-json",
                    "component_count": 42,
                    "artifact_path": str(tmp_path / "control-plane-api.cdx.json"),
                }
            },
            "failing_surfaces": [],
            "output_path": str(output_path),
            "summary": "1 surfaces passed",
        }

    monkeypatch.setattr(module, "generate_sbom_bundle", fake_generate_sbom_bundle)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "generate_sbom_bundle.py",
            "--output-path",
            str(output_path),
            "--image-ref",
            "store-control-plane-api:staging",
        ],
    )

    exit_code = module.main()

    assert exit_code == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["status"] == "passed"
    assert payload["surfaces"]["control_plane_api"]["format"] == "cyclonedx-json"


def test_generate_sbom_bundle_exits_non_zero_on_failed_posture(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    module = _load_script_module()
    output_path = tmp_path / "sbom-report.json"

    monkeypatch.setattr(
        module,
        "generate_sbom_bundle",
        lambda **_: {
            "status": "failed",
            "surfaces": {},
            "failing_surfaces": ["images"],
            "output_path": str(output_path),
            "summary": "1 surfaces failed: images",
        },
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "generate_sbom_bundle.py",
            "--output-path",
            str(output_path),
        ],
    )

    assert module.main() == 1
