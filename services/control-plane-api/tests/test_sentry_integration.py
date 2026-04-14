from __future__ import annotations

from fastapi.testclient import TestClient

from conftest import sqlite_test_database_url
from store_control_plane.config import build_settings
from store_control_plane.main import create_app
from store_control_plane.services.auth import ActorContext, ActorMembership
from store_control_plane.sentry import bind_actor_scope, initialize_sentry


class _FakeSentrySdk:
    def __init__(self) -> None:
        self.init_calls: list[dict[str, object]] = []
        self.user: dict[str, object] | None = None
        self.tags: dict[str, object] = {}

    def init(self, **kwargs) -> None:
        self.init_calls.append(kwargs)

    def set_user(self, payload: dict[str, object] | None) -> None:
        self.user = payload

    def set_tag(self, key: str, value: object) -> None:
        self.tags[key] = value


def _stub_token(*, subject: str, email: str, name: str) -> str:
    return f"stub:sub={subject};email={email};name={name}"


def test_initialize_sentry_invokes_sdk_and_scrubs_sensitive_event_fields() -> None:
    fake_sdk = _FakeSentrySdk()
    settings = build_settings(
        database_url=sqlite_test_database_url("sentry-init"),
        sentry_dsn="https://public@example.ingest.sentry.io/1",
        sentry_traces_sample_rate=0.25,
        release_version="2026.04.15-1",
        deployment_environment="staging",
    )

    initialized = initialize_sentry(settings, sentry_sdk=fake_sdk)

    assert initialized is True
    assert len(fake_sdk.init_calls) == 1
    init_call = fake_sdk.init_calls[0]
    assert init_call["dsn"] == "https://public@example.ingest.sentry.io/1"
    assert init_call["environment"] == "staging"
    assert init_call["release"] == "2026.04.15-1"
    assert init_call["traces_sample_rate"] == 0.25
    before_send = init_call["before_send"]
    assert callable(before_send)
    scrubbed = before_send(
        {
            "request": {
                "headers": {"Authorization": "Bearer secret-token"},
                "data": {"password": "hunter2", "device_id": "device-1"},
            },
            "contexts": {"runtime": {"sync_secret": "sync-secret"}},
            "extra": {"taxpayer_password": "gst-secret"},
        },
        None,
    )
    assert scrubbed["request"]["headers"]["Authorization"] == "[REDACTED]"
    assert scrubbed["request"]["data"]["password"] == "[REDACTED]"
    assert scrubbed["request"]["data"]["device_id"] == "device-1"
    assert scrubbed["contexts"]["runtime"]["sync_secret"] == "[REDACTED]"
    assert scrubbed["extra"]["taxpayer_password"] == "[REDACTED]"


def test_bind_actor_scope_sets_sentry_user_and_tags() -> None:
    fake_sdk = _FakeSentrySdk()
    actor = ActorContext(
        user_id="user-1",
        email="owner@store.local",
        full_name="Owner User",
        is_platform_admin=False,
        tenant_memberships=[ActorMembership(tenant_id="tenant-1", role_name="tenant_owner", status="ACTIVE")],
        branch_memberships=[ActorMembership(tenant_id="tenant-1", branch_id="branch-1", role_name="store_manager", status="ACTIVE")],
    )

    bind_actor_scope(actor, sentry_sdk=fake_sdk)

    assert fake_sdk.user == {"id": "user-1", "email": "owner@store.local", "username": "Owner User"}
    assert fake_sdk.tags["actor_user_id"] == "user-1"
    assert fake_sdk.tags["tenant_ids"] == "tenant-1"
    assert fake_sdk.tags["branch_ids"] == "branch-1"
    assert fake_sdk.tags["is_platform_admin"] == "false"


def test_me_route_binds_actor_scope(monkeypatch) -> None:
    client = TestClient(
        create_app(
            database_url=sqlite_test_database_url("sentry-actor-scope"),
            bootstrap_database=True,
            korsenex_idp_mode="stub",
        )
    )

    captured: dict[str, str] = {}

    def _capture(actor: ActorContext) -> None:
        captured["user_id"] = actor.user_id
        captured["email"] = actor.email

    monkeypatch.setattr("store_control_plane.dependencies.auth.bind_actor_scope", _capture)

    session = client.post(
        "/v1/auth/oidc/exchange",
        json={"token": _stub_token(subject="owner-1", email="owner@store.local", name="Owner User")},
    )
    assert session.status_code == 200

    response = client.get("/v1/auth/me", headers={"authorization": f"Bearer {session.json()['access_token']}"})

    assert response.status_code == 200
    assert captured == {"user_id": response.json()["user_id"], "email": "owner@store.local"}
