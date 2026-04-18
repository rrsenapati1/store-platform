from __future__ import annotations

import json
from pathlib import Path

from store_control_plane.release_gate_orchestration import run_release_gate, write_release_gate_report


class FakeRetrievalReport:
    def __init__(self, *, status: str) -> None:
        self.status = status

    def to_dict(self) -> dict[str, object]:
        return {"status": self.status}


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_run_release_gate_writes_passed_report_with_retrieval_verification(tmp_path: Path) -> None:
    def fake_vulnerability_scan(*, output_path: Path, **_: object) -> dict[str, object]:
        payload = {"status": "passed", "failing_surfaces": []}
        _write_json(output_path, payload)
        return payload | {"output_path": str(output_path)}

    def fake_operational_alert(*, output_path: Path, **_: object) -> dict[str, object]:
        payload = {"status": "passed", "failing_checks": []}
        _write_json(output_path, payload)
        return payload | {"output_path": str(output_path)}

    def fake_environment_drift(*, output_path: Path, **_: object) -> dict[str, object]:
        payload = {"status": "passed", "failing_checks": []}
        _write_json(output_path, payload)
        return payload | {"output_path": str(output_path)}

    def fake_tls(*, output_path: Path, **_: object) -> dict[str, object]:
        payload = {"status": "passed", "failing_checks": []}
        _write_json(output_path, payload)
        return payload | {"output_path": str(output_path)}

    def fake_sbom(*, output_path: Path, raw_output_dir: Path, **_: object) -> dict[str, object]:
        raw_output_dir.mkdir(parents=True, exist_ok=True)
        (raw_output_dir / "control-plane-api.cdx.json").write_text('{"bomFormat":"CycloneDX"}', encoding="utf-8")
        payload = {"status": "passed", "failing_surfaces": []}
        _write_json(output_path, payload)
        return payload | {"output_path": str(output_path)}

    def fake_license(*, output_path: Path, **_: object) -> dict[str, object]:
        payload = {"status": "passed", "failing_surfaces": []}
        _write_json(output_path, payload)
        return payload | {"output_path": str(output_path)}

    def fake_package_release(*, release_version: str, output_dir: Path, **_: object) -> dict[str, object]:
        output_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = output_dir / f"store-control-plane-{release_version}.manifest.json"
        provenance_path = output_dir / f"store-control-plane-{release_version}.provenance.json"
        archive_path = output_dir / f"store-control-plane-{release_version}.tar.gz"
        _write_json(
            manifest_path,
            {
                "release_version": release_version,
                "bundle_name": f"store-control-plane-{release_version}",
                "alembic_head": "20260419_0047_release_gate_orchestration",
                "built_at": "2026-04-19T00:00:00Z",
            },
        )
        _write_json(provenance_path, {"status": "passed", "failure_reason": None})
        archive_path.write_bytes(b"archive")
        return {
            "archive_path": str(archive_path),
            "manifest_path": str(manifest_path),
            "provenance_report_path": str(provenance_path),
        }

    def fake_deployed_load(*, output_path: Path, **_: object) -> dict[str, object]:
        payload = {"status": "passed", "failing_scenarios": []}
        _write_json(output_path, payload)
        return payload | {"output_path": str(output_path)}

    def fake_rollback(*, output_path: Path, **_: object) -> dict[str, object]:
        payload = {"status": "passed", "failure_reason": None}
        _write_json(output_path, payload)
        return payload | {"output_path": str(output_path)}

    def fake_restore_drill(*, output_path: Path, **_: object) -> dict[str, object]:
        payload = {"status": "passed", "failure_reason": None}
        _write_json(output_path, payload)
        return payload | {"output_path": str(output_path)}

    def fake_generate_evidence(
        *,
        output_path: Path,
        certification_output_path: Path,
        evidence_bundle_output_dir: Path,
        evidence_publication_output_dir: Path,
        retain_evidence_offsite: bool,
        **_: object,
    ) -> dict[str, object]:
        output_path.write_text("# Evidence\n", encoding="utf-8")
        _write_json(certification_output_path, {"status": "approved"})
        evidence_bundle_output_dir.mkdir(parents=True, exist_ok=True)
        _write_json(evidence_bundle_output_dir / "bundle-manifest.json", {"status": "passed"})
        evidence_publication_output_dir.mkdir(parents=True, exist_ok=True)
        publication_manifest_path = evidence_publication_output_dir / "prod-2026.04.19.publication.json"
        publication_manifest_path.write_text(json.dumps({"status": "published"}), encoding="utf-8")
        retention_manifest_path = evidence_publication_output_dir / "prod-2026.04.19.offsite-retention.json"
        if retain_evidence_offsite:
            retention_manifest_path.write_text(json.dumps({"status": "retained"}), encoding="utf-8")
        return {
            "final_status": "approved",
            "output_path": str(output_path),
            "certification_output_path": str(certification_output_path),
            "certification_result": {"status": "approved"},
            "evidence_bundle_result": {"status": "passed"},
            "evidence_publication_result": {
                "status": "published",
                "publication_manifest_path": str(publication_manifest_path),
            },
            "offsite_retention_result": {
                "status": "retained",
                "retention_manifest_path": str(retention_manifest_path),
            },
        }

    result = run_release_gate(
        base_url="https://control.store.korsenex.com",
        expected_environment="prod",
        expected_release_version="2026.04.19",
        release_owner="ops@store.korsenex.com",
        output_dir=tmp_path / "release-gate",
        admin_bearer_token="admin-token",
        branch_bearer_token="branch-token",
        tenant_id="tenant-1",
        branch_id="branch-1",
        product_id="product-1",
        dump_key="control-plane/prod/postgres-backups/restore.dump",
        metadata_key="control-plane/prod/postgres-backups/metadata.json",
        target_database_url="postgresql+asyncpg://store:secret@db.internal:5432/store_restore",
        retain_evidence_offsite=True,
        verify_retained_evidence=True,
        image_refs=["store-control-plane-api:prod"],
        run_vulnerability_scans=fake_vulnerability_scan,
        verify_operational_alert_posture=fake_operational_alert,
        verify_environment_drift=fake_environment_drift,
        verify_tls_posture=fake_tls,
        generate_sbom_bundle=fake_sbom,
        run_license_compliance=fake_license,
        package_release=fake_package_release,
        verify_deployed_load_posture=fake_deployed_load,
        verify_release_rollback=fake_rollback,
        run_restore_drill=fake_restore_drill,
        generate_release_candidate_evidence=fake_generate_evidence,
        verify_retained_release_evidence=lambda **_: FakeRetrievalReport(status="passed"),
    )

    assert result["status"] == "passed"
    assert result["certification_status"] == "approved"
    assert result["retained_evidence_status"] == "passed"
    assert result["environment"] == "prod"
    assert result["release_version"] == "2026.04.19"
    assert result["release_owner"] == "ops@store.korsenex.com"
    report_payload = json.loads(Path(result["report_path"]).read_text(encoding="utf-8"))
    assert report_payload["status"] == "passed"
    assert report_payload["environment"] == "prod"
    assert report_payload["release_version"] == "2026.04.19"
    assert report_payload["report_paths"]["vulnerability_scan_report"].endswith("vulnerability-scan-report.json")


def test_run_release_gate_blocks_when_retained_evidence_verification_fails(tmp_path: Path) -> None:
    def fake_simple_report(*, output_path: Path, **_: object) -> dict[str, object]:
        payload = {"status": "passed", "failing_checks": [], "failing_surfaces": [], "failing_scenarios": []}
        _write_json(output_path, payload)
        return payload | {"output_path": str(output_path)}

    def fake_package_release(*, release_version: str, output_dir: Path, **_: object) -> dict[str, object]:
        output_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = output_dir / f"store-control-plane-{release_version}.manifest.json"
        provenance_path = output_dir / f"store-control-plane-{release_version}.provenance.json"
        archive_path = output_dir / f"store-control-plane-{release_version}.tar.gz"
        _write_json(
            manifest_path,
            {
                "release_version": release_version,
                "bundle_name": f"store-control-plane-{release_version}",
                "alembic_head": "20260419_0047_release_gate_orchestration",
                "built_at": "2026-04-19T00:00:00Z",
            },
        )
        _write_json(provenance_path, {"status": "passed", "failure_reason": None})
        archive_path.write_bytes(b"archive")
        return {
            "archive_path": str(archive_path),
            "manifest_path": str(manifest_path),
            "provenance_report_path": str(provenance_path),
        }

    def fake_generate_evidence(
        *,
        output_path: Path,
        certification_output_path: Path,
        evidence_bundle_output_dir: Path,
        evidence_publication_output_dir: Path,
        retain_evidence_offsite: bool,
        **_: object,
    ) -> dict[str, object]:
        output_path.write_text("# Evidence\n", encoding="utf-8")
        _write_json(certification_output_path, {"status": "approved"})
        evidence_bundle_output_dir.mkdir(parents=True, exist_ok=True)
        _write_json(evidence_bundle_output_dir / "bundle-manifest.json", {"status": "passed"})
        evidence_publication_output_dir.mkdir(parents=True, exist_ok=True)
        publication_manifest_path = evidence_publication_output_dir / "prod-2026.04.19.publication.json"
        publication_manifest_path.write_text(json.dumps({"status": "published"}), encoding="utf-8")
        retention_manifest_path = evidence_publication_output_dir / "prod-2026.04.19.offsite-retention.json"
        if retain_evidence_offsite:
            retention_manifest_path.write_text(json.dumps({"status": "retained"}), encoding="utf-8")
        return {
            "final_status": "approved",
            "output_path": str(output_path),
            "certification_output_path": str(certification_output_path),
            "certification_result": {"status": "approved"},
            "evidence_bundle_result": {"status": "passed"},
            "evidence_publication_result": {
                "status": "published",
                "publication_manifest_path": str(publication_manifest_path),
            },
            "offsite_retention_result": {
                "status": "retained",
                "retention_manifest_path": str(retention_manifest_path),
            },
        }

    result = run_release_gate(
        base_url="https://control.store.korsenex.com",
        expected_environment="prod",
        expected_release_version="2026.04.19",
        release_owner="ops@store.korsenex.com",
        output_dir=tmp_path / "release-gate",
        admin_bearer_token="admin-token",
        branch_bearer_token="branch-token",
        tenant_id="tenant-1",
        branch_id="branch-1",
        product_id="product-1",
        dump_key="control-plane/prod/postgres-backups/restore.dump",
        metadata_key="control-plane/prod/postgres-backups/metadata.json",
        target_database_url="postgresql+asyncpg://store:secret@db.internal:5432/store_restore",
        retain_evidence_offsite=True,
        verify_retained_evidence=True,
        image_refs=["store-control-plane-api:prod"],
        run_vulnerability_scans=fake_simple_report,
        verify_operational_alert_posture=fake_simple_report,
        verify_environment_drift=fake_simple_report,
        verify_tls_posture=fake_simple_report,
        generate_sbom_bundle=fake_simple_report,
        run_license_compliance=fake_simple_report,
        package_release=fake_package_release,
        verify_deployed_load_posture=fake_simple_report,
        verify_release_rollback=fake_simple_report,
        run_restore_drill=fake_simple_report,
        generate_release_candidate_evidence=fake_generate_evidence,
        verify_retained_release_evidence=lambda **_: FakeRetrievalReport(status="failed"),
    )

    assert result["status"] == "blocked"
    assert result["retained_evidence_status"] == "failed"
    assert "retained evidence retrieval verification failed" in result["summary"]


def test_write_release_gate_report_writes_json(tmp_path: Path) -> None:
    output_path = tmp_path / "release-gate-report.json"
    payload = {"status": "passed"}

    written_path = write_release_gate_report(payload, output_path=output_path)

    assert written_path == output_path
    assert json.loads(output_path.read_text(encoding="utf-8"))["status"] == "passed"
