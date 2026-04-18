from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
from pathlib import Path

from ..config import Settings
from .object_storage import ObjectStorageClientProtocol, build_object_storage_client


@dataclass(slots=True)
class ReleaseEvidenceRetentionPlan:
    bucket: str
    archive_key: str
    publication_manifest_key: str
    catalog_key: str
    retention_manifest_key: str
    archive_path: Path
    publication_manifest_path: Path
    catalog_path: Path
    retention_manifest_path: Path
    manifest: dict[str, object]


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _join_key(*segments: str | None) -> str:
    return "/".join(segment for segment in segments if segment)


def create_release_evidence_retention_plan(
    settings: Settings,
    *,
    publication_dir: Path,
    environment: str,
    release_version: str,
    now: datetime,
) -> ReleaseEvidenceRetentionPlan:
    if not settings.object_storage_bucket:
        raise ValueError("object storage bucket is required for offsite evidence retention")

    archive_name = f"store-release-evidence-{environment}-{release_version}.tar.gz"
    publication_manifest_name = f"{environment}-{release_version}.publication.json"
    retention_manifest_name = f"{environment}-{release_version}.offsite-retention.json"
    archive_path = publication_dir / archive_name
    publication_manifest_path = publication_dir / publication_manifest_name
    catalog_path = publication_dir / "release-evidence-catalog.json"
    retention_manifest_path = publication_dir / retention_manifest_name

    for required_path in (archive_path, publication_manifest_path, catalog_path):
        if not required_path.exists():
            raise FileNotFoundError(f"missing publication artifact: {required_path}")

    publication_manifest = _load_json(publication_manifest_path)
    base_prefix = _join_key(
        settings.object_storage_prefix,
        settings.release_evidence_artifact_prefix,
        environment,
        release_version,
    )
    catalog_key = _join_key(
        settings.object_storage_prefix,
        settings.release_evidence_artifact_prefix,
        "release-evidence-catalog.json",
    )
    archive_key = _join_key(base_prefix, archive_name)
    publication_manifest_key = _join_key(base_prefix, publication_manifest_name)
    retention_manifest_key = _join_key(base_prefix, retention_manifest_name)

    manifest: dict[str, object] = {
        "environment": environment,
        "release_version": release_version,
        "published_at": now.astimezone(UTC).isoformat(),
        "bucket": settings.object_storage_bucket,
        "archive_key": archive_key,
        "publication_manifest_key": publication_manifest_key,
        "catalog_key": catalog_key,
        "retention_manifest_key": retention_manifest_key,
        "archive_sha256": _hash_file(archive_path),
        "publication_manifest_sha256": _hash_file(publication_manifest_path),
        "catalog_sha256": _hash_file(catalog_path),
        "certification_status": publication_manifest.get("certification_status"),
    }

    return ReleaseEvidenceRetentionPlan(
        bucket=settings.object_storage_bucket,
        archive_key=archive_key,
        publication_manifest_key=publication_manifest_key,
        catalog_key=catalog_key,
        retention_manifest_key=retention_manifest_key,
        archive_path=archive_path,
        publication_manifest_path=publication_manifest_path,
        catalog_path=catalog_path,
        retention_manifest_path=retention_manifest_path,
        manifest=manifest,
    )


def run_release_evidence_retention(
    settings: Settings,
    *,
    publication_dir: Path,
    environment: str,
    release_version: str,
    now: datetime | None = None,
    storage_client: ObjectStorageClientProtocol | None = None,
) -> ReleaseEvidenceRetentionPlan:
    resolved_now = now or datetime.now(UTC)
    plan = create_release_evidence_retention_plan(
        settings,
        publication_dir=publication_dir,
        environment=environment,
        release_version=release_version,
        now=resolved_now,
    )
    plan.retention_manifest_path.write_text(json.dumps(plan.manifest, indent=2), encoding="utf-8")

    client = storage_client or build_object_storage_client(settings)
    metadata = {
        "environment": environment,
        "release_version": release_version,
        "certification_status": str(plan.manifest.get("certification_status") or ""),
    }
    client.upload_file(local_path=plan.archive_path, bucket=plan.bucket, key=plan.archive_key, metadata=metadata)
    client.upload_file(
        local_path=plan.publication_manifest_path,
        bucket=plan.bucket,
        key=plan.publication_manifest_key,
        metadata=metadata,
        content_type="application/json",
    )
    client.upload_file(
        local_path=plan.catalog_path,
        bucket=plan.bucket,
        key=plan.catalog_key,
        metadata=metadata,
        content_type="application/json",
    )
    client.upload_file(
        local_path=plan.retention_manifest_path,
        bucket=plan.bucket,
        key=plan.retention_manifest_key,
        metadata=metadata,
        content_type="application/json",
    )
    return plan
