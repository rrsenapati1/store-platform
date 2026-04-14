from store_api.print_reporting import build_branch_print_health_report, build_platform_print_exception_report


def test_branch_print_health_report_marks_failed_device_for_attention():
    report = build_branch_print_health_report(
        devices=[
            {
                "id": "device-1",
                "device_name": "Counter Desktop 1",
                "session_surface": "store_desktop",
            }
        ],
        print_jobs=[
            {"device_id": "device-1", "status": "COMPLETED", "failure_reason": None},
            {"device_id": "device-1", "status": "FAILED", "failure_reason": "Paper jam"},
        ],
    )

    assert report == {
        "device_count": 1,
        "queued_jobs": 0,
        "completed_jobs": 1,
        "failed_jobs": 1,
        "records": [
            {
                "device_id": "device-1",
                "device_name": "Counter Desktop 1",
                "session_surface": "store_desktop",
                "queued_jobs": 0,
                "completed_jobs": 1,
                "failed_jobs": 1,
                "latest_status": "FAILED",
                "last_failure_reason": "Paper jam",
                "success_rate": 50.0,
                "health_status": "ATTENTION",
            }
        ],
    }


def test_platform_print_exception_report_rolls_up_failed_devices_only():
    report = build_platform_print_exception_report(
        tenants_by_id={"tenant-1": {"name": "Acme Retail"}},
        branches_by_id={"branch-1": {"name": "Bengaluru Flagship"}},
        devices=[
            {
                "id": "device-1",
                "tenant_id": "tenant-1",
                "branch_id": "branch-1",
                "device_name": "Counter Desktop 1",
                "session_surface": "store_desktop",
            },
            {
                "id": "device-2",
                "tenant_id": "tenant-1",
                "branch_id": "branch-1",
                "device_name": "Label Station 2",
                "session_surface": "store_desktop",
            },
        ],
        print_jobs=[
            {"device_id": "device-1", "status": "FAILED", "failure_reason": "Out of paper"},
            {"device_id": "device-1", "status": "COMPLETED", "failure_reason": None},
            {"device_id": "device-2", "status": "COMPLETED", "failure_reason": None},
        ],
    )

    assert report == {
        "failed_device_count": 1,
        "records": [
            {
                "tenant_id": "tenant-1",
                "tenant_name": "Acme Retail",
                "branch_id": "branch-1",
                "branch_name": "Bengaluru Flagship",
                "device_id": "device-1",
                "device_name": "Counter Desktop 1",
                "session_surface": "store_desktop",
                "queued_jobs": 0,
                "completed_jobs": 1,
                "failed_jobs": 1,
                "last_failure_reason": "Out of paper",
                "success_rate": 50.0,
            }
        ],
    }
