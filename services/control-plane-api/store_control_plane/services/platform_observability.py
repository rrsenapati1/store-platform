from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import Settings
from ..models import HubSyncStatus, OperationsJob, SyncConflict
from ..ops.object_storage import build_object_storage_client
from ..services.system_status import build_system_health
from ..utils import utc_now


def _parse_datetime(value: object) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        normalized = value.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            return None
        return parsed.replace(tzinfo=None)
    return None


class PlatformObservabilityService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self._session = session
        self._settings = settings

    async def build_summary(self) -> dict[str, object]:
        system_health = await build_system_health(settings=self._settings, session=self._session)
        operations = await self._build_operations_summary()
        runtime = await self._build_runtime_summary()
        backup = self._build_backup_summary()
        return {
            "environment": self._settings.deployment_environment,
            "release_version": self._settings.release_version,
            "system_health": system_health,
            "operations": operations,
            "runtime": runtime,
            "backup": backup,
        }

    async def _build_operations_summary(self) -> dict[str, object]:
        counts_statement = (
            select(OperationsJob.status, func.count(OperationsJob.id))
            .group_by(OperationsJob.status)
        )
        counts: dict[str, int] = {}
        for status, count in (await self._session.execute(counts_statement)).all():
            counts[str(status)] = int(count or 0)

        failures_statement = (
            select(OperationsJob)
            .where(OperationsJob.status.in_(("DEAD_LETTER", "RETRYABLE")))
            .order_by(OperationsJob.dead_lettered_at.desc().nullslast(), OperationsJob.updated_at.desc(), OperationsJob.id.desc())
            .limit(5)
        )
        failures = list((await self._session.scalars(failures_statement)).all())
        return {
            "queued_count": counts.get("QUEUED", 0),
            "running_count": counts.get("RUNNING", 0),
            "retryable_count": counts.get("RETRYABLE", 0),
            "dead_letter_count": counts.get("DEAD_LETTER", 0),
            "recent_failure_records": [
                {
                    "id": job.id,
                    "tenant_id": job.tenant_id,
                    "branch_id": job.branch_id,
                    "job_type": job.job_type,
                    "status": job.status,
                    "attempt_count": job.attempt_count,
                    "max_attempts": job.max_attempts,
                    "last_error": job.last_error,
                    "dead_lettered_at": job.dead_lettered_at,
                    "updated_at": job.updated_at,
                }
                for job in failures
            ],
        }

    async def _build_runtime_summary(self) -> dict[str, object]:
        statuses = list((await self._session.scalars(select(HubSyncStatus))).all())
        conflict_rows = (
            await self._session.execute(
                select(SyncConflict.tenant_id, SyncConflict.branch_id, func.count(SyncConflict.id))
                .where(SyncConflict.status == "OPEN")
                .group_by(SyncConflict.tenant_id, SyncConflict.branch_id)
            )
        ).all()
        conflict_counts = {(str(tenant_id), str(branch_id)): int(count or 0) for tenant_id, branch_id, count in conflict_rows}

        branch_records = []
        degraded_branch_count = 0
        connected_spoke_count = 0
        max_local_outbox_depth = 0
        for status in statuses:
            open_conflict_count = conflict_counts.get((status.tenant_id, status.branch_id), 0)
            connected_spoke_count += int(status.connected_spoke_count or 0)
            max_local_outbox_depth = max(max_local_outbox_depth, int(status.local_outbox_depth or 0))
            degraded = status.runtime_state != "HEALTHY" or open_conflict_count > 0 or int(status.local_outbox_depth or 0) > 0
            if degraded:
                degraded_branch_count += 1
            branch_records.append(
                {
                    "tenant_id": status.tenant_id,
                    "branch_id": status.branch_id,
                    "hub_device_id": status.hub_device_id,
                    "runtime_state": status.runtime_state,
                    "connected_spoke_count": int(status.connected_spoke_count or 0),
                    "local_outbox_depth": int(status.local_outbox_depth or 0),
                    "open_conflict_count": open_conflict_count,
                    "last_heartbeat_at": status.last_heartbeat_at,
                    "last_local_spoke_sync_at": status.last_local_spoke_sync_at,
                }
            )

        branch_records.sort(
            key=lambda record: (
                record["runtime_state"] == "HEALTHY" and record["open_conflict_count"] == 0 and record["local_outbox_depth"] == 0,
                -int(record["open_conflict_count"]),
                -int(record["local_outbox_depth"]),
                str(record["tenant_id"]),
                str(record["branch_id"]),
            )
        )
        return {
            "tracked_branch_count": len(statuses),
            "degraded_branch_count": degraded_branch_count,
            "connected_spoke_count": connected_spoke_count,
            "open_conflict_count": sum(conflict_counts.values()),
            "max_local_outbox_depth": max_local_outbox_depth,
            "branches": branch_records[:10],
        }

    def _build_backup_summary(self) -> dict[str, object]:
        if not self._settings.object_storage_bucket:
            return {
                "configured": False,
                "status": "not_configured",
                "last_successful_backup_at": None,
                "metadata_key": None,
                "release_version": None,
                "age_hours": None,
                "detail": None,
            }

        prefix = "/".join(
            segment
            for segment in (self._settings.object_storage_prefix, self._settings.backup_artifact_prefix)
            if segment
        )
        try:
            client = build_object_storage_client(self._settings)
            keys = client.list_keys(
                bucket=self._settings.object_storage_bucket,
                prefix=prefix,
                limit=100,
            )
            metadata_keys = sorted(key for key in keys if key.endswith("metadata.json"))
            if not metadata_keys:
                return {
                    "configured": True,
                    "status": "missing",
                    "last_successful_backup_at": None,
                    "metadata_key": None,
                    "release_version": None,
                    "age_hours": None,
                    "detail": "No backup metadata found in object storage",
                }
            metadata_key = metadata_keys[-1]
            payload = json.loads(
                client.read_text(
                    bucket=self._settings.object_storage_bucket,
                    key=metadata_key,
                )
            )
            created_at = _parse_datetime(payload.get("created_at"))
            age_hours = None
            if created_at is not None:
                age_hours = round((utc_now() - created_at).total_seconds() / 3600, 2)
            return {
                "configured": True,
                "status": "ok",
                "last_successful_backup_at": created_at,
                "metadata_key": metadata_key,
                "release_version": payload.get("release_version"),
                "age_hours": age_hours,
                "detail": None,
            }
        except Exception as exc:  # pragma: no cover - guarded by integration-style behavior
            return {
                "configured": True,
                "status": "error",
                "last_successful_backup_at": None,
                "metadata_key": None,
                "release_version": None,
                "age_hours": None,
                "detail": str(exc),
            }
