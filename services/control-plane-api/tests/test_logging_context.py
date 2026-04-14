from __future__ import annotations

from fastapi.testclient import TestClient

from conftest import sqlite_test_database_url
from store_control_plane.logging import scrub_sensitive_mapping
from store_control_plane.main import create_app


def test_request_id_is_generated_and_echoed_back() -> None:
    client = TestClient(
        create_app(
            database_url=sqlite_test_database_url("request-id-generated"),
            bootstrap_database=True,
            korsenex_idp_mode="stub",
        )
    )

    response = client.get("/v1/system/health")

    assert response.status_code == 200
    assert response.headers["x-request-id"]


def test_request_id_preserves_client_supplied_header() -> None:
    client = TestClient(
        create_app(
            database_url=sqlite_test_database_url("request-id-preserved"),
            bootstrap_database=True,
            korsenex_idp_mode="stub",
        )
    )

    response = client.get("/v1/system/health", headers={"x-request-id": "req-from-client-123"})

    assert response.status_code == 200
    assert response.headers["x-request-id"] == "req-from-client-123"


def test_scrub_sensitive_mapping_redacts_tokens_passwords_and_secrets() -> None:
    payload = {
        "authorization": "Bearer very-secret-token",
        "password": "hunter2",
        "nested": {
            "sync_secret": "sync-secret",
            "device_id": "device-1",
        },
        "list": [{"taxpayer_password": "abc"}, {"api_key": "allowed"}],
    }

    scrubbed = scrub_sensitive_mapping(payload)

    assert scrubbed["authorization"] == "[REDACTED]"
    assert scrubbed["password"] == "[REDACTED]"
    assert scrubbed["nested"]["sync_secret"] == "[REDACTED]"
    assert scrubbed["nested"]["device_id"] == "device-1"
    assert scrubbed["list"][0]["taxpayer_password"] == "[REDACTED]"
