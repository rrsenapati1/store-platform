from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from store_control_plane.config import build_settings
from store_control_plane.ops.release_evidence_retention import (
    create_release_evidence_retention_plan,
    run_release_evidence_retention,
)


class RecordingObjectStorageClient:
    def __init__(self) -> None:
        self.uploads: list[dict[str, object]] = []

    def upload_file(
        self,
        *,
        local_path: Path,
        bucket: str,
        key: str,
        metadata: dict[str, str] | None = None,
        content_type: str | None = None,
    ) -> None:
        self.uploads.append(
            {
                "local_path": local_path,
                "bucket": bucket,
                "key": key,
                "metadata": metadata,
                "content_type": content_type,
            }
        )


def _create_publication_dir(root: Path) -> Path:
    publication_dir = root / "published"
    publication_dir.mkdir(parents=True, exist_ok=True)
    (publication_dir / "store-release-evidence-prod-2026.04.19.tar.gz").write_bytes(b"archive")
    (publication_dir / "prod-2026.04.19.publication.json").write_text(
        json.dumps(
            {
                "status": "published",
                "environment": "prod",
                "release_version": "2026.04.19",
                "certification_status": "approved",
            }
        ),
        encoding="utf-8",
    )
    (publication_dir / "release-evidence-catalog.json").write_text(
        json.dumps(
            {
                "generated_at": "2026-04-19T00:00:00Z",
                "publications": [
                    {
                        "environment": "prod",
                        "release_version": "2026.04.19",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return publication_dir


def test_create_release_evidence_retention_plan_uses_storage_prefix_and_manifest(tmp_path: Path) -> None:
    settings = build_settings(
        deployment_environment="prod",
        release_version="2026.04.19",
        object_storage_bucket="store-platform-prod",
        object_storage_prefix="control-plane/prod",
    )
    publication_dir = _create_publication_dir(tmp_path)

    plan = create_release_evidence_retention_plan(
        settings,
        publication_dir=publication_dir,
        environment="prod",
        release_version="2026.04.19",
        now=datetime(2026, 4, 19, 12, 0, 0, tzinfo=UTC),
    )

    assert plan.bucket == "store-platform-prod"
    assert plan.archive_key == (
        "control-plane/prod/release-evidence/prod/2026.04.19/"
        "store-release-evidence-prod-2026.04.19.tar.gz"
    )
    assert plan.publication_manifest_key == (
        "control-plane/prod/release-evidence/prod/2026.04.19/prod-2026.04.19.publication.json"
    )
    assert plan.catalog_key == "control-plane/prod/release-evidence/release-evidence-catalog.json"
    assert plan.retention_manifest_key == (
        "control-plane/prod/release-evidence/prod/2026.04.19/prod-2026.04.19.offsite-retention.json"
    )
    assert plan.manifest["environment"] == "prod"
    assert plan.manifest["release_version"] == "2026.04.19"
    assert plan.manifest["certification_status"] == "approved"


def test_run_release_evidence_retention_uploads_archive_manifest_catalog_and_retention_manifest(tmp_path: Path) -> None:
    settings = build_settings(
        deployment_environment="prod",
        release_version="2026.04.19",
        object_storage_bucket="store-platform-prod",
        object_storage_prefix="control-plane/prod",
    )
    publication_dir = _create_publication_dir(tmp_path)
    storage = RecordingObjectStorageClient()

    plan = run_release_evidence_retention(
        settings,
        publication_dir=publication_dir,
        environment="prod",
        release_version="2026.04.19",
        now=datetime(2026, 4, 19, 12, 0, 0, tzinfo=UTC),
        storage_client=storage,
    )

    assert len(storage.uploads) == 4
    assert [upload["key"] for upload in storage.uploads] == [
        plan.archive_key,
        plan.publication_manifest_key,
        plan.catalog_key,
        plan.retention_manifest_key,
    ]
    retention_payload = json.loads(plan.retention_manifest_path.read_text(encoding="utf-8"))
    assert retention_payload["bucket"] == "store-platform-prod"
    assert retention_payload["archive_key"] == plan.archive_key
    assert retention_payload["publication_manifest_key"] == plan.publication_manifest_key
    assert retention_payload["catalog_key"] == plan.catalog_key
    assert retention_payload["certification_status"] == "approved"
