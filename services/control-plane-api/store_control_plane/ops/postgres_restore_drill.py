from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlsplit, urlunsplit

from fastapi.testclient import TestClient

from ..config import Settings
from ..main import create_app
from ..verification import run_control_plane_smoke
from .postgres_restore import RestorePlan, run_postgres_restore


RestoreRunner = Callable[..., RestorePlan]
HealthVerifier = Callable[..., dict[str, object]]
SmokeVerifier = Callable[..., dict[str, object]]
NowProvider = Callable[[], datetime]


@dataclass(slots=True)
class RestoreDrillCheckResult:
    status: str
    payload: dict[str, object] | None = None
    summary: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "payload": self.payload,
            "summary": self.summary,
        }


@dataclass(slots=True)
class RestoreDrillReport:
    status: str
    started_at: datetime
    finished_at: datetime
    duration_seconds: float
    source: dict[str, object]
    target: dict[str, object]
    restored_manifest: dict[str, object] | None
    health_result: RestoreDrillCheckResult
    verification_result: RestoreDrillCheckResult
    failure_reason: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "duration_seconds": self.duration_seconds,
            "source": self.source,
            "target": self.target,
            "restored_manifest": self.restored_manifest,
            "health_result": self.health_result.to_dict(),
            "verification_result": self.verification_result.to_dict(),
            "failure_reason": self.failure_reason,
        }


def _default_now_provider() -> datetime:
    return datetime.now(UTC)


def _redact_database_url(database_url: str) -> str:
    parts = urlsplit(database_url)
    username = parts.username or ""
    hostname = parts.hostname or ""
    port = f":{parts.port}" if parts.port else ""
    if username:
        netloc = f"{username}:***@{hostname}{port}"
    else:
        netloc = f"{hostname}{port}"
    return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))


def _default_health_verifier(*, database_url: str) -> dict[str, object]:
    with TestClient(
        create_app(
            database_url=database_url,
            bootstrap_database=False,
            korsenex_idp_mode="stub",
            compliance_irp_mode="stub",
            compliance_secret_key="restore-drill-health-check",
        )
    ) as client:
        response = client.get("/v1/system/health")
        response.raise_for_status()
        return response.json()


def _default_smoke_verifier(*, database_url: str) -> dict[str, object]:
    result = run_control_plane_smoke(database_url=database_url)
    return {
        "status": "passed",
        "payload": result.to_dict(),
        "summary": "control-plane smoke passed",
    }


def write_restore_drill_report(report: RestoreDrillReport, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    return output_path


def run_postgres_restore_drill(
    settings: Settings,
    *,
    dump_key: str,
    metadata_key: str,
    output_root: Path,
    target_database_url: str,
    verify_smoke: bool = False,
    allow_environment_mismatch: bool = False,
    restore_runner: RestoreRunner | None = None,
    health_verifier: HealthVerifier | None = None,
    smoke_verifier: SmokeVerifier | None = None,
    now_provider: NowProvider | None = None,
) -> RestoreDrillReport:
    restore = restore_runner or run_postgres_restore
    verify_health = health_verifier or _default_health_verifier
    verify_smoke_fn = smoke_verifier or _default_smoke_verifier
    now = now_provider or _default_now_provider

    started_at = now()
    source = {
        "bucket": settings.object_storage_bucket,
        "dump_key": dump_key,
        "metadata_key": metadata_key,
    }
    target = {"target_database_url": _redact_database_url(target_database_url.replace("+asyncpg", "", 1))}
    restored_manifest: dict[str, object] | None = None
    health_result = RestoreDrillCheckResult(status="skipped", summary="not-run")
    verification_result = RestoreDrillCheckResult(status="skipped", summary="not-run")
    failure_reason: str | None = None
    status = "failed"

    try:
        restore_plan = restore(
            settings=settings,
            dump_key=dump_key,
            metadata_key=metadata_key,
            output_root=output_root,
            target_database_url=target_database_url,
            allow_environment_mismatch=allow_environment_mismatch,
        )
        restored_manifest = restore_plan.manifest
        target = {"target_database_url": _redact_database_url(restore_plan.target_database_url)}
    except Exception as exc:  # pragma: no cover - exercised by tests
        failure_reason = str(exc)
        finished_at = now()
        return RestoreDrillReport(
            status=status,
            started_at=started_at,
            finished_at=finished_at,
            duration_seconds=max((finished_at - started_at).total_seconds(), 0.0),
            source=source,
            target=target,
            restored_manifest=restored_manifest,
            health_result=health_result,
            verification_result=verification_result,
            failure_reason=failure_reason,
        )

    try:
        health_payload = verify_health(database_url=restore_plan.target_database_url)
    except Exception as exc:
        health_result = RestoreDrillCheckResult(status="failed", summary=str(exc))
        failure_reason = "post-restore health verification failed"
    else:
        if str(health_payload.get("status") or "").lower() == "ok":
            health_result = RestoreDrillCheckResult(status="passed", payload=health_payload)
        else:
            health_result = RestoreDrillCheckResult(status="failed", payload=health_payload)
            failure_reason = "post-restore health verification failed"

    if failure_reason is None and verify_smoke:
        try:
            smoke_payload = verify_smoke_fn(database_url=restore_plan.target_database_url)
        except Exception as exc:
            verification_result = RestoreDrillCheckResult(status="failed", summary=str(exc))
            failure_reason = "post-restore smoke verification failed"
        else:
            smoke_status = str(smoke_payload.get("status") or "").lower()
            if smoke_status in {"passed", "ok"}:
                verification_result = RestoreDrillCheckResult(status="passed", payload=smoke_payload)
            else:
                verification_result = RestoreDrillCheckResult(status="failed", payload=smoke_payload)
                failure_reason = "post-restore smoke verification failed"

    finished_at = now()
    if failure_reason is None:
        status = "passed"
    return RestoreDrillReport(
        status=status,
        started_at=started_at,
        finished_at=finished_at,
        duration_seconds=max((finished_at - started_at).total_seconds(), 0.0),
        source=source,
        target=target,
        restored_manifest=restored_manifest,
        health_result=health_result,
        verification_result=verification_result,
        failure_reason=failure_reason,
    )

