from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable

from alembic.config import Config
from alembic.script import ScriptDirectory

from ..config import Settings
from .object_storage import ObjectStorageClientProtocol, build_object_storage_client


CommandRunner = Callable[[list[str]], None]


@dataclass(slots=True)
class BackupPlan:
    bucket: str
    dump_key: str
    metadata_key: str
    dump_path: Path
    metadata_path: Path
    manifest: dict[str, object]


def _default_command_runner(command: list[str]) -> None:
    subprocess.run(command, check=True)


def _serialize_timestamp(value: datetime) -> str:
    return value.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")


def _sync_database_url(database_url: str) -> str:
    return database_url.replace("+asyncpg", "", 1)


def resolve_alembic_head(*, service_root: Path | None = None) -> str:
    root = service_root or Path(__file__).resolve().parents[2]
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "alembic"))
    return ScriptDirectory.from_config(config).get_current_head() or "unknown"


def create_backup_plan(
    settings: Settings,
    *,
    output_root: Path,
    now: datetime,
    alembic_head: str,
) -> BackupPlan:
    if not settings.object_storage_bucket:
        raise ValueError("object storage bucket is required for Postgres backups")

    timestamp = _serialize_timestamp(now)
    dump_name = f"store-control-plane-{settings.deployment_environment}-{timestamp}.dump"
    backup_prefix = "/".join(
        segment
        for segment in (
            settings.object_storage_prefix,
            settings.backup_artifact_prefix,
            timestamp,
        )
        if segment
    )
    dump_key = f"{backup_prefix}/{dump_name}"
    metadata_key = f"{backup_prefix}/metadata.json"
    dump_path = output_root / dump_name
    metadata_path = output_root / "metadata.json"

    manifest: dict[str, object] = {
        "environment": settings.deployment_environment,
        "release_version": settings.release_version,
        "public_base_url": settings.public_base_url,
        "alembic_head": alembic_head,
        "created_at": now.astimezone(UTC).isoformat(),
        "bucket": settings.object_storage_bucket,
        "dump_key": dump_key,
        "metadata_key": metadata_key,
        "retention_days": settings.backup_retention_days,
    }
    return BackupPlan(
        bucket=settings.object_storage_bucket,
        dump_key=dump_key,
        metadata_key=metadata_key,
        dump_path=dump_path,
        metadata_path=metadata_path,
        manifest=manifest,
    )


def run_postgres_backup(
    settings: Settings,
    *,
    output_root: Path,
    alembic_head: str | None = None,
    now: datetime | None = None,
    storage_client: ObjectStorageClientProtocol | None = None,
    command_runner: CommandRunner | None = None,
    dry_run: bool = False,
    pg_dump_command: str = "pg_dump",
) -> BackupPlan:
    output_root.mkdir(parents=True, exist_ok=True)
    resolved_now = now or datetime.now(UTC)
    resolved_head = alembic_head or resolve_alembic_head()
    plan = create_backup_plan(
        settings,
        output_root=output_root,
        now=resolved_now,
        alembic_head=resolved_head,
    )
    plan.metadata_path.write_text(json.dumps(plan.manifest, indent=2), encoding="utf-8")

    if dry_run:
        return plan

    runner = command_runner or _default_command_runner
    runner(
        [
            pg_dump_command,
            "--format=custom",
            "--file",
            str(plan.dump_path),
            _sync_database_url(settings.database_url),
        ]
    )

    client = storage_client or build_object_storage_client(settings)
    metadata = {
        "environment": settings.deployment_environment,
        "release_version": settings.release_version,
        "alembic_head": str(plan.manifest["alembic_head"]),
    }
    client.upload_file(local_path=plan.dump_path, bucket=plan.bucket, key=plan.dump_key, metadata=metadata)
    client.upload_file(
        local_path=plan.metadata_path,
        bucket=plan.bucket,
        key=plan.metadata_key,
        metadata=metadata,
        content_type="application/json",
    )
    return plan
