from __future__ import annotations

import json
from pathlib import Path


from store_control_plane.release_evidence_bundle import build_release_evidence_bundle


def test_build_release_evidence_bundle_copies_reports_and_directories(tmp_path: Path) -> None:
    release_evidence_path = tmp_path / "release-candidate-evidence.md"
    release_evidence_path.write_text("# Release Candidate Evidence\n", encoding="utf-8")
    certification_report_path = tmp_path / "certification-report.json"
    certification_report_path.write_text(json.dumps({"status": "approved"}), encoding="utf-8")
    vulnerability_report_path = tmp_path / "vulnerability-report.json"
    vulnerability_report_path.write_text(json.dumps({"status": "passed"}), encoding="utf-8")
    launch_readiness_report_path = tmp_path / "launch-readiness-report.json"
    launch_readiness_report_path.write_text(json.dumps({"status": "ready"}), encoding="utf-8")
    launch_manifest_path = tmp_path / "v2-launch-readiness-manifest.json"
    launch_manifest_path.write_text(json.dumps({"release_version": "2026.04.19"}), encoding="utf-8")

    sbom_artifact_dir = tmp_path / "sbom-artifacts"
    sbom_artifact_dir.mkdir()
    (sbom_artifact_dir / "control-plane-api.cdx.json").write_text('{"bomFormat":"CycloneDX"}', encoding="utf-8")
    vulnerability_raw_output_dir = tmp_path / "vulnerability-raw"
    vulnerability_raw_output_dir.mkdir()
    (vulnerability_raw_output_dir / "python.json").write_text('{"dependencies":[]}', encoding="utf-8")

    output_dir = tmp_path / "evidence-bundle"
    result = build_release_evidence_bundle(
        output_dir=output_dir,
        report_paths={
            "release_candidate_evidence": release_evidence_path,
            "certification_report": certification_report_path,
            "vulnerability_scan_report": vulnerability_report_path,
            "launch_readiness_report": launch_readiness_report_path,
            "launch_readiness_manifest": launch_manifest_path,
        },
        directory_paths={
            "sbom_artifacts": sbom_artifact_dir,
            "vulnerability_raw_output": vulnerability_raw_output_dir,
        },
        generated_at="2026-04-19T00:00:00Z",
    )

    assert result["status"] == "passed"
    manifest_path = Path(str(result["manifest_path"]))
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["status"] == "passed"
    assert manifest["reports"]["release_candidate_evidence"]["bundle_path"].endswith(
        "reports/release-candidate-evidence.md"
    )
    assert manifest["reports"]["launch_readiness_report"]["bundle_path"].endswith(
        "reports/launch-readiness-report.json"
    )
    assert manifest["reports"]["launch_readiness_manifest"]["bundle_path"].endswith(
        "reports/launch-readiness-manifest.json"
    )
    assert manifest["reports"]["vulnerability_scan_report"]["sha256"]
    assert manifest["directories"]["sbom_artifacts"]["file_count"] == 1
    assert manifest["directories"]["vulnerability_raw_output"]["file_count"] == 1
    assert (output_dir / "reports" / "release-candidate-evidence.md").read_text(encoding="utf-8").startswith(
        "# Release Candidate Evidence"
    )
    assert json.loads((output_dir / "reports" / "launch-readiness-report.json").read_text(encoding="utf-8"))["status"] == "ready"
    assert (output_dir / "artifacts" / "sbom-artifacts" / "control-plane-api.cdx.json").exists()

