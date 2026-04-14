from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from store_control_plane.main import create_app


def test_authority_boundary_manifest_publishes_cutover_contract():
    tmp_root = Path(__file__).resolve().parents[1] / ".tmp-tests"
    tmp_root.mkdir(parents=True, exist_ok=True)
    database_url = f"sqlite+aiosqlite:///{(tmp_root / f'authority-boundary-{uuid4().hex}.db').as_posix()}"
    client = TestClient(
        create_app(
            database_url=database_url,
            bootstrap_database=True,
            korsenex_idp_mode="stub",
            legacy_write_mode="cutover",
            platform_admin_emails=["admin@store.local"],
        )
    )

    response = client.get("/v1/system/authority-boundary")

    assert response.status_code == 200
    assert response.json()["legacy_write_mode"] == "cutover"
    assert response.json()["migrated_domains"] == [
        "onboarding",
        "workforce",
        "catalog",
        "barcode_foundation",
        "purchasing",
        "inventory",
        "batch_tracking",
        "billing",
        "compliance_exports",
        "customer_reporting",
        "supplier_reporting",
        "runtime_print",
        "sync_runtime",
    ]
    assert response.json()["legacy_remaining_domains"] == []
    assert response.json()["shutdown_criteria"] == [
        "Control-plane verification script passes on Postgres",
        "Migrated writes are blocked on the legacy retail API",
        "Legacy-only domain list is empty",
    ]
