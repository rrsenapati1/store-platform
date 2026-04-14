from __future__ import annotations

from collections import defaultdict
from typing import Any


def _percentage(*, completed_jobs: int, failed_jobs: int) -> float:
    attempts = completed_jobs + failed_jobs
    if attempts == 0:
        return 100.0
    return round((completed_jobs / attempts) * 100, 2)


def _device_health_status(*, queued_jobs: int, failed_jobs: int) -> str:
    if failed_jobs > 0:
        return "ATTENTION"
    if queued_jobs > 0:
        return "BUSY"
    return "HEALTHY"


def build_branch_print_health_report(
    *,
    devices: list[dict[str, Any]],
    print_jobs: list[dict[str, Any]],
) -> dict[str, Any]:
    jobs_by_device: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for job in print_jobs:
        jobs_by_device[job["device_id"]].append(job)

    records: list[dict[str, Any]] = []
    queued_jobs = 0
    completed_jobs = 0
    failed_jobs = 0

    for device in devices:
        device_jobs = jobs_by_device.get(device["id"], [])
        queued_count = sum(1 for job in device_jobs if job["status"] == "QUEUED")
        completed_count = sum(1 for job in device_jobs if job["status"] == "COMPLETED")
        failed_count = sum(1 for job in device_jobs if job["status"] == "FAILED")
        latest_status = device_jobs[-1]["status"] if device_jobs else "IDLE"
        latest_failure_reason = next(
            (job["failure_reason"] for job in reversed(device_jobs) if job["status"] == "FAILED"),
            None,
        )
        queued_jobs += queued_count
        completed_jobs += completed_count
        failed_jobs += failed_count
        records.append(
            {
                "device_id": device["id"],
                "device_name": device["device_name"],
                "session_surface": device["session_surface"],
                "queued_jobs": queued_count,
                "completed_jobs": completed_count,
                "failed_jobs": failed_count,
                "latest_status": latest_status,
                "last_failure_reason": latest_failure_reason,
                "success_rate": _percentage(completed_jobs=completed_count, failed_jobs=failed_count),
                "health_status": _device_health_status(queued_jobs=queued_count, failed_jobs=failed_count),
            }
        )

    records.sort(key=lambda record: (-record["failed_jobs"], -record["queued_jobs"], record["device_name"]))
    return {
        "device_count": len(devices),
        "queued_jobs": queued_jobs,
        "completed_jobs": completed_jobs,
        "failed_jobs": failed_jobs,
        "records": records,
    }


def build_platform_print_exception_report(
    *,
    tenants_by_id: dict[str, dict[str, Any]],
    branches_by_id: dict[str, dict[str, Any]],
    devices: list[dict[str, Any]],
    print_jobs: list[dict[str, Any]],
) -> dict[str, Any]:
    jobs_by_device: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for job in print_jobs:
        jobs_by_device[job["device_id"]].append(job)

    records: list[dict[str, Any]] = []
    for device in devices:
        device_jobs = jobs_by_device.get(device["id"], [])
        queued_count = sum(1 for job in device_jobs if job["status"] == "QUEUED")
        completed_count = sum(1 for job in device_jobs if job["status"] == "COMPLETED")
        failed_count = sum(1 for job in device_jobs if job["status"] == "FAILED")
        if failed_count == 0:
            continue
        last_failure_reason = next(
            (job["failure_reason"] for job in reversed(device_jobs) if job["status"] == "FAILED"),
            None,
        )
        records.append(
            {
                "tenant_id": device["tenant_id"],
                "tenant_name": tenants_by_id[device["tenant_id"]]["name"],
                "branch_id": device["branch_id"],
                "branch_name": branches_by_id[device["branch_id"]]["name"],
                "device_id": device["id"],
                "device_name": device["device_name"],
                "session_surface": device["session_surface"],
                "queued_jobs": queued_count,
                "completed_jobs": completed_count,
                "failed_jobs": failed_count,
                "last_failure_reason": last_failure_reason,
                "success_rate": _percentage(completed_jobs=completed_count, failed_jobs=failed_count),
            }
        )

    records.sort(key=lambda record: (-record["failed_jobs"], record["tenant_name"], record["branch_name"], record["device_name"]))
    return {
        "failed_device_count": len(records),
        "records": records,
    }
