from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from store_control_plane.config import build_settings
from store_control_plane.ops.postgres_backup import create_backup_plan, run_postgres_backup


class RecordingObjectStorageClient:
    def __init__(self) -> None:
        self.uploads: list[dict[str, object]] = []

    def upload_file(
        self,
        *,
        local_path: Path,
        bucket: str,
        key: str,
        metadata: dict[str, str] | None = None,
        content_type: str | None = None,
    ) -> None:
        self.uploads.append(
            {
                "local_path": local_path,
                "bucket": bucket,
                "key": key,
                "metadata": metadata,
                "content_type": content_type,
            }
        )


def test_create_backup_plan_uses_environment_prefix_and_metadata(tmp_path: Path) -> None:
    settings = build_settings(
        deployment_environment="staging",
        release_version="2026.04.14-staging",
        object_storage_bucket="store-platform-staging",
        object_storage_prefix="control-plane/staging",
    )

    plan = create_backup_plan(
        settings,
        output_root=tmp_path,
        now=datetime(2026, 4, 14, 10, 30, 45, tzinfo=UTC),
        alembic_head="20260414_0022_saas_billing_lifecycle",
    )

    assert plan.bucket == "store-platform-staging"
    assert plan.dump_key == (
        "control-plane/staging/postgres-backups/20260414T103045Z/"
        "store-control-plane-staging-20260414T103045Z.dump"
    )
    assert plan.metadata_key == (
        "control-plane/staging/postgres-backups/20260414T103045Z/metadata.json"
    )
    assert plan.manifest["environment"] == "staging"
    assert plan.manifest["release_version"] == "2026.04.14-staging"
    assert plan.manifest["alembic_head"] == "20260414_0022_saas_billing_lifecycle"
    assert plan.dump_path.name == "store-control-plane-staging-20260414T103045Z.dump"


def test_run_postgres_backup_invokes_pg_dump_and_uploads_dump_and_metadata(tmp_path: Path) -> None:
    settings = build_settings(
        database_url="postgresql+asyncpg://store:secret@db.internal:5432/store_control_plane_staging",
        deployment_environment="staging",
        release_version="2026.04.14-staging",
        object_storage_bucket="store-platform-staging",
        object_storage_prefix="control-plane/staging",
    )
    storage = RecordingObjectStorageClient()
    command_calls: list[list[str]] = []

    def runner(command: list[str]) -> None:
        command_calls.append(command)
        output_path = Path(command[command.index("--file") + 1])
        output_path.write_bytes(b"pg-dump")

    plan = run_postgres_backup(
        settings,
        output_root=tmp_path,
        now=datetime(2026, 4, 14, 10, 30, 45, tzinfo=UTC),
        alembic_head="20260414_0022_saas_billing_lifecycle",
        storage_client=storage,
        command_runner=runner,
    )

    assert command_calls == [
        [
            "pg_dump",
            "--format=custom",
            "--file",
            str(plan.dump_path),
            "postgresql://store:secret@db.internal:5432/store_control_plane_staging",
        ]
    ]
    assert len(storage.uploads) == 2
    dump_upload = storage.uploads[0]
    metadata_upload = storage.uploads[1]
    assert dump_upload["bucket"] == "store-platform-staging"
    assert dump_upload["key"] == plan.dump_key
    assert metadata_upload["key"] == plan.metadata_key
    metadata_payload = json.loads(plan.metadata_path.read_text(encoding="utf-8"))
    assert metadata_payload["environment"] == "staging"
    assert metadata_payload["release_version"] == "2026.04.14-staging"
