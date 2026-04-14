from __future__ import annotations

from fastapi.testclient import TestClient

from conftest import sqlite_test_database_url
from store_control_plane.main import create_app


def test_secure_headers_are_applied_to_health_response() -> None:
    client = TestClient(
        create_app(
            database_url=sqlite_test_database_url("security-headers"),
            bootstrap_database=True,
            korsenex_idp_mode="stub",
            deployment_environment="prod",
            secure_headers_enabled=True,
            secure_headers_hsts_enabled=True,
        )
    )

    response = client.get("/v1/system/health")

    assert response.status_code == 200
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
    assert "max-age=" in response.headers["strict-transport-security"]
