from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from store_control_plane.config import build_settings
from store_control_plane.ops.postgres_restore import run_postgres_restore


class RecordingRestoreObjectStorageClient:
    def __init__(self, *, manifest: dict[str, object], dump_bytes: bytes = b"pg-dump") -> None:
        self.downloads: list[dict[str, object]] = []
        self._manifest = manifest
        self._dump_bytes = dump_bytes

    def download_file(self, *, bucket: str, key: str, local_path: Path) -> None:
        local_path.parent.mkdir(parents=True, exist_ok=True)
        self.downloads.append({"bucket": bucket, "key": key, "local_path": local_path})
        if str(key).endswith(".json"):
            local_path.write_text(json.dumps(self._manifest), encoding="utf-8")
        else:
            local_path.write_bytes(self._dump_bytes)


def test_run_postgres_restore_downloads_artifacts_and_invokes_pg_restore(tmp_path: Path) -> None:
    settings = build_settings(
        deployment_environment="staging",
        object_storage_bucket="store-platform-staging",
    )
    storage = RecordingRestoreObjectStorageClient(
        manifest={
            "environment": "staging",
            "release_version": "2026.04.14-staging",
            "alembic_head": "20260414_0022_saas_billing_lifecycle",
        }
    )
    command_calls: list[list[str]] = []

    def runner(command: list[str]) -> None:
        command_calls.append(command)

    plan = run_postgres_restore(
        settings,
        dump_key="control-plane/staging/postgres-backups/20260414T103045Z/store-control-plane-staging-20260414T103045Z.dump",
        metadata_key="control-plane/staging/postgres-backups/20260414T103045Z/metadata.json",
        output_root=tmp_path,
        target_database_url="postgresql+asyncpg://store:secret@db.internal:5432/store_control_plane_staging",
        storage_client=storage,
        command_runner=runner,
    )

    assert [record["key"] for record in storage.downloads] == [
        "control-plane/staging/postgres-backups/20260414T103045Z/metadata.json",
        "control-plane/staging/postgres-backups/20260414T103045Z/store-control-plane-staging-20260414T103045Z.dump",
    ]
    assert command_calls == [
        [
            "pg_restore",
            "--clean",
            "--if-exists",
            "--no-owner",
            "--dbname",
            "postgresql://store:secret@db.internal:5432/store_control_plane_staging",
            str(plan.dump_path),
        ]
    ]
    assert plan.manifest["environment"] == "staging"
    assert plan.dump_path.read_bytes() == b"pg-dump"


def test_run_postgres_restore_rejects_environment_mismatch_without_override(tmp_path: Path) -> None:
    settings = build_settings(
        deployment_environment="staging",
        object_storage_bucket="store-platform-staging",
    )
    storage = RecordingRestoreObjectStorageClient(
        manifest={
            "environment": "prod",
            "release_version": "2026.04.14",
            "alembic_head": "20260414_0022_saas_billing_lifecycle",
        }
    )

    with pytest.raises(ValueError, match="environment mismatch"):
        run_postgres_restore(
            settings,
            dump_key="control-plane/prod/postgres-backups/20260414T103045Z/store-control-plane-prod-20260414T103045Z.dump",
            metadata_key="control-plane/prod/postgres-backups/20260414T103045Z/metadata.json",
            output_root=tmp_path,
            target_database_url="postgresql+asyncpg://store:secret@db.internal:5432/store_control_plane_restore",
            storage_client=storage,
        )
