from __future__ import annotations

import json
from pathlib import Path

from store_control_plane.launch_gate_orchestration import run_v2_launch_gate, write_v2_launch_gate_report


class FakeRetrievalReport:
    def __init__(self, *, status: str) -> None:
        self.status = status

    def to_dict(self) -> dict[str, object]:
        return {"status": self.status}


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_run_v2_launch_gate_writes_ready_report_and_publishes_launch_bundle(tmp_path: Path) -> None:
    launch_manifest_path = tmp_path / "v2-launch-readiness-manifest.json"
    _write_json(
        launch_manifest_path,
        {
            "release_version": "2026.04.19",
            "environment": "prod",
        },
    )

    def fake_run_release_gate(*, output_dir: Path, **_: object) -> dict[str, object]:
        report_paths = {
            "release_evidence": str(output_dir / "reports" / "release-candidate-evidence.md"),
            "certification_report": str(output_dir / "reports" / "certification-report.json"),
            "vulnerability_scan_report": str(output_dir / "reports" / "vulnerability-scan-report.json"),
        }
        for path in report_paths.values():
            target = Path(path)
            if target.suffix == ".md":
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("# Release Candidate Evidence\n", encoding="utf-8")
            else:
                _write_json(target, {"status": "passed"})
        raw_vulnerability_dir = output_dir / "raw" / "vulnerability-scans"
        raw_sbom_dir = output_dir / "raw" / "sbom"
        raw_vulnerability_dir.mkdir(parents=True, exist_ok=True)
        raw_sbom_dir.mkdir(parents=True, exist_ok=True)
        (raw_vulnerability_dir / "python.json").write_text("{}", encoding="utf-8")
        (raw_sbom_dir / "control-plane-api.cdx.json").write_text("{}", encoding="utf-8")
        report_path = output_dir / "release-gate-report.json"
        payload = {
            "status": "passed",
            "summary": "release certification approved",
            "environment": "prod",
            "release_version": "2026.04.19",
            "release_owner": "release@store.korsenex.com",
            "certification_status": "approved",
            "report_paths": report_paths,
            "report_path": str(report_path),
        }
        _write_json(report_path, payload)
        return payload

    def fake_build_launch_readiness_report(
        *,
        output_path: Path,
        markdown_output_path: Path,
        **_: object,
    ) -> dict[str, object]:
        _write_json(output_path, {"status": "ready"})
        markdown_output_path.write_text("# V2 Launch Readiness Report\n", encoding="utf-8")
        return {
            "status": "ready",
            "summary": "launch readiness ready",
            "output_path": str(output_path),
            "markdown_output_path": str(markdown_output_path),
        }

    def fake_build_release_evidence_bundle(
        *,
        output_dir: Path,
        report_paths: dict[str, Path | None],
        directory_paths: dict[str, Path | None] | None = None,
        **_: object,
    ) -> dict[str, object]:
        output_dir.mkdir(parents=True, exist_ok=True)
        manifest = {
            "status": "passed",
            "reports": {
                label: {"bundle_path": f"reports/{Path(str(path)).name}"}
                for label, path in report_paths.items()
                if path is not None
            },
            "directories": {
                label: {"bundle_path": f"artifacts/{Path(str(path)).name}"}
                for label, path in (directory_paths or {}).items()
                if path is not None
            },
        }
        _write_json(output_dir / "bundle-manifest.json", manifest)
        (output_dir / "bundle-index.md").write_text("# Release Evidence Bundle\n", encoding="utf-8")
        return {
            "status": "passed",
            "output_dir": str(output_dir),
            "manifest_path": str(output_dir / "bundle-manifest.json"),
            "summary": "launch bundle assembled",
        }

    def fake_publish_release_evidence_bundle(
        *,
        output_dir: Path,
        **_: object,
    ) -> dict[str, object]:
        output_dir.mkdir(parents=True, exist_ok=True)
        publication_manifest_path = output_dir / "prod-2026.04.19.publication.json"
        _write_json(
            publication_manifest_path,
            {
                "status": "published",
                "launch_readiness_status": "ready",
            },
        )
        return {
            "status": "published",
            "publication_manifest_path": str(publication_manifest_path),
            "archive_path": str(output_dir / "store-release-evidence-prod-2026.04.19.tar.gz"),
            "catalog_path": str(output_dir / "release-evidence-catalog.json"),
            "summary": "published launch evidence",
        }

    def fake_retain_release_evidence(*_: object, **__: object):
        return type(
            "Plan",
            (),
            {
                "bucket": "store-platform-prod",
                "archive_key": "control-plane/prod/release-evidence/prod/2026.04.19/store-release-evidence-prod-2026.04.19.tar.gz",
                "publication_manifest_key": "control-plane/prod/release-evidence/prod/2026.04.19/prod-2026.04.19.publication.json",
                "catalog_key": "control-plane/prod/release-evidence/release-evidence-catalog.json",
                "retention_manifest_key": "control-plane/prod/release-evidence/prod/2026.04.19/prod-2026.04.19.offsite-retention.json",
                "retention_manifest_path": tmp_path / "v2-launch-gate" / "published" / "prod-2026.04.19.offsite-retention.json",
            },
        )()

    result = run_v2_launch_gate(
        base_url="https://control.store.korsenex.com",
        expected_environment="prod",
        expected_release_version="2026.04.19",
        release_owner="release@store.korsenex.com",
        output_dir=tmp_path / "v2-launch-gate",
        admin_bearer_token="admin-token",
        branch_bearer_token="branch-token",
        tenant_id="tenant-1",
        branch_id="branch-1",
        product_id="product-1",
        dump_key="control-plane/prod/postgres-backups/restore.dump",
        metadata_key="control-plane/prod/postgres-backups/metadata.json",
        target_database_url="postgresql+asyncpg://store:secret@db.internal:5432/store_restore",
        launch_manifest_path=launch_manifest_path,
        retain_evidence_offsite=True,
        verify_retained_evidence=True,
        run_release_gate=fake_run_release_gate,
        build_launch_readiness_report=fake_build_launch_readiness_report,
        build_release_evidence_bundle=fake_build_release_evidence_bundle,
        publish_release_evidence_bundle=fake_publish_release_evidence_bundle,
        retain_release_evidence=fake_retain_release_evidence,
        verify_retained_release_evidence=lambda **_: FakeRetrievalReport(status="passed"),
    )

    assert result["status"] == "ready"
    assert result["technical_gate_status"] == "passed"
    assert result["launch_readiness_status"] == "ready"
    assert result["retained_evidence_status"] == "passed"
    payload = json.loads(Path(result["report_path"]).read_text(encoding="utf-8"))
    assert payload["status"] == "ready"
    assert payload["launch_bundle_result"]["status"] == "passed"
    assert payload["launch_publication_result"]["status"] == "published"


def test_run_v2_launch_gate_holds_when_launch_readiness_report_blocks(tmp_path: Path) -> None:
    launch_manifest_path = tmp_path / "v2-launch-readiness-manifest.json"
    _write_json(launch_manifest_path, {"release_version": "2026.04.19", "environment": "prod"})

    def fake_run_release_gate(*, output_dir: Path, **_: object) -> dict[str, object]:
        report_path = output_dir / "release-gate-report.json"
        payload = {
            "status": "passed",
            "summary": "release certification approved",
            "environment": "prod",
            "release_version": "2026.04.19",
            "release_owner": "release@store.korsenex.com",
            "certification_status": "approved",
            "report_paths": {
                "release_evidence": str(output_dir / "reports" / "release-candidate-evidence.md"),
                "certification_report": str(output_dir / "reports" / "certification-report.json"),
            },
            "report_path": str(report_path),
        }
        Path(payload["report_paths"]["release_evidence"]).parent.mkdir(parents=True, exist_ok=True)
        Path(payload["report_paths"]["release_evidence"]).write_text("# Release Candidate Evidence\n", encoding="utf-8")
        _write_json(Path(payload["report_paths"]["certification_report"]), {"status": "approved"})
        _write_json(report_path, payload)
        return payload

    def fake_build_launch_readiness_report(
        *,
        output_path: Path,
        markdown_output_path: Path,
        **_: object,
    ) -> dict[str, object]:
        _write_json(output_path, {"status": "hold"})
        markdown_output_path.write_text("# V2 Launch Readiness Report\n", encoding="utf-8")
        return {
            "status": "hold",
            "summary": "launch readiness hold",
            "output_path": str(output_path),
            "markdown_output_path": str(markdown_output_path),
        }

    result = run_v2_launch_gate(
        base_url="https://control.store.korsenex.com",
        expected_environment="prod",
        expected_release_version="2026.04.19",
        release_owner="release@store.korsenex.com",
        output_dir=tmp_path / "v2-launch-gate",
        admin_bearer_token="admin-token",
        branch_bearer_token="branch-token",
        tenant_id="tenant-1",
        branch_id="branch-1",
        product_id="product-1",
        dump_key="control-plane/prod/postgres-backups/restore.dump",
        metadata_key="control-plane/prod/postgres-backups/metadata.json",
        target_database_url="postgresql+asyncpg://store:secret@db.internal:5432/store_restore",
        launch_manifest_path=launch_manifest_path,
        run_release_gate=fake_run_release_gate,
        build_launch_readiness_report=fake_build_launch_readiness_report,
    )

    assert result["status"] == "hold"
    assert result["launch_readiness_status"] == "hold"
    assert "launch readiness hold" in result["summary"]


def test_write_v2_launch_gate_report_writes_json(tmp_path: Path) -> None:
    output_path = tmp_path / "v2-launch-gate-report.json"
    payload = {"status": "ready"}

    written_path = write_v2_launch_gate_report(payload, output_path=output_path)

    assert written_path == output_path
    assert json.loads(output_path.read_text(encoding="utf-8"))["status"] == "ready"
