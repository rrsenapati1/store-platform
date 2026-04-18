from __future__ import annotations

from fastapi.testclient import TestClient

from conftest import sqlite_test_database_url
from store_control_plane.main import create_app


def test_system_health_reports_environment_release_and_database_posture() -> None:
    database_url = sqlite_test_database_url("system-health")
    client = TestClient(
        create_app(
            database_url=database_url,
            bootstrap_database=True,
            korsenex_idp_mode="stub",
            deployment_environment="staging",
            public_base_url="https://control.staging.store.korsenex.com",
            release_version="2026.04.14-staging",
        )
    )

    response = client.get("/v1/system/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["environment"] == "staging"
    assert response.json()["public_base_url"] == "https://control.staging.store.korsenex.com"
    assert response.json()["release_version"] == "2026.04.14-staging"
    assert response.json()["database"]["status"] == "ok"
    assert response.json()["operations_worker"]["configured"] is True


def test_system_security_controls_report_effective_header_and_rate_limit_posture() -> None:
    database_url = sqlite_test_database_url("system-security-controls")
    client = TestClient(
        create_app(
            database_url=database_url,
            bootstrap_database=True,
            korsenex_idp_mode="stub",
            secure_headers_enabled=True,
            secure_headers_hsts_enabled=True,
            secure_headers_csp="default-src 'self'; frame-ancestors 'none'",
            rate_limit_window_seconds=90,
            rate_limit_auth_requests=8,
            rate_limit_activation_requests=5,
            rate_limit_webhook_requests=21,
        )
    )

    response = client.get("/v1/system/security-controls")

    assert response.status_code == 200
    payload = response.json()
    assert payload["secure_headers_enabled"] is True
    assert payload["secure_headers_hsts_enabled"] is True
    assert payload["secure_headers_csp"] == "default-src 'self'; frame-ancestors 'none'"
    assert payload["rate_limits"] == {
        "window_seconds": 90,
        "auth_requests": 8,
        "activation_requests": 5,
        "webhook_requests": 21,
    }
