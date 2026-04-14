from fastapi.testclient import TestClient

from conftest import sqlite_test_database_url
from store_control_plane.main import create_app


def _stub_token(*, subject: str, email: str, name: str) -> str:
    return f"stub:sub={subject};email={email};name={name}"


def _exchange(client: TestClient, *, subject: str, email: str, name: str) -> dict[str, str]:
    response = client.post(
        "/v1/auth/oidc/exchange",
        json={"token": _stub_token(subject=subject, email=email, name=name)},
    )
    assert response.status_code == 200
    return response.json()


def _bootstrap_store_desktop_context(
    client: TestClient,
    *,
    installation_id: str,
    device_code: str,
) -> dict[str, object]:
    admin_session = _exchange(client, subject="platform-admin-1", email="admin@store.local", name="Platform Admin")
    admin_headers = {"authorization": f"Bearer {admin_session['access_token']}"}

    tenant = client.post(
        "/v1/platform/tenants",
        headers=admin_headers,
        json={"name": "Acme Retail", "slug": f"acme-retail-{device_code.lower()}"},
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

    membership = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/memberships",
        headers=owner_headers,
        json={"email": "cashier@acme.local", "full_name": "Cash Counter One", "role_name": "cashier"},
    )
    assert membership.status_code == 200

    claim = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/runtime/device-claim",
        headers=owner_headers,
        json={
            "installation_id": installation_id,
            "runtime_kind": "packaged_desktop",
            "hostname": "COUNTER-01",
            "operating_system": "windows",
            "architecture": "x86_64",
            "app_version": "0.1.0",
        },
    )
    assert claim.status_code == 200

    approval = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/device-claims/{claim.json()['claim_id']}/approve",
        headers=owner_headers,
        json={
            "device_name": "Counter Desktop 1",
            "device_code": device_code,
            "session_surface": "store_desktop",
            "assigned_staff_profile_id": staff_profile_id,
        },
    )
    assert approval.status_code == 200

    return {
        "tenant_id": tenant_id,
        "branch_id": branch_id,
        "device_id": approval.json()["device"]["id"],
        "staff_profile_id": staff_profile_id,
        "installation_id": installation_id,
        "admin_headers": admin_headers,
        "owner_headers": owner_headers,
    }


def test_owner_issues_store_desktop_activation_and_packaged_runtime_redeems_it_without_staff_oidc_login():
    database_url = sqlite_test_database_url("store-desktop-activation")
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

    membership = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/memberships",
        headers=owner_headers,
        json={"email": "cashier@acme.local", "full_name": "Cash Counter One", "role_name": "cashier"},
    )
    assert membership.status_code == 200
    assert membership.json()["status"] == "PENDING"

    claim = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/runtime/device-claim",
        headers=owner_headers,
        json={
            "installation_id": "store-runtime-abcd1234efgh5678",
            "runtime_kind": "packaged_desktop",
            "hostname": "COUNTER-01",
            "operating_system": "windows",
            "architecture": "x86_64",
            "app_version": "0.1.0",
        },
    )
    assert claim.status_code == 200
    claim_id = claim.json()["claim_id"]

    approval = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/device-claims/{claim_id}/approve",
        headers=owner_headers,
        json={
            "device_name": "Counter Desktop 1",
            "device_code": "BLR-POS-01",
            "session_surface": "store_desktop",
            "assigned_staff_profile_id": staff_profile_id,
        },
    )
    assert approval.status_code == 200
    device_id = approval.json()["device"]["id"]

    activation_issue = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/devices/{device_id}/desktop-activation",
        headers=owner_headers,
    )
    assert activation_issue.status_code == 200
    activation_code = activation_issue.json()["activation_code"]
    assert activation_issue.json()["staff_profile_id"] == staff_profile_id

    redeem = client.post(
        "/v1/auth/store-desktop/activate",
        json={
            "installation_id": "store-runtime-abcd1234efgh5678",
            "activation_code": activation_code,
        },
    )
    assert redeem.status_code == 200
    assert redeem.json()["access_token"]
    assert redeem.json()["device_id"] == device_id
    assert redeem.json()["staff_profile_id"] == staff_profile_id
    assert redeem.json()["local_auth_token"]
    assert redeem.json()["offline_valid_until"]
    assert redeem.json()["activation_version"] == 1

    runtime_headers = {"authorization": f"Bearer {redeem.json()['access_token']}"}
    runtime_actor = client.get("/v1/auth/me", headers=runtime_headers)
    assert runtime_actor.status_code == 200
    assert runtime_actor.json()["email"] == "cashier@acme.local"
    assert runtime_actor.json()["branch_memberships"][0]["branch_id"] == branch_id
    assert runtime_actor.json()["branch_memberships"][0]["role_name"] == "cashier"
    assert redeem.json()["expires_at"]

    refresh = client.post("/v1/auth/refresh", headers=runtime_headers)
    assert refresh.status_code == 200
    assert refresh.json()["access_token"] != redeem.json()["access_token"]
    assert refresh.json()["expires_at"]

    old_runtime_actor = client.get("/v1/auth/me", headers=runtime_headers)
    assert old_runtime_actor.status_code == 401

    refreshed_headers = {"authorization": f"Bearer {refresh.json()['access_token']}"}
    refreshed_runtime_actor = client.get("/v1/auth/me", headers=refreshed_headers)
    assert refreshed_runtime_actor.status_code == 200

    sign_out = client.post("/v1/auth/sign-out", headers=refreshed_headers)
    assert sign_out.status_code == 200
    assert sign_out.json()["status"] == "signed_out"

    runtime_actor_after_sign_out = client.get("/v1/auth/me", headers=refreshed_headers)
    assert runtime_actor_after_sign_out.status_code == 401

    unlock = client.post(
        "/v1/auth/store-desktop/unlock",
        json={
            "installation_id": "store-runtime-abcd1234efgh5678",
            "local_auth_token": redeem.json()["local_auth_token"],
        },
    )
    assert unlock.status_code == 200
    assert unlock.json()["access_token"]
    assert unlock.json()["access_token"] != refresh.json()["access_token"]
    assert unlock.json()["device_id"] == device_id
    assert unlock.json()["staff_profile_id"] == staff_profile_id
    assert unlock.json()["activation_version"] == 1
    assert unlock.json()["offline_valid_until"]

    staff_directory = client.get(
        f"/v1/tenants/{tenant_id}/staff-profiles",
        headers=owner_headers,
    )
    assert staff_directory.status_code == 200
    assert staff_directory.json()["records"][0]["user_id"] == runtime_actor.json()["user_id"]

    second_redeem = client.post(
        "/v1/auth/store-desktop/activate",
        json={
            "installation_id": "store-runtime-abcd1234efgh5678",
            "activation_code": activation_code,
        },
    )
    assert second_redeem.status_code == 401


def test_store_desktop_activation_rejects_staff_profiles_that_reuse_owner_web_identity():
    database_url = sqlite_test_database_url("store-desktop-activation-owner-conflict")
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
            "email": "owner@acme.local",
            "full_name": "Acme Owner",
            "phone_number": "9876543210",
            "primary_branch_id": branch_id,
        },
    )
    assert staff_profile.status_code == 200
    staff_profile_id = staff_profile.json()["id"]

    membership = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/memberships",
        headers=owner_headers,
        json={"email": "owner@acme.local", "full_name": "Acme Owner", "role_name": "cashier"},
    )
    assert membership.status_code == 200

    claim = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/runtime/device-claim",
        headers=owner_headers,
        json={
            "installation_id": "store-runtime-ownerconflict1234",
            "runtime_kind": "packaged_desktop",
            "hostname": "COUNTER-01",
            "operating_system": "windows",
            "architecture": "x86_64",
            "app_version": "0.1.0",
        },
    )
    assert claim.status_code == 200
    claim_id = claim.json()["claim_id"]

    approval = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/device-claims/{claim_id}/approve",
        headers=owner_headers,
        json={
            "device_name": "Counter Desktop 1",
            "device_code": "BLR-POS-02",
            "session_surface": "store_desktop",
            "assigned_staff_profile_id": staff_profile_id,
        },
    )
    assert approval.status_code == 200
    device_id = approval.json()["device"]["id"]

    activation_issue = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/devices/{device_id}/desktop-activation",
        headers=owner_headers,
    )
    assert activation_issue.status_code == 200

    redeem = client.post(
        "/v1/auth/store-desktop/activate",
        json={
            "installation_id": "store-runtime-ownerconflict1234",
            "activation_code": activation_issue.json()["activation_code"],
        },
    )
    assert redeem.status_code == 409
    assert redeem.json()["detail"] == "Staff profile email is already bound to an interactive user"


def test_store_desktop_activation_is_blocked_during_grace_but_existing_unlock_continues_until_grace_expires():
    database_url = sqlite_test_database_url("store-desktop-activation-grace")
    client = TestClient(
        create_app(
            database_url=database_url,
            bootstrap_database=True,
            korsenex_idp_mode="stub",
            platform_admin_emails=["admin@store.local"],
        )
    )

    context = _bootstrap_store_desktop_context(
        client,
        installation_id="store-runtime-grace1234",
        device_code="BLR-POS-GRACE-01",
    )

    activation_issue = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/devices/{context['device_id']}/desktop-activation",
        headers=context["owner_headers"],
    )
    assert activation_issue.status_code == 200

    redeem = client.post(
        "/v1/auth/store-desktop/activate",
        json={
            "installation_id": context["installation_id"],
            "activation_code": activation_issue.json()["activation_code"],
        },
    )
    assert redeem.status_code == 200

    bootstrap = client.post(
        f"/v1/tenants/{context['tenant_id']}/billing/subscription-bootstrap",
        headers=context["owner_headers"],
        json={"provider_name": "cashfree"},
    )
    assert bootstrap.status_code == 200

    renewal_failed = client.post(
        "/v1/billing/webhooks/cashfree",
        json={
            "event_id": "cf_evt_grace_1",
            "event_type": "subscription.renewal_failed",
            "tenant_id": context["tenant_id"],
            "provider_customer_id": bootstrap.json()["provider_customer_id"],
            "provider_subscription_id": bootstrap.json()["provider_subscription_id"],
            "grace_until": "2026-04-20T18:00:00",
        },
    )
    assert renewal_failed.status_code == 200

    issue_during_grace = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/devices/{context['device_id']}/desktop-activation",
        headers=context["owner_headers"],
    )
    assert issue_during_grace.status_code == 402
    assert issue_during_grace.json()["detail"] == "Commercial grace only allows existing runtime devices. Ask the owner to update billing before activating a new device."

    unlock = client.post(
        "/v1/auth/store-desktop/unlock",
        json={
            "installation_id": context["installation_id"],
            "local_auth_token": redeem.json()["local_auth_token"],
        },
    )
    assert unlock.status_code == 200


def test_store_desktop_unlock_rejects_expired_grace_window():
    database_url = sqlite_test_database_url("store-desktop-activation-expired-grace")
    client = TestClient(
        create_app(
            database_url=database_url,
            bootstrap_database=True,
            korsenex_idp_mode="stub",
            platform_admin_emails=["admin@store.local"],
        )
    )

    context = _bootstrap_store_desktop_context(
        client,
        installation_id="store-runtime-expiredgrace1234",
        device_code="BLR-POS-GRACE-02",
    )

    activation_issue = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/devices/{context['device_id']}/desktop-activation",
        headers=context["owner_headers"],
    )
    assert activation_issue.status_code == 200

    redeem = client.post(
        "/v1/auth/store-desktop/activate",
        json={
            "installation_id": context["installation_id"],
            "activation_code": activation_issue.json()["activation_code"],
        },
    )
    assert redeem.status_code == 200

    bootstrap = client.post(
        f"/v1/tenants/{context['tenant_id']}/billing/subscription-bootstrap",
        headers=context["owner_headers"],
        json={"provider_name": "razorpay"},
    )
    assert bootstrap.status_code == 200

    renewal_failed = client.post(
        "/v1/billing/webhooks/razorpay",
        json={
            "event_id": "rp_evt_grace_expired_1",
            "event_type": "subscription.renewal_failed",
            "tenant_id": context["tenant_id"],
            "provider_customer_id": bootstrap.json()["provider_customer_id"],
            "provider_subscription_id": bootstrap.json()["provider_subscription_id"],
            "grace_until": "2026-04-10T18:00:00",
        },
    )
    assert renewal_failed.status_code == 200

    unlock = client.post(
        "/v1/auth/store-desktop/unlock",
        json={
            "installation_id": context["installation_id"],
            "local_auth_token": redeem.json()["local_auth_token"],
        },
    )

    assert unlock.status_code == 402
    assert unlock.json()["detail"] == "Commercial grace expired for this tenant. Ask the owner to update billing."


def test_store_desktop_activation_redeem_and_unlock_reject_suspended_commercial_access():
    database_url = sqlite_test_database_url("store-desktop-activation-suspended")
    client = TestClient(
        create_app(
            database_url=database_url,
            bootstrap_database=True,
            korsenex_idp_mode="stub",
            platform_admin_emails=["admin@store.local"],
        )
    )

    suspended_redeem_context = _bootstrap_store_desktop_context(
        client,
        installation_id="store-runtime-suspended-redeem1234",
        device_code="BLR-POS-SUSP-01",
    )

    activation_issue = client.post(
        f"/v1/tenants/{suspended_redeem_context['tenant_id']}/branches/{suspended_redeem_context['branch_id']}/devices/{suspended_redeem_context['device_id']}/desktop-activation",
        headers=suspended_redeem_context["owner_headers"],
    )
    assert activation_issue.status_code == 200

    suspend = client.post(
        f"/v1/platform/tenants/{suspended_redeem_context['tenant_id']}/billing/suspend",
        headers=suspended_redeem_context["admin_headers"],
        json={"reason": "Billing hold"},
    )
    assert suspend.status_code == 200

    redeem = client.post(
        "/v1/auth/store-desktop/activate",
        json={
            "installation_id": suspended_redeem_context["installation_id"],
            "activation_code": activation_issue.json()["activation_code"],
        },
    )
    assert redeem.status_code == 402
    assert redeem.json()["detail"] == "Commercial access is suspended for this tenant. Ask the owner to update billing."

    suspended_unlock_context = _bootstrap_store_desktop_context(
        client,
        installation_id="store-runtime-suspended-unlock1234",
        device_code="BLR-POS-SUSP-02",
    )

    activation_issue_for_unlock = client.post(
        f"/v1/tenants/{suspended_unlock_context['tenant_id']}/branches/{suspended_unlock_context['branch_id']}/devices/{suspended_unlock_context['device_id']}/desktop-activation",
        headers=suspended_unlock_context["owner_headers"],
    )
    assert activation_issue_for_unlock.status_code == 200

    redeem_for_unlock = client.post(
        "/v1/auth/store-desktop/activate",
        json={
            "installation_id": suspended_unlock_context["installation_id"],
            "activation_code": activation_issue_for_unlock.json()["activation_code"],
        },
    )
    assert redeem_for_unlock.status_code == 200

    suspend_unlock = client.post(
        f"/v1/platform/tenants/{suspended_unlock_context['tenant_id']}/billing/suspend",
        headers=suspended_unlock_context["admin_headers"],
        json={"reason": "Billing hold"},
    )
    assert suspend_unlock.status_code == 200

    unlock = client.post(
        "/v1/auth/store-desktop/unlock",
        json={
            "installation_id": suspended_unlock_context["installation_id"],
            "local_auth_token": redeem_for_unlock.json()["local_auth_token"],
        },
    )
    assert unlock.status_code == 402
    assert unlock.json()["detail"] == "Commercial access is suspended for this tenant. Ask the owner to update billing."
