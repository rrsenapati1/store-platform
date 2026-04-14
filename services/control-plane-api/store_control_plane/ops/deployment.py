from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from ..config import Settings


CommandRunner = Callable[[list[str]], None]
BackupExecutor = Callable[[], None]


@dataclass(slots=True)
class ReleaseDeploymentPlan:
    release_bundle_path: Path
    alembic_command: list[str]
    api_restart_command: list[str]
    worker_restart_command: list[str]


def execute_release_deployment(
    settings: Settings,
    *,
    release_bundle_path: Path,
    backup_executor: BackupExecutor,
    command_runner: CommandRunner,
    dry_run: bool = False,
    python_command: str = "python",
) -> ReleaseDeploymentPlan:
    if not release_bundle_path.exists():
        raise FileNotFoundError(f"release bundle does not exist: {release_bundle_path}")

    plan = ReleaseDeploymentPlan(
        release_bundle_path=release_bundle_path,
        alembic_command=[python_command, "-m", "alembic", "-c", "alembic.ini", "upgrade", "head"],
        api_restart_command=["systemctl", "restart", "store-control-plane-api"],
        worker_restart_command=["systemctl", "restart", "store-control-plane-worker"],
    )

    if dry_run:
        return plan

    backup_executor()
    command_runner(plan.alembic_command)
    command_runner(plan.api_restart_command)
    command_runner(plan.worker_restart_command)
    return plan
