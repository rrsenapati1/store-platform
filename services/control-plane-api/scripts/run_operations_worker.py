from __future__ import annotations

import argparse
import asyncio
import sys
from dataclasses import dataclass
from pathlib import Path

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from store_control_plane.config.settings import Settings
from store_control_plane.db.session import create_session_factory
from store_control_plane.services.operations_worker import OperationsWorkerService
from store_control_plane.utils import utc_now


@dataclass(slots=True)
class WorkerOutcome:
    leased: int
    completed: int
    retried: int
    dead_lettered: int
    requeued_expired_leases: int
    deleted_completed_jobs: int


async def run_worker_once(settings: Settings) -> WorkerOutcome:
    engine, session_factory = create_session_factory(settings.database_url)
    try:
        async with session_factory() as session:
            worker = OperationsWorkerService(
                session,
                lease_seconds=settings.operations_worker_lease_seconds,
                retry_delay_seconds=settings.operations_job_retry_delay_seconds,
            )
            processed = await worker.process_due_jobs(
                limit=settings.operations_worker_batch_size,
                now=utc_now(),
            )
            swept = await worker.run_maintenance_sweep(
                now=utc_now(),
                retention_hours=settings.operations_job_retention_hours,
            )
            return WorkerOutcome(
                leased=processed["leased"],
                completed=processed["completed"],
                retried=processed["retried"],
                dead_lettered=processed["dead_lettered"],
                requeued_expired_leases=processed["requeued_expired_leases"],
                deleted_completed_jobs=swept["deleted_completed_jobs"],
            )
    finally:
        await engine.dispose()


async def run_worker_loop(settings: Settings) -> None:
    while True:
        outcome = await run_worker_once(settings)
        print(
            "[operations-worker]",
            f"leased={outcome.leased}",
            f"completed={outcome.completed}",
            f"retried={outcome.retried}",
            f"dead_lettered={outcome.dead_lettered}",
            f"requeued_expired_leases={outcome.requeued_expired_leases}",
            f"deleted_completed_jobs={outcome.deleted_completed_jobs}",
            flush=True,
        )
        await asyncio.sleep(settings.operations_worker_poll_seconds)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Store control-plane operations worker.")
    parser.add_argument("--once", action="store_true", help="Process one worker batch and exit.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = Settings()
    if args.once:
        outcome = asyncio.run(run_worker_once(settings))
        print(
            "[operations-worker]",
            f"leased={outcome.leased}",
            f"completed={outcome.completed}",
            f"retried={outcome.retried}",
            f"dead_lettered={outcome.dead_lettered}",
            f"requeued_expired_leases={outcome.requeued_expired_leases}",
            f"deleted_completed_jobs={outcome.deleted_completed_jobs}",
        )
        return
    asyncio.run(run_worker_loop(settings))


if __name__ == "__main__":
    main()
