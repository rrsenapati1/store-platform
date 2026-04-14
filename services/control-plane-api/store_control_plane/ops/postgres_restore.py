from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from ..config import Settings
from .object_storage import ObjectStorageClientProtocol, build_object_storage_client


CommandRunner = Callable[[list[str]], None]


@dataclass(slots=True)
class RestorePlan:
    bucket: str
    dump_key: str
    metadata_key: str
    dump_path: Path
    metadata_path: Path
    target_database_url: str
    manifest: dict[str, object]


def _default_command_runner(command: list[str]) -> None:
    subprocess.run(command, check=True)


def _sync_database_url(database_url: str) -> str:
    return database_url.replace("+asyncpg", "", 1)


def run_postgres_restore(
    settings: Settings,
    *,
    dump_key: str,
    metadata_key: str,
    output_root: Path,
    target_database_url: str,
    storage_client: ObjectStorageClientProtocol | None = None,
    command_runner: CommandRunner | None = None,
    dry_run: bool = False,
    pg_restore_command: str = "pg_restore",
    allow_environment_mismatch: bool = False,
) -> RestorePlan:
    bucket = settings.object_storage_bucket
    if not bucket:
        raise ValueError("object storage bucket is required for Postgres restore")

    output_root.mkdir(parents=True, exist_ok=True)
    metadata_path = output_root / Path(metadata_key).name
    dump_path = output_root / Path(dump_key).name

    client = storage_client or build_object_storage_client(settings)
    client.download_file(bucket=bucket, key=metadata_key, local_path=metadata_path)
    manifest = json.loads(metadata_path.read_text(encoding="utf-8"))
    manifest_environment = str(manifest.get("environment") or "").strip().lower()
    if (
        manifest_environment
        and manifest_environment != settings.deployment_environment
        and not allow_environment_mismatch
    ):
        raise ValueError("restore metadata environment mismatch")

    client.download_file(bucket=bucket, key=dump_key, local_path=dump_path)
    plan = RestorePlan(
        bucket=bucket,
        dump_key=dump_key,
        metadata_key=metadata_key,
        dump_path=dump_path,
        metadata_path=metadata_path,
        target_database_url=_sync_database_url(target_database_url),
        manifest=manifest,
    )
    if dry_run:
        return plan

    runner = command_runner or _default_command_runner
    runner(
        [
            pg_restore_command,
            "--clean",
            "--if-exists",
            "--no-owner",
            "--dbname",
            plan.target_database_url,
            str(plan.dump_path),
        ]
    )
    return plan
