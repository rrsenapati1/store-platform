from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import tarfile

from ..config import Settings
from .object_storage import ObjectStorageClientProtocol, build_object_storage_client


def _join_key(*segments: str | None) -> str:
    return "/".join(segment for segment in segments if segment)


def _required_manifest_value(manifest: dict[str, object], field: str) -> str:
    raw_value = manifest.get(field)
    if raw_value in {None, ""}:
        raise ValueError(f"retention manifest missing required field: {field}")
    return str(raw_value)


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object in {path}")
    return payload


def _verify_archive(path: Path, *, expected_sha256: str) -> dict[str, object]:
    observed_sha256 = _hash_file(path)
    if observed_sha256 != expected_sha256:
        return {
            "status": "failed",
            "reason": "archive SHA-256 does not match retention manifest",
            "expected_sha256": expected_sha256,
            "observed_sha256": observed_sha256,
        }

    try:
        with tarfile.open(path, "r:gz") as archive:
            members = [member.name for member in archive.getmembers() if member.isfile()]
    except (OSError, tarfile.TarError) as exc:
        return {
            "status": "failed",
            "reason": f"archive is not readable: {exc}",
            "expected_sha256": expected_sha256,
            "observed_sha256": observed_sha256,
        }

    if not any(member.endswith("/bundle-manifest.json") for member in members):
        return {
            "status": "failed",
            "reason": "archive is missing bundle-manifest.json",
            "expected_sha256": expected_sha256,
            "observed_sha256": observed_sha256,
        }
    if not any(member.endswith("/reports/release-candidate-evidence.md") for member in members):
        return {
            "status": "failed",
            "reason": "archive is missing release-candidate evidence markdown",
            "expected_sha256": expected_sha256,
            "observed_sha256": observed_sha256,
        }

    return {
        "status": "passed",
        "reason": "archive hash and required contents verified",
        "expected_sha256": expected_sha256,
        "observed_sha256": observed_sha256,
        "member_count": len(members),
    }


def _verify_publication_manifest(
    path: Path,
    *,
    expected_sha256: str,
    environment: str,
    release_version: str,
    expected_certification_status: str | None,
) -> dict[str, object]:
    observed_sha256 = _hash_file(path)
    if observed_sha256 != expected_sha256:
        return {
            "status": "failed",
            "reason": "publication manifest SHA-256 does not match retention manifest",
            "expected_sha256": expected_sha256,
            "observed_sha256": observed_sha256,
        }

    publication_manifest = _load_json(path)
    manifest_environment = str(publication_manifest.get("environment") or "")
    manifest_release_version = str(publication_manifest.get("release_version") or "")
    manifest_certification_status = publication_manifest.get("certification_status")

    if manifest_environment != environment or manifest_release_version != release_version:
        return {
            "status": "failed",
            "reason": "publication manifest identity does not match requested release",
            "expected_sha256": expected_sha256,
            "observed_sha256": observed_sha256,
            "observed_environment": manifest_environment,
            "observed_release_version": manifest_release_version,
        }
    if expected_certification_status is not None and manifest_certification_status != expected_certification_status:
        return {
            "status": "failed",
            "reason": "publication manifest certification status differs from retention manifest",
            "expected_sha256": expected_sha256,
            "observed_sha256": observed_sha256,
            "expected_certification_status": expected_certification_status,
            "observed_certification_status": manifest_certification_status,
        }

    return {
        "status": "passed",
        "reason": "publication manifest hash and identity verified",
        "expected_sha256": expected_sha256,
        "observed_sha256": observed_sha256,
        "certification_status": manifest_certification_status,
    }


def _verify_catalog(path: Path, *, environment: str, release_version: str) -> dict[str, object]:
    observed_sha256 = _hash_file(path)
    catalog = _load_json(path)
    publications = list(catalog.get("publications") or [])
    matching_entry = next(
        (
            dict(entry)
            for entry in publications
            if isinstance(entry, dict)
            and entry.get("environment") == environment
            and entry.get("release_version") == release_version
        ),
        None,
    )
    if matching_entry is None:
        return {
            "status": "failed",
            "reason": "rolling publication catalog does not contain the retained release entry",
            "observed_sha256": observed_sha256,
        }

    return {
        "status": "passed",
        "reason": "rolling publication catalog still contains the retained release entry",
        "observed_sha256": observed_sha256,
        "entry": matching_entry,
    }


@dataclass(slots=True)
class ReleaseEvidenceRetrievalReport:
    status: str
    environment: str
    release_version: str
    bucket: str
    generated_at: str
    summary: str
    failure_reason: str | None
    retention_manifest_path: Path
    archive_path: Path
    publication_manifest_path: Path
    catalog_path: Path
    archive_check: dict[str, object]
    publication_manifest_check: dict[str, object]
    catalog_check: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["retention_manifest_path"] = str(self.retention_manifest_path)
        payload["archive_path"] = str(self.archive_path)
        payload["publication_manifest_path"] = str(self.publication_manifest_path)
        payload["catalog_path"] = str(self.catalog_path)
        return payload


def verify_retained_release_evidence(
    settings: Settings,
    *,
    environment: str,
    release_version: str,
    output_root: Path,
    generated_at: str | None = None,
    storage_client: ObjectStorageClientProtocol | None = None,
) -> ReleaseEvidenceRetrievalReport:
    if not settings.object_storage_bucket:
        raise ValueError("object storage bucket is required for retained evidence verification")

    output_root.mkdir(parents=True, exist_ok=True)
    base_prefix = _join_key(
        settings.object_storage_prefix,
        settings.release_evidence_artifact_prefix,
        environment,
        release_version,
    )
    retention_manifest_name = f"{environment}-{release_version}.offsite-retention.json"
    retention_manifest_key = _join_key(base_prefix, retention_manifest_name)
    retention_manifest_path = output_root / retention_manifest_name

    client = storage_client or build_object_storage_client(settings)
    client.download_file(
        bucket=settings.object_storage_bucket,
        key=retention_manifest_key,
        local_path=retention_manifest_path,
    )
    retention_manifest = _load_json(retention_manifest_path)
    bucket = _required_manifest_value(retention_manifest, "bucket")
    archive_key = _required_manifest_value(retention_manifest, "archive_key")
    publication_manifest_key = _required_manifest_value(retention_manifest, "publication_manifest_key")
    catalog_key = _required_manifest_value(retention_manifest, "catalog_key")

    archive_path = output_root / Path(archive_key).name
    publication_manifest_path = output_root / Path(publication_manifest_key).name
    catalog_path = output_root / Path(catalog_key).name

    client.download_file(bucket=bucket, key=archive_key, local_path=archive_path)
    client.download_file(bucket=bucket, key=publication_manifest_key, local_path=publication_manifest_path)
    client.download_file(bucket=bucket, key=catalog_key, local_path=catalog_path)

    archive_check = _verify_archive(
        archive_path,
        expected_sha256=_required_manifest_value(retention_manifest, "archive_sha256"),
    )
    publication_manifest_check = _verify_publication_manifest(
        publication_manifest_path,
        expected_sha256=_required_manifest_value(retention_manifest, "publication_manifest_sha256"),
        environment=environment,
        release_version=release_version,
        expected_certification_status=(
            None
            if retention_manifest.get("certification_status") is None
            else str(retention_manifest["certification_status"])
        ),
    )
    catalog_check = _verify_catalog(catalog_path, environment=environment, release_version=release_version)

    failing_checks = [
        name
        for name, check in (
            ("archive", archive_check),
            ("publication_manifest", publication_manifest_check),
            ("catalog", catalog_check),
        )
        if check.get("status") != "passed"
    ]
    failure_reason = None
    if failing_checks:
        failure_reason = f"retained release evidence verification failed: {', '.join(failing_checks)}"

    report = ReleaseEvidenceRetrievalReport(
        status="passed" if not failing_checks else "failed",
        environment=environment,
        release_version=release_version,
        bucket=bucket,
        generated_at=generated_at or datetime.now(UTC).isoformat(),
        summary=(
            "retained release evidence verified successfully"
            if not failing_checks
            else failure_reason or "retained release evidence verification failed"
        ),
        failure_reason=failure_reason,
        retention_manifest_path=retention_manifest_path,
        archive_path=archive_path,
        publication_manifest_path=publication_manifest_path,
        catalog_path=catalog_path,
        archive_check=archive_check,
        publication_manifest_check=publication_manifest_check,
        catalog_check=catalog_check,
    )
    return report
