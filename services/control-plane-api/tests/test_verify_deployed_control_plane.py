from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_verify_script_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "verify_deployed_control_plane.py"
    spec = importlib.util.spec_from_file_location("verify_deployed_control_plane_script", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_verify_deployed_control_plane_checks_health_authority_and_optional_auth() -> None:
    module = _load_verify_script_module()
    seen: list[tuple[str, dict[str, str] | None]] = []

    def fake_fetch_json(url: str, *, headers: dict[str, str] | None = None) -> dict[str, object]:
        seen.append((url, headers))
        if url.endswith("/v1/system/health"):
            return {
                "status": "ok",
                "environment": "staging",
                "public_base_url": "https://control.staging.store.korsenex.com",
                "release_version": "2026.04.14-staging",
                "database": {"status": "ok"},
                "operations_worker": {"configured": True},
            }
        if url.endswith("/v1/system/authority-boundary"):
            return {
                "control_plane_service": "store-control-plane",
                "legacy_service": "legacy-retail-api",
                "cutover_phase": "post-cutover",
                "legacy_write_mode": "cutover",
                "migrated_domains": ["onboarding"],
                "legacy_remaining_domains": [],
                "shutdown_criteria": [],
                "shutdown_steps": [],
            }
        if url.endswith("/v1/auth/me"):
            return {"email": "ops@store.korsenex.com"}
        raise AssertionError(f"unexpected url {url}")

    result = module.verify_deployed_control_plane(
        base_url="https://control.staging.store.korsenex.com",
        expected_environment="staging",
        expected_release_version="2026.04.14-staging",
        bearer_token="secret-token",
        fetch_json=fake_fetch_json,
    )

    assert result["status"] == "ok"
    assert result["environment"] == "staging"
    assert result["authenticated_actor_email"] == "ops@store.korsenex.com"
    assert seen[2] == (
        "https://control.staging.store.korsenex.com/v1/auth/me",
        {"authorization": "Bearer secret-token"},
    )
