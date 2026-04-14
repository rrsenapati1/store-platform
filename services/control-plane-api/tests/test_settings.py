from __future__ import annotations

from store_control_plane.config.settings import Settings, build_settings


def test_settings_accept_comma_separated_env_values(monkeypatch) -> None:
    monkeypatch.setenv("STORE_CONTROL_PLANE_PLATFORM_ADMIN_EMAILS", "admin@store.local, ops@store.local")
    monkeypatch.setenv("STORE_CONTROL_PLANE_KORSENEX_IDP_ALGORITHMS", "RS256,ES256")

    settings = Settings()

    assert settings.platform_admin_emails == ["admin@store.local", "ops@store.local"]
    assert settings.korsenex_idp_algorithms == ["RS256", "ES256"]


def test_build_settings_normalizes_platform_admin_emails() -> None:
    settings = build_settings(platform_admin_emails=["Admin@Store.local", "ops@store.local"])

    assert settings.platform_admin_emails == ["admin@store.local", "ops@store.local"]
