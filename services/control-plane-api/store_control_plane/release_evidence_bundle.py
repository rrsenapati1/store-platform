from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil


def _slugify(label: str) -> str:
    return label.strip().lower().replace("_", "-")


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _reset_output_dir(output_dir: Path) -> None:
    if output_dir.exists():
        for child_name in ("reports", "artifacts"):
            child_path = output_dir / child_name
            if child_path.exists():
                shutil.rmtree(child_path)
        for file_name in ("bundle-manifest.json", "bundle-index.md"):
            file_path = output_dir / file_name
            if file_path.exists():
                file_path.unlink()
    output_dir.mkdir(parents=True, exist_ok=True)


def _copy_report(*, label: str, source_path: Path, output_dir: Path) -> dict[str, object]:
    destination = output_dir / "reports" / f"{_slugify(label)}{source_path.suffix or '.json'}"
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, destination)
    return {
        "status": "passed",
        "source_path": str(source_path),
        "bundle_path": destination.relative_to(output_dir).as_posix(),
        "size_bytes": destination.stat().st_size,
        "sha256": _hash_file(destination),
    }


def _hash_directory(root: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    file_count = 0
    for file_path in sorted(path for path in root.rglob("*") if path.is_file()):
        relative_path = file_path.relative_to(root).as_posix()
        digest.update(relative_path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(_hash_file(file_path).encode("utf-8"))
        digest.update(b"\0")
        file_count += 1
    return digest.hexdigest(), file_count


def _copy_directory(*, label: str, source_path: Path, output_dir: Path) -> dict[str, object]:
    destination = output_dir / "artifacts" / _slugify(label)
    shutil.copytree(source_path, destination, dirs_exist_ok=True)
    sha256, file_count = _hash_directory(destination)
    return {
        "status": "passed",
        "source_path": str(source_path),
        "bundle_path": destination.relative_to(output_dir).as_posix(),
        "file_count": file_count,
        "sha256": sha256,
    }


def _summarize_bundle(*, failing_entries: list[str], report_count: int, directory_count: int) -> str:
    if failing_entries:
        return f"{len(failing_entries)} bundle entries failed: {', '.join(failing_entries)}"
    return f"{report_count} reports and {directory_count} artifact directories bundled"


def _render_bundle_index(
    *,
    generated_at: str,
    reports: dict[str, dict[str, object]],
    directories: dict[str, dict[str, object]],
    summary: str,
) -> str:
    lines = [
        "# Release Evidence Bundle",
        "",
        f"- Generated: {generated_at}",
        f"- Summary: {summary}",
        "",
        "## Reports",
        "",
    ]
    for label, entry in reports.items():
        lines.append(
            f"- `{label}`: {entry.get('status')} -> {entry.get('bundle_path') or 'not-copied'}"
        )
    lines.extend(["", "## Artifact Directories", ""])
    for label, entry in directories.items():
        lines.append(
            f"- `{label}`: {entry.get('status')} -> {entry.get('bundle_path') or 'not-copied'}"
        )
    lines.append("")
    return "\n".join(lines)


def build_release_evidence_bundle(
    *,
    output_dir: Path,
    report_paths: dict[str, Path | None],
    directory_paths: dict[str, Path | None] | None = None,
    generated_at: str | None = None,
) -> dict[str, object]:
    effective_generated_at = generated_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    _reset_output_dir(output_dir)

    reports: dict[str, dict[str, object]] = {}
    directories: dict[str, dict[str, object]] = {}
    failing_entries: list[str] = []

    for label, source_path in report_paths.items():
        if source_path is None:
            continue
        if not source_path.exists() or not source_path.is_file():
            reports[label] = {
                "status": "missing",
                "source_path": str(source_path),
                "bundle_path": None,
                "size_bytes": 0,
                "sha256": None,
            }
            failing_entries.append(label)
            continue
        reports[label] = _copy_report(label=label, source_path=source_path, output_dir=output_dir)

    for label, source_path in (directory_paths or {}).items():
        if source_path is None:
            continue
        if not source_path.exists() or not source_path.is_dir():
            directories[label] = {
                "status": "missing",
                "source_path": str(source_path),
                "bundle_path": None,
                "file_count": 0,
                "sha256": None,
            }
            failing_entries.append(label)
            continue
        directories[label] = _copy_directory(label=label, source_path=source_path, output_dir=output_dir)

    summary = _summarize_bundle(
        failing_entries=failing_entries,
        report_count=len(reports),
        directory_count=len(directories),
    )
    manifest = {
        "status": "passed" if not failing_entries else "failed",
        "generated_at": effective_generated_at,
        "reports": reports,
        "directories": directories,
        "failing_entries": failing_entries,
        "summary": summary,
    }
    manifest_path = output_dir / "bundle-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    index_path = output_dir / "bundle-index.md"
    index_path.write_text(
        _render_bundle_index(
            generated_at=effective_generated_at,
            reports=reports,
            directories=directories,
            summary=summary,
        ),
        encoding="utf-8",
    )

    return {
        "status": manifest["status"],
        "output_dir": str(output_dir),
        "manifest_path": str(manifest_path),
        "index_path": str(index_path),
        "reports": reports,
        "directories": directories,
        "failing_entries": failing_entries,
        "summary": summary,
    }
