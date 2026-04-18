from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path


@dataclass(slots=True)
class RollbackVerificationReport:
    status: str
    environment: str | None
    current_release_version: str
    current_alembic_head: str
    target_release_version: str
    target_alembic_head: str
    rollback_mode: str
    generated_at: str
    summary: str
    failure_reason: str | None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def parse_release_version(value: str) -> tuple[tuple[int, ...], int, int]:
    normalized = value.strip()
    if not normalized:
        raise ValueError("release version is required")
    base_text, _, suffix = normalized.partition("-rc")
    base = tuple(int(part) for part in base_text.split("."))
    if suffix:
        return (base, 0, int(suffix))
    return (base, 1, 0)


def load_release_bundle_manifest(manifest_path: Path) -> dict[str, object]:
    if not manifest_path.exists():
        raise FileNotFoundError(f"release bundle manifest does not exist: {manifest_path}")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("release bundle manifest must be a JSON object")
    required_fields = ("release_version", "alembic_head", "bundle_name", "built_at")
    for field in required_fields:
        if not payload.get(field):
            raise ValueError(f"release bundle manifest missing required field: {field}")
    return payload


def summarize_rollback_verification_report(report: RollbackVerificationReport) -> str:
    if report.status == "passed":
        return "rollback target verified for app-only rollback"
    return report.failure_reason or "rollback verification failed"


def build_rollback_verification_report(
    *,
    environment: str | None,
    current_release_version: str,
    current_alembic_head: str,
    target_manifest: dict[str, object],
    generated_at: str,
) -> RollbackVerificationReport:
    target_release_version = str(target_manifest["release_version"])
    target_alembic_head = str(target_manifest["alembic_head"])
    failure_reason: str | None = None
    rollback_mode = "app_only"

    if target_release_version == current_release_version:
        failure_reason = "target bundle matches the currently deployed release"
    elif parse_release_version(target_release_version) > parse_release_version(current_release_version):
        failure_reason = "target bundle is newer than the currently deployed release"
    elif target_alembic_head != current_alembic_head:
        failure_reason = "target bundle schema head differs from deployed schema head"

    if failure_reason is not None:
        rollback_mode = "restore_required"

    report = RollbackVerificationReport(
        status="passed" if failure_reason is None else "failed",
        environment=environment,
        current_release_version=current_release_version,
        current_alembic_head=current_alembic_head,
        target_release_version=target_release_version,
        target_alembic_head=target_alembic_head,
        rollback_mode=rollback_mode,
        generated_at=generated_at,
        summary="",
        failure_reason=failure_reason,
    )
    report.summary = summarize_rollback_verification_report(report)
    return report


def write_rollback_verification_report(report: RollbackVerificationReport, *, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
