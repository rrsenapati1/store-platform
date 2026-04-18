from fastapi.testclient import TestClient

from store_control_plane.main import create_app
from conftest import sqlite_test_database_url


def _stub_token(*, subject: str, email: str, name: str) -> str:
    return f"stub:sub={subject};email={email};name={name}"


def _exchange(client: TestClient, *, subject: str, email: str, name: str) -> dict[str, str]:
    response = client.post(
        "/v1/auth/oidc/exchange",
        json={"token": _stub_token(subject=subject, email=email, name=name)},
    )
    assert response.status_code == 200
    return response.json()


def _bootstrap_workforce_context(
    client: TestClient,
    *,
    slug: str,
) -> dict[str, str]:
    admin_session = _exchange(client, subject="platform-admin-1", email="admin@store.local", name="Platform Admin")
    admin_headers = {"authorization": f"Bearer {admin_session['access_token']}"}

    tenant = client.post(
        "/v1/platform/tenants",
        headers=admin_headers,
        json={"name": "Acme Retail", "slug": slug},
    )
    assert tenant.status_code == 200
    tenant_id = tenant.json()["id"]

    owner_invite = client.post(
        f"/v1/platform/tenants/{tenant_id}/owner-invites",
        headers=admin_headers,
        json={"email": "owner@acme.local", "full_name": "Acme Owner"},
    )
    assert owner_invite.status_code == 200

    owner_session = _exchange(client, subject="owner-1", email="owner@acme.local", name="Acme Owner")
    owner_headers = {"authorization": f"Bearer {owner_session['access_token']}"}

    branch = client.post(
        f"/v1/tenants/{tenant_id}/branches",
        headers=owner_headers,
        json={"name": "Bengaluru Flagship", "code": "blr-flagship", "gstin": "29ABCDE1234F1Z5"},
    )
    assert branch.status_code == 200
    branch_id = branch.json()["id"]

    staff_profile = client.post(
        f"/v1/tenants/{tenant_id}/staff-profiles",
        headers=owner_headers,
        json={
            "email": "cashier@acme.local",
            "full_name": "Cash Counter One",
            "phone_number": "9876543210",
            "primary_branch_id": branch_id,
        },
    )
    assert staff_profile.status_code == 200
    staff_profile_id = staff_profile.json()["id"]

    branch_membership = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/memberships",
        headers=owner_headers,
        json={"email": "cashier@acme.local", "full_name": "Cash Counter One", "role_name": "cashier"},
    )
    assert branch_membership.status_code == 200

    device = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/devices",
        headers=owner_headers,
        json={
            "device_name": "Counter Desktop 1",
            "device_code": "BLR-POS-01",
            "session_surface": "store_desktop",
            "assigned_staff_profile_id": staff_profile_id,
        },
    )
    assert device.status_code == 200
    device_id = device.json()["id"]

    cashier_session = _exchange(client, subject="cashier-1", email="cashier@acme.local", name="Cash Counter One")
    cashier_headers = {"authorization": f"Bearer {cashier_session['access_token']}"}

    return {
        "tenant_id": tenant_id,
        "branch_id": branch_id,
        "staff_profile_id": staff_profile_id,
        "device_id": device_id,
        "owner_access_token": owner_session["access_token"],
        "cashier_access_token": cashier_session["access_token"],
    }


def test_owner_bootstraps_staff_directory_and_branch_devices():
    database_url = sqlite_test_database_url("staff-devices")
    client = TestClient(
        create_app(
            database_url=database_url,
            bootstrap_database=True,
            korsenex_idp_mode="stub",
            platform_admin_emails=["admin@store.local"],
        )
    )

    admin_session = _exchange(client, subject="platform-admin-1", email="admin@store.local", name="Platform Admin")
    admin_headers = {"authorization": f"Bearer {admin_session['access_token']}"}

    tenant = client.post(
        "/v1/platform/tenants",
        headers=admin_headers,
        json={"name": "Acme Retail", "slug": "acme-retail"},
    )
    assert tenant.status_code == 200
    tenant_id = tenant.json()["id"]

    owner_invite = client.post(
        f"/v1/platform/tenants/{tenant_id}/owner-invites",
        headers=admin_headers,
        json={"email": "owner@acme.local", "full_name": "Acme Owner"},
    )
    assert owner_invite.status_code == 200

    owner_session = _exchange(client, subject="owner-1", email="owner@acme.local", name="Acme Owner")
    owner_headers = {"authorization": f"Bearer {owner_session['access_token']}"}

    branch = client.post(
        f"/v1/tenants/{tenant_id}/branches",
        headers=owner_headers,
        json={"name": "Bengaluru Flagship", "code": "blr-flagship", "gstin": "29ABCDE1234F1Z5"},
    )
    assert branch.status_code == 200
    branch_id = branch.json()["id"]

    staff_profile = client.post(
        f"/v1/tenants/{tenant_id}/staff-profiles",
        headers=owner_headers,
        json={
            "email": "cashier@acme.local",
            "full_name": "Cash Counter One",
            "phone_number": "9876543210",
            "primary_branch_id": branch_id,
        },
    )
    assert staff_profile.status_code == 200
    staff_profile_id = staff_profile.json()["id"]

    branch_membership = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/memberships",
        headers=owner_headers,
        json={"email": "cashier@acme.local", "full_name": "Cash Counter One", "role_name": "cashier"},
    )
    assert branch_membership.status_code == 200

    staff_directory = client.get(
        f"/v1/tenants/{tenant_id}/staff-profiles",
        headers=owner_headers,
    )
    assert staff_directory.status_code == 200
    assert staff_directory.json()["records"][0]["email"] == "cashier@acme.local"
    assert staff_directory.json()["records"][0]["role_names"] == ["cashier"]
    assert staff_directory.json()["records"][0]["branch_ids"] == [branch_id]

    device = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/devices",
        headers=owner_headers,
        json={
            "device_name": "Counter Desktop 1",
            "device_code": "BLR-POS-01",
            "session_surface": "store_desktop",
            "assigned_staff_profile_id": staff_profile_id,
        },
    )
    assert device.status_code == 200
    assert device.json()["session_surface"] == "store_desktop"

    devices = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/devices",
        headers=owner_headers,
    )
    assert devices.status_code == 200
    assert devices.json()["records"][0]["device_code"] == "BLR-POS-01"
    assert devices.json()["records"][0]["assigned_staff_full_name"] == "Cash Counter One"

    cashier_session = _exchange(client, subject="cashier-1", email="cashier@acme.local", name="Cash Counter One")
    cashier_headers = {"authorization": f"Bearer {cashier_session['access_token']}"}

    actor = client.get("/v1/auth/me", headers=cashier_headers)
    assert actor.status_code == 200
    assert actor.json()["branch_memberships"][0]["branch_id"] == branch_id

    refreshed_staff_directory = client.get(
        f"/v1/tenants/{tenant_id}/staff-profiles",
        headers=owner_headers,
    )
    assert refreshed_staff_directory.status_code == 200
    assert refreshed_staff_directory.json()["records"][0]["user_id"] == actor.json()["user_id"]


def test_cashier_session_lifecycle_is_governed_per_device() -> None:
    database_url = sqlite_test_database_url("cashier-session-lifecycle")
    client = TestClient(
        create_app(
            database_url=database_url,
            bootstrap_database=True,
            korsenex_idp_mode="stub",
            platform_admin_emails=["admin@store.local"],
        )
    )

    admin_session = _exchange(client, subject="platform-admin-1", email="admin@store.local", name="Platform Admin")
    admin_headers = {"authorization": f"Bearer {admin_session['access_token']}"}

    tenant = client.post(
        "/v1/platform/tenants",
        headers=admin_headers,
        json={"name": "Acme Retail", "slug": "acme-retail-cashier-session"},
    )
    assert tenant.status_code == 200
    tenant_id = tenant.json()["id"]

    owner_invite = client.post(
        f"/v1/platform/tenants/{tenant_id}/owner-invites",
        headers=admin_headers,
        json={"email": "owner@acme.local", "full_name": "Acme Owner"},
    )
    assert owner_invite.status_code == 200

    owner_session = _exchange(client, subject="owner-1", email="owner@acme.local", name="Acme Owner")
    owner_headers = {"authorization": f"Bearer {owner_session['access_token']}"}

    branch = client.post(
        f"/v1/tenants/{tenant_id}/branches",
        headers=owner_headers,
        json={"name": "Bengaluru Flagship", "code": "blr-flagship", "gstin": "29ABCDE1234F1Z5"},
    )
    assert branch.status_code == 200
    branch_id = branch.json()["id"]

    staff_profile = client.post(
        f"/v1/tenants/{tenant_id}/staff-profiles",
        headers=owner_headers,
        json={
            "email": "cashier@acme.local",
            "full_name": "Cash Counter One",
            "phone_number": "9876543210",
            "primary_branch_id": branch_id,
        },
    )
    assert staff_profile.status_code == 200
    staff_profile_id = staff_profile.json()["id"]

    branch_membership = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/memberships",
        headers=owner_headers,
        json={"email": "cashier@acme.local", "full_name": "Cash Counter One", "role_name": "cashier"},
    )
    assert branch_membership.status_code == 200

    device = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/devices",
        headers=owner_headers,
        json={
            "device_name": "Counter Desktop 1",
            "device_code": "BLR-POS-01",
            "session_surface": "store_desktop",
            "assigned_staff_profile_id": staff_profile_id,
        },
    )
    assert device.status_code == 200
    device_id = device.json()["id"]

    cashier_session = _exchange(client, subject="cashier-1", email="cashier@acme.local", name="Cash Counter One")
    cashier_headers = {"authorization": f"Bearer {cashier_session['access_token']}"}

    attendance_opened = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/attendance-sessions",
        headers=cashier_headers,
        json={
            "device_registration_id": device_id,
            "staff_profile_id": staff_profile_id,
            "clock_in_note": "Morning shift start",
        },
    )
    assert attendance_opened.status_code == 200

    opened = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/cashier-sessions",
        headers=cashier_headers,
        json={
            "device_registration_id": device_id,
            "staff_profile_id": staff_profile_id,
            "opening_float_amount": 500.0,
            "opening_note": "Morning shift",
        },
    )
    assert opened.status_code == 200
    cashier_session_id = opened.json()["id"]
    assert opened.json()["status"] == "OPEN"
    assert opened.json()["opening_float_amount"] == 500.0

    duplicate_open = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/cashier-sessions",
        headers=cashier_headers,
        json={
            "device_registration_id": device_id,
            "staff_profile_id": staff_profile_id,
            "opening_float_amount": 250.0,
            "opening_note": "Second open should be rejected",
        },
    )
    assert duplicate_open.status_code == 409

    closed = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/cashier-sessions/{cashier_session_id}/close",
        headers=cashier_headers,
        json={"closing_note": "Shift complete"},
    )
    assert closed.status_code == 200
    assert closed.json()["status"] == "CLOSED"
    assert closed.json()["closing_note"] == "Shift complete"

    reopened = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/cashier-sessions",
        headers=cashier_headers,
        json={
            "device_registration_id": device_id,
            "staff_profile_id": staff_profile_id,
            "opening_float_amount": 450.0,
            "opening_note": "Evening shift",
        },
    )
    assert reopened.status_code == 200
    reopened_session_id = reopened.json()["id"]

    forced_closed = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/cashier-sessions/{reopened_session_id}/force-close",
        headers=owner_headers,
        json={"reason": "Terminal left signed in"},
    )
    assert forced_closed.status_code == 200
    assert forced_closed.json()["status"] == "FORCED_CLOSED"
    assert forced_closed.json()["force_close_reason"] == "Terminal left signed in"

    attendance_closed = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/attendance-sessions/{attendance_opened.json()['id']}/close",
        headers=cashier_headers,
        json={"clock_out_note": "Shift complete"},
    )
    assert attendance_closed.status_code == 200


def test_attendance_session_lifecycle_gates_cashier_sessions() -> None:
    database_url = sqlite_test_database_url("attendance-session-lifecycle")
    client = TestClient(
        create_app(
            database_url=database_url,
            bootstrap_database=True,
            korsenex_idp_mode="stub",
            platform_admin_emails=["admin@store.local"],
        )
    )

    admin_session = _exchange(client, subject="platform-admin-1", email="admin@store.local", name="Platform Admin")
    admin_headers = {"authorization": f"Bearer {admin_session['access_token']}"}

    tenant = client.post(
        "/v1/platform/tenants",
        headers=admin_headers,
        json={"name": "Acme Retail", "slug": "acme-retail-attendance"},
    )
    assert tenant.status_code == 200
    tenant_id = tenant.json()["id"]

    owner_invite = client.post(
        f"/v1/platform/tenants/{tenant_id}/owner-invites",
        headers=admin_headers,
        json={"email": "owner@acme.local", "full_name": "Acme Owner"},
    )
    assert owner_invite.status_code == 200

    owner_session = _exchange(client, subject="owner-1", email="owner@acme.local", name="Acme Owner")
    owner_headers = {"authorization": f"Bearer {owner_session['access_token']}"}

    branch = client.post(
        f"/v1/tenants/{tenant_id}/branches",
        headers=owner_headers,
        json={"name": "Bengaluru Flagship", "code": "blr-flagship", "gstin": "29ABCDE1234F1Z5"},
    )
    assert branch.status_code == 200
    branch_id = branch.json()["id"]

    staff_profile = client.post(
        f"/v1/tenants/{tenant_id}/staff-profiles",
        headers=owner_headers,
        json={
            "email": "cashier@acme.local",
            "full_name": "Cash Counter One",
            "phone_number": "9876543210",
            "primary_branch_id": branch_id,
        },
    )
    assert staff_profile.status_code == 200
    staff_profile_id = staff_profile.json()["id"]

    branch_membership = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/memberships",
        headers=owner_headers,
        json={"email": "cashier@acme.local", "full_name": "Cash Counter One", "role_name": "cashier"},
    )
    assert branch_membership.status_code == 200

    device = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/devices",
        headers=owner_headers,
        json={
            "device_name": "Counter Desktop 1",
            "device_code": "BLR-POS-01",
            "session_surface": "store_desktop",
            "assigned_staff_profile_id": staff_profile_id,
        },
    )
    assert device.status_code == 200
    device_id = device.json()["id"]

    cashier_session = _exchange(client, subject="cashier-1", email="cashier@acme.local", name="Cash Counter One")
    cashier_headers = {"authorization": f"Bearer {cashier_session['access_token']}"}

    cashier_open_without_attendance = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/cashier-sessions",
        headers=cashier_headers,
        json={
            "device_registration_id": device_id,
            "staff_profile_id": staff_profile_id,
            "opening_float_amount": 500.0,
            "opening_note": "Morning shift",
        },
    )
    assert cashier_open_without_attendance.status_code == 400

    attendance_opened = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/attendance-sessions",
        headers=cashier_headers,
        json={
            "device_registration_id": device_id,
            "staff_profile_id": staff_profile_id,
            "clock_in_note": "Morning shift start",
        },
    )
    assert attendance_opened.status_code == 200
    attendance_session_id = attendance_opened.json()["id"]
    assert attendance_opened.json()["status"] == "OPEN"

    attendance_duplicate = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/attendance-sessions",
        headers=cashier_headers,
        json={
            "device_registration_id": device_id,
            "staff_profile_id": staff_profile_id,
            "clock_in_note": "Second clock-in should be rejected",
        },
    )
    assert attendance_duplicate.status_code == 409

    cashier_opened = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/cashier-sessions",
        headers=cashier_headers,
        json={
            "device_registration_id": device_id,
            "staff_profile_id": staff_profile_id,
            "opening_float_amount": 500.0,
            "opening_note": "Morning shift",
        },
    )
    assert cashier_opened.status_code == 200
    cashier_session_id = cashier_opened.json()["id"]

    attendance_close_while_cashier_open = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/attendance-sessions/{attendance_session_id}/close",
        headers=cashier_headers,
        json={"clock_out_note": "Trying to leave early"},
    )
    assert attendance_close_while_cashier_open.status_code == 400

    cashier_closed = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/cashier-sessions/{cashier_session_id}/close",
        headers=cashier_headers,
        json={"closing_note": "Shift complete"},
    )
    assert cashier_closed.status_code == 200

    attendance_closed = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/attendance-sessions/{attendance_session_id}/close",
        headers=cashier_headers,
        json={"clock_out_note": "Shift complete"},
    )
    assert attendance_closed.status_code == 200
    assert attendance_closed.json()["status"] == "CLOSED"
    assert attendance_closed.json()["clock_out_note"] == "Shift complete"

    attendance_reopened = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/attendance-sessions",
        headers=cashier_headers,
        json={
            "device_registration_id": device_id,
            "staff_profile_id": staff_profile_id,
            "clock_in_note": "Evening shift",
        },
    )
    assert attendance_reopened.status_code == 200
    reopened_attendance_session_id = attendance_reopened.json()["id"]

    forced_closed = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/attendance-sessions/{reopened_attendance_session_id}/force-close",
        headers=owner_headers,
        json={"reason": "Missed clock-out on abandoned terminal"},
    )
    assert forced_closed.status_code == 200
    assert forced_closed.json()["status"] == "FORCED_CLOSED"
    assert forced_closed.json()["force_close_reason"] == "Missed clock-out on abandoned terminal"


def test_shift_session_lifecycle_and_policy_can_gate_attendance() -> None:
    database_url = sqlite_test_database_url("shift-session-lifecycle")
    client = TestClient(
        create_app(
            database_url=database_url,
            bootstrap_database=True,
            korsenex_idp_mode="stub",
            platform_admin_emails=["admin@store.local"],
        )
    )

    context = _bootstrap_workforce_context(client, slug="acme-retail-shifts")
    tenant_id = context["tenant_id"]
    branch_id = context["branch_id"]
    owner_headers = {"authorization": f"Bearer {context['owner_access_token']}"}
    cashier_headers = {"authorization": f"Bearer {context['cashier_access_token']}"}

    runtime_policy = client.put(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/runtime-policy",
        headers=owner_headers,
        json={
            "require_shift_for_attendance": True,
            "require_attendance_for_cashier": True,
            "require_assigned_staff_for_device": True,
            "allow_offline_sales": True,
            "max_pending_offline_sales": 25,
        },
    )
    assert runtime_policy.status_code == 200
    assert runtime_policy.json()["require_shift_for_attendance"] is True

    attendance_without_shift = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/attendance-sessions",
        headers=cashier_headers,
        json={
            "device_registration_id": context["device_id"],
            "staff_profile_id": context["staff_profile_id"],
            "clock_in_note": "Trying to clock in before shift",
        },
    )
    assert attendance_without_shift.status_code == 400

    opened_shift = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/shift-sessions",
        headers=cashier_headers,
        json={"shift_name": "Morning Shift", "opening_note": "Counter opens at 9 AM"},
    )
    assert opened_shift.status_code == 200
    shift_session_id = opened_shift.json()["id"]
    assert opened_shift.json()["status"] == "OPEN"

    attendance_opened = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/attendance-sessions",
        headers=cashier_headers,
        json={
            "device_registration_id": context["device_id"],
            "staff_profile_id": context["staff_profile_id"],
            "clock_in_note": "Morning attendance",
        },
    )
    assert attendance_opened.status_code == 200
    attendance_session_id = attendance_opened.json()["id"]
    assert attendance_opened.json()["shift_session_id"] == shift_session_id

    cashier_session = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/cashier-sessions",
        headers=cashier_headers,
        json={
            "device_registration_id": context["device_id"],
            "staff_profile_id": context["staff_profile_id"],
            "opening_float_amount": 500.0,
            "opening_note": "Morning cashier session",
        },
    )
    assert cashier_session.status_code == 200
    cashier_session_id = cashier_session.json()["id"]

    close_shift_while_active = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/shift-sessions/{shift_session_id}/close",
        headers=cashier_headers,
        json={"closing_note": "Trying to close too early"},
    )
    assert close_shift_while_active.status_code == 400

    cashier_closed = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/cashier-sessions/{cashier_session_id}/close",
        headers=cashier_headers,
        json={"closing_note": "Cash drawer balanced"},
    )
    assert cashier_closed.status_code == 200

    attendance_closed = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/attendance-sessions/{attendance_session_id}/close",
        headers=cashier_headers,
        json={"clock_out_note": "Leaving after shift"},
    )
    assert attendance_closed.status_code == 200

    shift_closed = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/shift-sessions/{shift_session_id}/close",
        headers=cashier_headers,
        json={"closing_note": "Morning shift reconciled"},
    )
    assert shift_closed.status_code == 200
    assert shift_closed.json()["status"] == "CLOSED"
    assert shift_closed.json()["closing_note"] == "Morning shift reconciled"
    assert shift_closed.json()["linked_attendance_sessions_count"] == 1
    assert shift_closed.json()["linked_cashier_sessions_count"] == 1


def test_workforce_audit_export_and_branch_runtime_policy_reads() -> None:
    database_url = sqlite_test_database_url("workforce-audit-export")
    client = TestClient(
        create_app(
            database_url=database_url,
            bootstrap_database=True,
            korsenex_idp_mode="stub",
            platform_admin_emails=["admin@store.local"],
        )
    )

    context = _bootstrap_workforce_context(client, slug="acme-retail-audit-export")
    tenant_id = context["tenant_id"]
    branch_id = context["branch_id"]
    owner_headers = {"authorization": f"Bearer {context['owner_access_token']}"}
    cashier_headers = {"authorization": f"Bearer {context['cashier_access_token']}"}

    default_runtime_policy = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/runtime-policy",
        headers=owner_headers,
    )
    assert default_runtime_policy.status_code == 200
    assert default_runtime_policy.json()["require_shift_for_attendance"] is False

    updated_runtime_policy = client.put(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/runtime-policy",
        headers=owner_headers,
        json={
            "require_shift_for_attendance": True,
            "require_attendance_for_cashier": True,
            "require_assigned_staff_for_device": True,
            "allow_offline_sales": False,
            "max_pending_offline_sales": 3,
        },
    )
    assert updated_runtime_policy.status_code == 200
    assert updated_runtime_policy.json()["allow_offline_sales"] is False
    assert updated_runtime_policy.json()["max_pending_offline_sales"] == 3

    shift = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/shift-sessions",
        headers=cashier_headers,
        json={"shift_name": "Audit Shift", "opening_note": "Creating audit trail"},
    )
    assert shift.status_code == 200

    attendance = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/attendance-sessions",
        headers=cashier_headers,
        json={
            "device_registration_id": context["device_id"],
            "staff_profile_id": context["staff_profile_id"],
            "clock_in_note": "Audit attendance",
        },
    )
    assert attendance.status_code == 200

    cashier_session = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/cashier-sessions",
        headers=cashier_headers,
        json={
            "device_registration_id": context["device_id"],
            "staff_profile_id": context["staff_profile_id"],
            "opening_float_amount": 300.0,
            "opening_note": "Audit cashier session",
        },
    )
    assert cashier_session.status_code == 200

    workforce_audit_events = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/workforce-audit-events",
        headers=owner_headers,
    )
    assert workforce_audit_events.status_code == 200
    actions = [record["action"] for record in workforce_audit_events.json()["records"]]
    assert "branch_runtime_policy.updated" in actions
    assert "shift_session.opened" in actions
    assert "attendance_session.opened" in actions
    assert "cashier_session.opened" in actions

    workforce_audit_export = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/workforce-audit-export",
        headers=owner_headers,
    )
    assert workforce_audit_export.status_code == 200
    export_payload = workforce_audit_export.json()
    assert export_payload["content_type"] == "text/csv"
    assert export_payload["filename"].startswith("workforce-audit-")
    assert "action,entity_type,entity_id" in export_payload["content"]
    assert "shift_session.opened" in export_payload["content"]
    assert "branch_runtime_policy.updated" in export_payload["content"]
