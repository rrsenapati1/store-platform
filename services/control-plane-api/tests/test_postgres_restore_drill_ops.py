from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from store_control_plane.config import build_settings
from store_control_plane.ops.postgres_restore import RestorePlan
from store_control_plane.ops.postgres_restore_drill import (
    run_postgres_restore_drill,
    write_restore_drill_report,
)


def _build_restore_plan(tmp_path: Path) -> RestorePlan:
    dump_path = tmp_path / "store-control-plane-staging.dump"
    metadata_path = tmp_path / "metadata.json"
    dump_path.write_bytes(b"dump")
    metadata_path.write_text(
        json.dumps(
            {
                "environment": "staging",
                "release_version": "2026.04.18-rc1",
                "alembic_head": "20260418_0044_restore_drill_foundation",
            }
        ),
        encoding="utf-8",
    )
    return RestorePlan(
        bucket="store-platform-staging",
        dump_key="control-plane/staging/postgres-backups/20260418T023000Z/store-control-plane-staging.dump",
        metadata_key="control-plane/staging/postgres-backups/20260418T023000Z/metadata.json",
        dump_path=dump_path,
        metadata_path=metadata_path,
        target_database_url="postgresql://store:secret@db.internal:5432/store_control_plane_restore",
        manifest={
            "environment": "staging",
            "release_version": "2026.04.18-rc1",
            "alembic_head": "20260418_0044_restore_drill_foundation",
        },
    )


def test_run_postgres_restore_drill_reports_success_and_skipped_smoke(tmp_path: Path) -> None:
    settings = build_settings(
        deployment_environment="staging",
        object_storage_bucket="store-platform-staging",
    )
    restore_plan = _build_restore_plan(tmp_path)

    def fake_restore_runner(**_: object) -> RestorePlan:
        return restore_plan

    def fake_health_verifier(*, database_url: str) -> dict[str, object]:
        assert database_url == "postgresql://store:secret@db.internal:5432/store_control_plane_restore"
        return {
            "status": "ok",
            "environment": "staging",
            "release_version": "2026.04.18-rc1",
        }

    report = run_postgres_restore_drill(
        settings,
        dump_key=restore_plan.dump_key,
        metadata_key=restore_plan.metadata_key,
        output_root=tmp_path,
        target_database_url="postgresql+asyncpg://store:secret@db.internal:5432/store_control_plane_restore",
        restore_runner=fake_restore_runner,
        health_verifier=fake_health_verifier,
        now_provider=lambda: datetime(2026, 4, 18, 3, 0, 0, tzinfo=UTC),
    )

    payload = report.to_dict()
    assert payload["status"] == "passed"
    assert payload["source"] == {
        "bucket": "store-platform-staging",
        "dump_key": restore_plan.dump_key,
        "metadata_key": restore_plan.metadata_key,
    }
    assert payload["restored_manifest"] == restore_plan.manifest
    assert payload["health_result"]["status"] == "passed"
    assert payload["verification_result"]["status"] == "skipped"
    assert payload["failure_reason"] is None


def test_run_postgres_restore_drill_reports_restore_failure(tmp_path: Path) -> None:
    settings = build_settings(
        deployment_environment="staging",
        object_storage_bucket="store-platform-staging",
    )

    def fake_restore_runner(**_: object) -> RestorePlan:
        raise ValueError("restore metadata environment mismatch")

    report = run_postgres_restore_drill(
        settings,
        dump_key="control-plane/prod/postgres-backups/metadata.dump",
        metadata_key="control-plane/prod/postgres-backups/metadata.json",
        output_root=tmp_path,
        target_database_url="postgresql+asyncpg://store:secret@db.internal:5432/store_control_plane_restore",
        restore_runner=fake_restore_runner,
        now_provider=lambda: datetime(2026, 4, 18, 3, 0, 0, tzinfo=UTC),
    )

    payload = report.to_dict()
    assert payload["status"] == "failed"
    assert payload["health_result"]["status"] == "skipped"
    assert payload["failure_reason"] == "restore metadata environment mismatch"


def test_run_postgres_restore_drill_reports_health_failure(tmp_path: Path) -> None:
    settings = build_settings(
        deployment_environment="staging",
        object_storage_bucket="store-platform-staging",
    )
    restore_plan = _build_restore_plan(tmp_path)

    def fake_restore_runner(**_: object) -> RestorePlan:
        return restore_plan

    def fake_health_verifier(*, database_url: str) -> dict[str, object]:
        assert database_url == "postgresql://store:secret@db.internal:5432/store_control_plane_restore"
        return {"status": "degraded", "database": {"status": "ok"}}

    report = run_postgres_restore_drill(
        settings,
        dump_key=restore_plan.dump_key,
        metadata_key=restore_plan.metadata_key,
        output_root=tmp_path,
        target_database_url="postgresql+asyncpg://store:secret@db.internal:5432/store_control_plane_restore",
        restore_runner=fake_restore_runner,
        health_verifier=fake_health_verifier,
        now_provider=lambda: datetime(2026, 4, 18, 3, 0, 0, tzinfo=UTC),
    )

    payload = report.to_dict()
    assert payload["status"] == "failed"
    assert payload["health_result"]["status"] == "failed"
    assert payload["failure_reason"] == "post-restore health verification failed"


def test_run_postgres_restore_drill_reports_smoke_failure(tmp_path: Path) -> None:
    settings = build_settings(
        deployment_environment="staging",
        object_storage_bucket="store-platform-staging",
    )
    restore_plan = _build_restore_plan(tmp_path)

    def fake_restore_runner(**_: object) -> RestorePlan:
        return restore_plan

    def fake_health_verifier(*, database_url: str) -> dict[str, object]:
        assert database_url == "postgresql://store:secret@db.internal:5432/store_control_plane_restore"
        return {"status": "ok"}

    def fake_smoke_verifier(*, database_url: str) -> dict[str, object]:
        assert database_url == "postgresql://store:secret@db.internal:5432/store_control_plane_restore"
        return {"status": "failed", "summary": "owner auth failed"}

    report = run_postgres_restore_drill(
        settings,
        dump_key=restore_plan.dump_key,
        metadata_key=restore_plan.metadata_key,
        output_root=tmp_path,
        target_database_url="postgresql+asyncpg://store:secret@db.internal:5432/store_control_plane_restore",
        verify_smoke=True,
        restore_runner=fake_restore_runner,
        health_verifier=fake_health_verifier,
        smoke_verifier=fake_smoke_verifier,
        now_provider=lambda: datetime(2026, 4, 18, 3, 0, 0, tzinfo=UTC),
    )

    payload = report.to_dict()
    assert payload["status"] == "failed"
    assert payload["verification_result"]["status"] == "failed"
    assert payload["failure_reason"] == "post-restore smoke verification failed"


def test_write_restore_drill_report_writes_expected_json(tmp_path: Path) -> None:
    settings = build_settings(
        deployment_environment="staging",
        object_storage_bucket="store-platform-staging",
    )
    restore_plan = _build_restore_plan(tmp_path)

    def fake_restore_runner(**_: object) -> RestorePlan:
        return restore_plan

    def fake_health_verifier(*, database_url: str) -> dict[str, object]:
        assert database_url == "postgresql://store:secret@db.internal:5432/store_control_plane_restore"
        return {"status": "ok"}

    report = run_postgres_restore_drill(
        settings,
        dump_key=restore_plan.dump_key,
        metadata_key=restore_plan.metadata_key,
        output_root=tmp_path,
        target_database_url="postgresql+asyncpg://store:secret@db.internal:5432/store_control_plane_restore",
        restore_runner=fake_restore_runner,
        health_verifier=fake_health_verifier,
        now_provider=lambda: datetime(2026, 4, 18, 3, 0, 0, tzinfo=UTC),
    )

    output_path = tmp_path / "reports" / "restore-drill.json"
    write_restore_drill_report(report, output_path)

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["status"] == "passed"
    assert payload["source"]["dump_key"] == restore_plan.dump_key
    assert payload["restored_manifest"]["release_version"] == "2026.04.18-rc1"

