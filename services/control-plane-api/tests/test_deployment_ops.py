from __future__ import annotations

from pathlib import Path

import pytest

from store_control_plane.config import build_settings
from store_control_plane.ops.deployment import execute_release_deployment


def test_execute_release_deployment_runs_backup_before_migration_and_restarts_services(tmp_path: Path) -> None:
    settings = build_settings(deployment_environment="staging")
    release_bundle_path = tmp_path / "release.tar.gz"
    release_bundle_path.write_text("release", encoding="utf-8")
    steps: list[str] = []
    commands: list[list[str]] = []

    def backup_executor() -> None:
        steps.append("backup")

    def runner(command: list[str]) -> None:
        commands.append(command)
        steps.append("command")

    plan = execute_release_deployment(
        settings,
        release_bundle_path=release_bundle_path,
        backup_executor=backup_executor,
        command_runner=runner,
    )

    assert steps == ["backup", "command", "command", "command"]
    assert commands == [
        ["python", "-m", "alembic", "-c", "alembic.ini", "upgrade", "head"],
        ["systemctl", "restart", "store-control-plane-api"],
        ["systemctl", "restart", "store-control-plane-worker"],
    ]
    assert plan.release_bundle_path == release_bundle_path


def test_execute_release_deployment_stops_before_restart_when_migration_fails(tmp_path: Path) -> None:
    settings = build_settings(deployment_environment="prod")
    release_bundle_path = tmp_path / "release.tar.gz"
    release_bundle_path.write_text("release", encoding="utf-8")
    commands: list[list[str]] = []

    def backup_executor() -> None:
        return None

    def runner(command: list[str]) -> None:
        commands.append(command)
        if command[:3] == ["python", "-m", "alembic"]:
            raise RuntimeError("migration failed")

    with pytest.raises(RuntimeError, match="migration failed"):
        execute_release_deployment(
            settings,
            release_bundle_path=release_bundle_path,
            backup_executor=backup_executor,
            command_runner=runner,
        )

    assert commands == [["python", "-m", "alembic", "-c", "alembic.ini", "upgrade", "head"]]
