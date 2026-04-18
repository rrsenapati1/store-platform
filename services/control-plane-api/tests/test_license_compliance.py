from __future__ import annotations

import importlib.util
import json
from datetime import date
from pathlib import Path

import pytest


def _load_module():
    module_path = Path(__file__).resolve().parents[1] / "store_control_plane" / "license_compliance.py"
    spec = importlib.util.spec_from_file_location("store_control_plane.license_compliance", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_build_license_compliance_report_marks_failed_surface_when_denied_findings_present() -> None:
    module = _load_module()

    report = module.build_license_compliance_report(
        generated_at="2026-04-18T18:00:00Z",
        surface_results={
            "control_plane_api": {
                "status": "failed",
                "artifact_path": "D:/codes/projects/store/docs/launch/evidence/control-plane.cdx.json",
                "component_count": 12,
                "license_summary": {"allowed": 11, "review_required": 0, "denied": 1, "unknown": 0},
                "findings": [
                    {
                        "package_or_identifier": "copyleft-lib",
                        "license": "GPL-3.0-only",
                        "status": "denied",
                    }
                ],
                "failure_reason": None,
            }
        },
    )

    assert report["status"] == "failed"
    assert report["failing_surfaces"] == ["control_plane_api"]
    assert report["surfaces"]["control_plane_api"]["license_summary"]["denied"] == 1


def test_apply_license_exceptions_ignores_matching_non_expired_finding() -> None:
    module = _load_module()

    filtered = module.apply_license_exceptions(
        surface="control_plane_api",
        findings=[
            {
                "package_or_identifier": "copyleft-lib",
                "license": "GPL-3.0-only",
                "status": "denied",
            }
        ],
        exceptions=[
            {
                "surface": "control_plane_api",
                "package_or_identifier": "copyleft-lib",
                "license": "GPL-3.0-only",
                "expires_on": "2026-05-01",
            }
        ],
        today=date(2026, 4, 18),
    )

    assert filtered == []


def test_apply_license_exceptions_fails_expired_exception() -> None:
    module = _load_module()

    with pytest.raises(ValueError, match="expired license exception"):
        module.apply_license_exceptions(
            surface="control_plane_api",
            findings=[],
            exceptions=[
                {
                    "surface": "control_plane_api",
                    "package_or_identifier": "copyleft-lib",
                    "license": "GPL-3.0-only",
                    "expires_on": "2026-04-01",
                }
            ],
            today=date(2026, 4, 18),
        )


def test_run_license_compliance_reads_sbom_artifact_and_flags_unknown_license(tmp_path: Path) -> None:
    module = _load_module()
    sbom_artifact_path = tmp_path / "control-plane.cdx.json"
    sbom_artifact_path.write_text(
        json.dumps(
            {
                "components": [
                    {
                        "name": "allowed-lib",
                        "version": "1.0.0",
                        "licenses": [{"license": {"id": "MIT"}}],
                    },
                    {
                        "name": "mystery-lib",
                        "version": "2.0.0",
                        "licenses": [{"license": {"name": "Custom-Internal-License"}}],
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    sbom_report_path = tmp_path / "sbom-report.json"
    sbom_report_path.write_text(
        json.dumps(
            {
                "status": "passed",
                "surfaces": {
                    "control_plane_api": {
                        "status": "passed",
                        "artifact_path": str(sbom_artifact_path),
                        "component_count": 2,
                    }
                },
                "failing_surfaces": [],
            }
        ),
        encoding="utf-8",
    )
    policy_path = tmp_path / "license-policy.json"
    policy_path.write_text(
        json.dumps(
            {
                "allowed": ["MIT"],
                "review_required": ["LGPL-2.1-only"],
                "denied": ["GPL-3.0-only"],
                "fail_on_unknown": True,
            }
        ),
        encoding="utf-8",
    )
    output_path = tmp_path / "license-compliance-report.json"

    report = module.run_license_compliance(
        sbom_report_path=sbom_report_path,
        output_path=output_path,
        policy_path=policy_path,
    )

    assert report["status"] == "failed"
    assert report["failing_surfaces"] == ["control_plane_api"]
    assert report["surfaces"]["control_plane_api"]["license_summary"]["unknown"] == 1
    assert report["surfaces"]["control_plane_api"]["findings"][0]["package_or_identifier"] == "mystery-lib"
