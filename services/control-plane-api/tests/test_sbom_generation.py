from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_module():
    module_path = Path(__file__).resolve().parents[1] / "store_control_plane" / "sbom_generation.py"
    spec = importlib.util.spec_from_file_location("store_control_plane.sbom_generation", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_build_sbom_report_marks_failed_surface_when_generator_unavailable() -> None:
    module = _load_module()

    report = module.build_sbom_report(
        generated_at="2026-04-18T18:00:00Z",
        surface_results={
            "control_plane_api": {
                "tool": "syft",
                "status": "tool-unavailable",
                "command": "syft dir:D:/codes/projects/store/services/control-plane-api -o cyclonedx-json",
                "format": "cyclonedx-json",
                "component_count": 0,
                "artifact_path": None,
                "failure_reason": "syft executable unavailable",
            }
        },
    )

    assert report["status"] == "failed"
    assert report["failing_surfaces"] == ["control_plane_api"]
    assert report["surfaces"]["control_plane_api"]["failure_reason"] == "syft executable unavailable"


def test_write_sbom_report_writes_expected_json(tmp_path: Path) -> None:
    module = _load_module()
    report = module.build_sbom_report(
        generated_at="2026-04-18T18:00:00Z",
        surface_results={
            "control_plane_api": {
                "tool": "syft",
                "status": "passed",
                "command": "syft dir:D:/codes/projects/store/services/control-plane-api -o cyclonedx-json",
                "format": "cyclonedx-json",
                "component_count": 42,
                "artifact_path": str(tmp_path / "control-plane-api.cdx.json"),
                "failure_reason": None,
            }
        },
    )
    output_path = tmp_path / "sbom-report.json"
    module.write_sbom_report(report, output_path=output_path)
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert payload["status"] == "passed"
    assert module.summarize_sbom_report(report) == "1 surfaces passed"
