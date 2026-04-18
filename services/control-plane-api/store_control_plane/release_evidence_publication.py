from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import tarfile


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_bundle_manifest(bundle_dir: Path) -> dict[str, object]:
    manifest_path = bundle_dir / "bundle-manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"missing bundle manifest: {manifest_path}")
    return _load_json(manifest_path)


def _read_certification_status(bundle_dir: Path, bundle_manifest: dict[str, object]) -> str | None:
    return _read_report_status(bundle_dir, bundle_manifest, label="certification_report")


def _read_report_status(bundle_dir: Path, bundle_manifest: dict[str, object], *, label: str) -> str | None:
    reports = dict(bundle_manifest.get("reports") or {})
    report = dict(reports.get(label) or {})
    bundle_path = report.get("bundle_path")
    if not bundle_path:
        return None
    report_path = bundle_dir / str(bundle_path)
    if not report_path.exists():
        return None
    report_payload = _load_json(report_path)
    raw_status = report_payload.get("status")
    return None if raw_status is None else str(raw_status)


def _catalog_sort_key(entry: dict[str, object]) -> tuple[str, str]:
    return (str(entry.get("published_at") or ""), str(entry.get("release_version") or ""))


def _update_catalog(
    *,
    catalog_path: Path,
    publication_entry: dict[str, object],
    generated_at: str,
) -> dict[str, object]:
    if catalog_path.exists():
        catalog = _load_json(catalog_path)
    else:
        catalog = {"generated_at": generated_at, "publications": []}

    existing = [
        entry
        for entry in list(catalog.get("publications") or [])
        if not (
            entry.get("environment") == publication_entry.get("environment")
            and entry.get("release_version") == publication_entry.get("release_version")
        )
    ]
    existing.append(publication_entry)
    existing.sort(key=_catalog_sort_key, reverse=True)
    catalog["generated_at"] = generated_at
    catalog["publications"] = existing
    catalog_path.write_text(json.dumps(catalog, indent=2), encoding="utf-8")
    return catalog


def _archive_bundle(*, bundle_dir: Path, archive_path: Path, root_name: str) -> None:
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive_path, "w:gz") as archive:
        for file_path in sorted(path for path in bundle_dir.rglob("*") if path.is_file()):
            relative_path = file_path.relative_to(bundle_dir).as_posix()
            tar_info = archive.gettarinfo(str(file_path), arcname=f"{root_name}/{relative_path}")
            tar_info.uid = 0
            tar_info.gid = 0
            tar_info.uname = ""
            tar_info.gname = ""
            tar_info.mtime = 0
            with file_path.open("rb") as handle:
                archive.addfile(tar_info, handle)


def publish_release_evidence_bundle(
    *,
    bundle_dir: Path,
    output_dir: Path,
    release_version: str,
    environment: str,
    published_at: str | None = None,
) -> dict[str, object]:
    effective_published_at = published_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    if not bundle_dir.exists() or not bundle_dir.is_dir():
        return {
            "status": "failed",
            "summary": f"bundle directory missing: {bundle_dir}",
            "bundle_dir": str(bundle_dir),
        }

    bundle_manifest = _read_bundle_manifest(bundle_dir)
    certification_status = _read_certification_status(bundle_dir, bundle_manifest)
    launch_readiness_status = _read_report_status(bundle_dir, bundle_manifest, label="launch_readiness_report")
    output_dir.mkdir(parents=True, exist_ok=True)

    publication_base_name = f"store-release-evidence-{environment}-{release_version}"
    archive_path = output_dir / f"{publication_base_name}.tar.gz"
    _archive_bundle(bundle_dir=bundle_dir, archive_path=archive_path, root_name=publication_base_name)

    bundle_manifest_path = bundle_dir / "bundle-manifest.json"
    publication_manifest_path = output_dir / f"{environment}-{release_version}.publication.json"
    publication_manifest = {
        "status": "published",
        "environment": environment,
        "release_version": release_version,
        "published_at": effective_published_at,
        "bundle_dir": str(bundle_dir),
        "bundle_manifest_path": str(bundle_manifest_path),
        "bundle_manifest_sha256": _hash_file(bundle_manifest_path),
        "bundle_status": bundle_manifest.get("status"),
        "certification_status": certification_status,
        "launch_readiness_status": launch_readiness_status,
        "archive_path": str(archive_path),
        "archive_sha256": _hash_file(archive_path),
        "archive_size_bytes": archive_path.stat().st_size,
    }
    publication_manifest_path.write_text(json.dumps(publication_manifest, indent=2), encoding="utf-8")

    catalog_path = output_dir / "release-evidence-catalog.json"
    catalog = _update_catalog(
        catalog_path=catalog_path,
        publication_entry={
            "environment": environment,
            "release_version": release_version,
            "published_at": effective_published_at,
            "status": publication_manifest["status"],
            "certification_status": certification_status,
            "launch_readiness_status": launch_readiness_status,
            "archive_path": str(archive_path),
            "publication_manifest_path": str(publication_manifest_path),
        },
        generated_at=effective_published_at,
    )

    return {
        "status": "published",
        "archive_path": str(archive_path),
        "publication_manifest_path": str(publication_manifest_path),
        "catalog_path": str(catalog_path),
        "catalog": catalog,
        "summary": f"published release evidence for {environment} {release_version}",
    }
