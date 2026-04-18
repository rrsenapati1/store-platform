from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
from typing import Callable


SERVICE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
SBOM_TOOL = "syft"
SBOM_FORMAT = "cyclonedx-json"

SbomExecutor = Callable[[list[str], Path], subprocess.CompletedProcess[str]]

DEFAULT_SBOM_SURFACES: dict[str, str] = {
    "control_plane_api": f"dir:{(REPO_ROOT / 'services' / 'control-plane-api').as_posix()}",
    "platform_admin": f"dir:{(REPO_ROOT / 'apps' / 'platform-admin').as_posix()}",
    "owner_web": f"dir:{(REPO_ROOT / 'apps' / 'owner-web').as_posix()}",
    "store_desktop": f"dir:{(REPO_ROOT / 'apps' / 'store-desktop').as_posix()}",
    "store_mobile": f"dir:{(REPO_ROOT / 'apps' / 'store-mobile').as_posix()}",
    "store_desktop_tauri": f"dir:{(REPO_ROOT / 'apps' / 'store-desktop' / 'src-tauri').as_posix()}",
}


def _default_scan_executor(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )


def _sanitize_surface_name(surface_name: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", surface_name.strip().lower())
    return normalized.strip("_") or "surface"


def _write_artifact(raw_output_dir: Path | None, surface_name: str, content: str) -> Path | None:
    if raw_output_dir is None:
        return None
    raw_output_dir.mkdir(parents=True, exist_ok=True)
    destination = raw_output_dir / f"{_sanitize_surface_name(surface_name)}.cdx.json"
    destination.write_text(content, encoding="utf-8")
    return destination


def _normalize_surface_result(
    *,
    tool: str,
    status: str,
    command: list[str],
    format_name: str,
    component_count: int,
    artifact_path: Path | None,
    failure_reason: str | None = None,
) -> dict[str, object]:
    return {
        "tool": tool,
        "status": status,
        "command": " ".join(command),
        "format": format_name,
        "component_count": component_count,
        "artifact_path": None if artifact_path is None else str(artifact_path),
        "failure_reason": failure_reason,
    }


def build_sbom_report(
    *,
    generated_at: str,
    surface_results: dict[str, dict[str, object]],
) -> dict[str, object]:
    normalized_surfaces: dict[str, dict[str, object]] = {}
    failing_surfaces: list[str] = []

    for surface_name, raw_result in surface_results.items():
        normalized_result = {
            "tool": str(raw_result.get("tool") or SBOM_TOOL),
            "status": str(raw_result.get("status") or "failed"),
            "command": str(raw_result.get("command") or ""),
            "format": str(raw_result.get("format") or SBOM_FORMAT),
            "component_count": int(raw_result.get("component_count") or 0),
            "artifact_path": None if raw_result.get("artifact_path") is None else str(raw_result.get("artifact_path")),
            "failure_reason": None if raw_result.get("failure_reason") is None else str(raw_result.get("failure_reason")),
        }
        normalized_surfaces[surface_name] = normalized_result
        if normalized_result["status"] != "passed":
            failing_surfaces.append(surface_name)

    summary = (
        f"{len(normalized_surfaces)} surfaces passed"
        if not failing_surfaces
        else f"{len(failing_surfaces)} surfaces failed: {', '.join(failing_surfaces)}"
    )
    return {
        "status": "passed" if not failing_surfaces else "failed",
        "generated_at": generated_at,
        "format": SBOM_FORMAT,
        "surfaces": normalized_surfaces,
        "failing_surfaces": failing_surfaces,
        "summary": summary,
    }


def write_sbom_report(report: dict[str, object], *, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")


def summarize_sbom_report(report: dict[str, object]) -> str:
    return str(report.get("summary") or "")


def _count_components(payload: dict[str, object]) -> int:
    return len(list(payload.get("components") or []))


def _scan_surface(
    *,
    surface_name: str,
    target: str,
    raw_output_dir: Path | None,
    scan_executor: SbomExecutor,
) -> dict[str, object]:
    command = [SBOM_TOOL, target, "-o", SBOM_FORMAT]
    try:
        completed = scan_executor(command, REPO_ROOT)
    except FileNotFoundError:
        return _normalize_surface_result(
            tool=SBOM_TOOL,
            status="tool-unavailable",
            command=command,
            format_name=SBOM_FORMAT,
            component_count=0,
            artifact_path=None,
            failure_reason=f"{SBOM_TOOL} executable unavailable",
        )

    output_text = completed.stdout or completed.stderr or ""
    artifact_path = _write_artifact(raw_output_dir, surface_name, output_text) if output_text else None
    if completed.returncode != 0:
        return _normalize_surface_result(
            tool=SBOM_TOOL,
            status="failed",
            command=command,
            format_name=SBOM_FORMAT,
            component_count=0,
            artifact_path=artifact_path,
            failure_reason=f"{SBOM_TOOL} exited with code {completed.returncode}",
        )

    try:
        payload = json.loads(output_text) if output_text.strip() else {}
    except json.JSONDecodeError:
        return _normalize_surface_result(
            tool=SBOM_TOOL,
            status="failed",
            command=command,
            format_name=SBOM_FORMAT,
            component_count=0,
            artifact_path=artifact_path,
            failure_reason=f"{SBOM_TOOL} produced invalid JSON",
        )

    return _normalize_surface_result(
        tool=SBOM_TOOL,
        status="passed",
        command=command,
        format_name=SBOM_FORMAT,
        component_count=_count_components(payload),
        artifact_path=artifact_path,
    )


def generate_sbom_bundle(
    *,
    output_path: Path,
    raw_output_dir: Path | None = None,
    image_refs: list[str] | None = None,
    scan_executor: SbomExecutor | None = None,
) -> dict[str, object]:
    effective_raw_output_dir = raw_output_dir or output_path.with_name(f"{output_path.stem}-artifacts")
    executor = scan_executor or _default_scan_executor
    surface_results: dict[str, dict[str, object]] = {}

    for surface_name, target in DEFAULT_SBOM_SURFACES.items():
        surface_results[surface_name] = _scan_surface(
            surface_name=surface_name,
            target=target,
            raw_output_dir=effective_raw_output_dir,
            scan_executor=executor,
        )

    for image_ref in image_refs or []:
        surface_name = f"image_{_sanitize_surface_name(image_ref)}"
        surface_results[surface_name] = _scan_surface(
            surface_name=surface_name,
            target=image_ref,
            raw_output_dir=effective_raw_output_dir,
            scan_executor=executor,
        )

    report = build_sbom_report(
        generated_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        surface_results=surface_results,
    )
    write_sbom_report(report, output_path=output_path)
    report["output_path"] = str(output_path)
    report["raw_output_dir"] = str(effective_raw_output_dir)
    return report
