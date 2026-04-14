from fastapi.testclient import TestClient

from store_control_plane.main import create_app
from conftest import sqlite_test_database_url


def _stub_token(*, subject: str, email: str, name: str) -> str:
    return f"stub:sub={subject};email={email};name={name}"


def test_oidc_exchange_creates_platform_session_and_actor_context():
    database_url = sqlite_test_database_url("control-plane")
    client = TestClient(
        create_app(
            database_url=database_url,
            bootstrap_database=True,
            korsenex_idp_mode="stub",
            platform_admin_emails=["admin@store.local"],
        )
    )

    exchange = client.post(
        "/v1/auth/oidc/exchange",
        json={"token": _stub_token(subject="platform-admin-1", email="admin@store.local", name="Platform Admin")},
    )

    assert exchange.status_code == 200
    assert exchange.json()["token_type"] == "Bearer"

    me = client.get(
        "/v1/auth/me",
        headers={"authorization": f"Bearer {exchange.json()['access_token']}"},
    )

    assert me.status_code == 200
    assert me.json()["email"] == "admin@store.local"
    assert me.json()["full_name"] == "Platform Admin"
    assert me.json()["is_platform_admin"] is True
    assert me.json()["tenant_memberships"] == []
    assert me.json()["branch_memberships"] == []
