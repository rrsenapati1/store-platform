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
