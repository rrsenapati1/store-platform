from __future__ import annotations

import json
from pathlib import Path
import tarfile

from store_control_plane.config import build_settings
from store_control_plane.ops.release_evidence_retrieval import verify_retained_release_evidence


class RecordingObjectStorageClient:
    def __init__(self, payloads: dict[str, bytes]) -> None:
        self.payloads = payloads
        self.downloads: list[dict[str, object]] = []

    def download_file(self, *, bucket: str, key: str, local_path: Path) -> None:
        local_path.parent.mkdir(parents=True, exist_ok=True)
        self.downloads.append({"bucket": bucket, "key": key, "local_path": local_path})
        local_path.write_bytes(self.payloads[key])


def _make_archive_bytes(root: Path) -> bytes:
    archive_source = root / "bundle"
    (archive_source / "reports").mkdir(parents=True)
    (archive_source / "reports" / "release-candidate-evidence.md").write_text("# Evidence\n", encoding="utf-8")
    (archive_source / "reports" / "launch-readiness-report.json").write_text('{"status":"ready"}', encoding="utf-8")
    (archive_source / "reports" / "launch-readiness-manifest.json").write_text('{"release_version":"2026.04.19"}', encoding="utf-8")
    (archive_source / "bundle-manifest.json").write_text(
        json.dumps(
            {
                "status": "passed",
                "reports": {
                    "release_candidate_evidence": {"bundle_path": "reports/release-candidate-evidence.md"},
                    "launch_readiness_report": {"bundle_path": "reports/launch-readiness-report.json"},
                    "launch_readiness_manifest": {"bundle_path": "reports/launch-readiness-manifest.json"},
                },
            }
        ),
        encoding="utf-8",
    )
    archive_path = root / "store-release-evidence-prod-2026.04.19.tar.gz"
    with tarfile.open(archive_path, "w:gz") as archive:
        for file_path in sorted(path for path in archive_source.rglob("*") if path.is_file()):
            archive.add(file_path, arcname=f"store-release-evidence-prod-2026.04.19/{file_path.relative_to(archive_source).as_posix()}")
    return archive_path.read_bytes()


def test_verify_retained_release_evidence_downloads_and_verifies_hashes(tmp_path: Path) -> None:
    settings = build_settings(
        deployment_environment="prod",
        release_version="2026.04.19",
        object_storage_bucket="store-platform-prod",
        object_storage_prefix="control-plane/prod",
    )
    archive_bytes = _make_archive_bytes(tmp_path)
    publication_manifest = {
        "status": "published",
        "environment": "prod",
        "release_version": "2026.04.19",
        "certification_status": "approved",
    }
    catalog = {
        "publications": [
            {
                "environment": "prod",
                "release_version": "2026.04.19",
                "status": "published",
                "certification_status": "approved",
            }
        ]
    }
    import hashlib

    retention_manifest = {
        "environment": "prod",
        "release_version": "2026.04.19",
        "bucket": "store-platform-prod",
        "archive_key": "control-plane/prod/release-evidence/prod/2026.04.19/store-release-evidence-prod-2026.04.19.tar.gz",
        "publication_manifest_key": "control-plane/prod/release-evidence/prod/2026.04.19/prod-2026.04.19.publication.json",
        "catalog_key": "control-plane/prod/release-evidence/release-evidence-catalog.json",
        "retention_manifest_key": "control-plane/prod/release-evidence/prod/2026.04.19/prod-2026.04.19.offsite-retention.json",
        "archive_sha256": hashlib.sha256(archive_bytes).hexdigest(),
        "publication_manifest_sha256": hashlib.sha256(json.dumps(publication_manifest).encode("utf-8")).hexdigest(),
        "catalog_sha256": hashlib.sha256(json.dumps(catalog).encode("utf-8")).hexdigest(),
        "certification_status": "approved",
    }

    payloads = {
        retention_manifest["retention_manifest_key"]: json.dumps(retention_manifest).encode("utf-8"),
        retention_manifest["archive_key"]: archive_bytes,
        retention_manifest["publication_manifest_key"]: json.dumps(publication_manifest).encode("utf-8"),
        retention_manifest["catalog_key"]: json.dumps(catalog).encode("utf-8"),
    }
    storage = RecordingObjectStorageClient(payloads)

    report = verify_retained_release_evidence(
        settings,
        environment="prod",
        release_version="2026.04.19",
        output_root=tmp_path / "retrieved",
        storage_client=storage,
    )

    assert report.status == "passed"
    assert [record["key"] for record in storage.downloads] == [
        retention_manifest["retention_manifest_key"],
        retention_manifest["archive_key"],
        retention_manifest["publication_manifest_key"],
        retention_manifest["catalog_key"],
    ]
    assert report.archive_check["status"] == "passed"
    assert report.publication_manifest_check["status"] == "passed"
    assert report.catalog_check["status"] == "passed"


def test_verify_retained_release_evidence_fails_when_launch_artifacts_are_missing_from_archive(tmp_path: Path) -> None:
    settings = build_settings(
        deployment_environment="prod",
        release_version="2026.04.19",
        object_storage_bucket="store-platform-prod",
        object_storage_prefix="control-plane/prod",
    )
    archive_source = tmp_path / "broken-bundle"
    (archive_source / "reports").mkdir(parents=True)
    (archive_source / "reports" / "release-candidate-evidence.md").write_text("# Evidence\n", encoding="utf-8")
    (archive_source / "bundle-manifest.json").write_text(
        json.dumps(
            {
                "status": "passed",
                "reports": {
                    "release_candidate_evidence": {"bundle_path": "reports/release-candidate-evidence.md"},
                    "launch_readiness_report": {"bundle_path": "reports/launch-readiness-report.json"},
                },
            }
        ),
        encoding="utf-8",
    )
    broken_archive_path = tmp_path / "store-release-evidence-prod-2026.04.19.tar.gz"
    with tarfile.open(broken_archive_path, "w:gz") as archive:
        for file_path in sorted(path for path in archive_source.rglob("*") if path.is_file()):
            archive.add(file_path, arcname=f"store-release-evidence-prod-2026.04.19/{file_path.relative_to(archive_source).as_posix()}")
    archive_bytes = broken_archive_path.read_bytes()
    publication_manifest = {
        "status": "published",
        "environment": "prod",
        "release_version": "2026.04.19",
        "certification_status": "approved",
        "launch_readiness_status": "ready",
    }
    catalog = {"publications": [{"environment": "prod", "release_version": "2026.04.19"}]}
    import hashlib

    retention_manifest = {
        "environment": "prod",
        "release_version": "2026.04.19",
        "bucket": "store-platform-prod",
        "archive_key": "control-plane/prod/release-evidence/prod/2026.04.19/store-release-evidence-prod-2026.04.19.tar.gz",
        "publication_manifest_key": "control-plane/prod/release-evidence/prod/2026.04.19/prod-2026.04.19.publication.json",
        "catalog_key": "control-plane/prod/release-evidence/release-evidence-catalog.json",
        "retention_manifest_key": "control-plane/prod/release-evidence/prod/2026.04.19/prod-2026.04.19.offsite-retention.json",
        "archive_sha256": hashlib.sha256(archive_bytes).hexdigest(),
        "publication_manifest_sha256": hashlib.sha256(json.dumps(publication_manifest).encode("utf-8")).hexdigest(),
        "catalog_sha256": hashlib.sha256(json.dumps(catalog).encode("utf-8")).hexdigest(),
        "certification_status": "approved",
    }
    payloads = {
        retention_manifest["retention_manifest_key"]: json.dumps(retention_manifest).encode("utf-8"),
        retention_manifest["archive_key"]: archive_bytes,
        retention_manifest["publication_manifest_key"]: json.dumps(publication_manifest).encode("utf-8"),
        retention_manifest["catalog_key"]: json.dumps(catalog).encode("utf-8"),
    }
    storage = RecordingObjectStorageClient(payloads)

    report = verify_retained_release_evidence(
        settings,
        environment="prod",
        release_version="2026.04.19",
        output_root=tmp_path / "retrieved",
        storage_client=storage,
    )

    assert report.status == "failed"
    assert report.archive_check["status"] == "failed"
    assert "launch-readiness-report.json" in str(report.archive_check["reason"])
    assert report.archive_path.exists()
    assert report.retention_manifest_path.exists()


def test_verify_retained_release_evidence_fails_when_archive_hash_mismatches(tmp_path: Path) -> None:
    settings = build_settings(
        deployment_environment="prod",
        release_version="2026.04.19",
        object_storage_bucket="store-platform-prod",
        object_storage_prefix="control-plane/prod",
    )
    archive_bytes = b"wrong-archive"
    publication_manifest = {
        "status": "published",
        "environment": "prod",
        "release_version": "2026.04.19",
        "certification_status": "approved",
    }
    catalog = {"publications": [{"environment": "prod", "release_version": "2026.04.19"}]}
    retention_manifest = {
        "environment": "prod",
        "release_version": "2026.04.19",
        "bucket": "store-platform-prod",
        "archive_key": "control-plane/prod/release-evidence/prod/2026.04.19/store-release-evidence-prod-2026.04.19.tar.gz",
        "publication_manifest_key": "control-plane/prod/release-evidence/prod/2026.04.19/prod-2026.04.19.publication.json",
        "catalog_key": "control-plane/prod/release-evidence/release-evidence-catalog.json",
        "retention_manifest_key": "control-plane/prod/release-evidence/prod/2026.04.19/prod-2026.04.19.offsite-retention.json",
        "archive_sha256": "0" * 64,
        "publication_manifest_sha256": "1" * 64,
        "catalog_sha256": "2" * 64,
        "certification_status": "approved",
    }
    payloads = {
        retention_manifest["retention_manifest_key"]: json.dumps(retention_manifest).encode("utf-8"),
        retention_manifest["archive_key"]: archive_bytes,
        retention_manifest["publication_manifest_key"]: json.dumps(publication_manifest).encode("utf-8"),
        retention_manifest["catalog_key"]: json.dumps(catalog).encode("utf-8"),
    }
    storage = RecordingObjectStorageClient(payloads)

    report = verify_retained_release_evidence(
        settings,
        environment="prod",
        release_version="2026.04.19",
        output_root=tmp_path / "retrieved",
        storage_client=storage,
    )

    assert report.status == "failed"
    assert report.archive_check["status"] == "failed"


def test_verify_retained_release_evidence_tolerates_catalog_hash_drift_when_release_entry_still_exists(tmp_path: Path) -> None:
    settings = build_settings(
        deployment_environment="prod",
        release_version="2026.04.19",
        object_storage_bucket="store-platform-prod",
        object_storage_prefix="control-plane/prod",
    )
    archive_bytes = _make_archive_bytes(tmp_path)
    publication_manifest = {
        "status": "published",
        "environment": "prod",
        "release_version": "2026.04.19",
        "certification_status": "approved",
    }
    catalog = {
        "generated_at": "2026-04-20T00:00:00Z",
        "publications": [
            {
                "environment": "prod",
                "release_version": "2026.04.20",
                "status": "published",
            },
            {
                "environment": "prod",
                "release_version": "2026.04.19",
                "status": "published",
                "certification_status": "approved",
            },
        ],
    }
    import hashlib

    retention_manifest = {
        "environment": "prod",
        "release_version": "2026.04.19",
        "bucket": "store-platform-prod",
        "archive_key": "control-plane/prod/release-evidence/prod/2026.04.19/store-release-evidence-prod-2026.04.19.tar.gz",
        "publication_manifest_key": "control-plane/prod/release-evidence/prod/2026.04.19/prod-2026.04.19.publication.json",
        "catalog_key": "control-plane/prod/release-evidence/release-evidence-catalog.json",
        "retention_manifest_key": "control-plane/prod/release-evidence/prod/2026.04.19/prod-2026.04.19.offsite-retention.json",
        "archive_sha256": hashlib.sha256(archive_bytes).hexdigest(),
        "publication_manifest_sha256": hashlib.sha256(json.dumps(publication_manifest).encode("utf-8")).hexdigest(),
        "catalog_sha256": "f" * 64,
        "certification_status": "approved",
    }
    payloads = {
        retention_manifest["retention_manifest_key"]: json.dumps(retention_manifest).encode("utf-8"),
        retention_manifest["archive_key"]: archive_bytes,
        retention_manifest["publication_manifest_key"]: json.dumps(publication_manifest).encode("utf-8"),
        retention_manifest["catalog_key"]: json.dumps(catalog).encode("utf-8"),
    }
    storage = RecordingObjectStorageClient(payloads)

    report = verify_retained_release_evidence(
        settings,
        environment="prod",
        release_version="2026.04.19",
        output_root=tmp_path / "retrieved",
        storage_client=storage,
    )

    assert report.status == "passed"
    assert report.catalog_check["status"] == "passed"
