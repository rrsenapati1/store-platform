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


def test_settings_normalize_deployment_and_object_storage_fields(monkeypatch) -> None:
    monkeypatch.setenv("STORE_CONTROL_PLANE_DEPLOYMENT_ENVIRONMENT", " Staging ")
    monkeypatch.setenv("STORE_CONTROL_PLANE_PUBLIC_BASE_URL", " https://control.staging.store.korsenex.com/ ")
    monkeypatch.setenv("STORE_CONTROL_PLANE_RELEASE_VERSION", " 2026.04.14 ")
    monkeypatch.setenv("STORE_CONTROL_PLANE_OBJECT_STORAGE_BUCKET", " store-stage-artifacts ")
    monkeypatch.setenv("STORE_CONTROL_PLANE_OBJECT_STORAGE_PREFIX", " /store/staging/control-plane/ ")
    monkeypatch.setenv("STORE_CONTROL_PLANE_BACKUP_ARTIFACT_PREFIX", " /postgres/backups/ ")
    monkeypatch.setenv("STORE_CONTROL_PLANE_DESKTOP_RELEASE_ARTIFACT_PREFIX", " /desktop/releases/ ")
    monkeypatch.setenv("STORE_CONTROL_PLANE_BACKUP_RETENTION_DAYS", "30")

    settings = Settings()

    assert settings.deployment_environment == "staging"
    assert settings.public_base_url == "https://control.staging.store.korsenex.com"
    assert settings.release_version == "2026.04.14"
    assert settings.object_storage_bucket == "store-stage-artifacts"
    assert settings.object_storage_prefix == "store/staging/control-plane"
    assert settings.backup_artifact_prefix == "postgres/backups"
    assert settings.desktop_release_artifact_prefix == "desktop/releases"
    assert settings.backup_retention_days == 30


def test_build_settings_accepts_deployment_overrides() -> None:
    settings = build_settings(
        deployment_environment=" Prod ",
        public_base_url=" https://control.store.korsenex.com/ ",
        release_version=" 1.2.3 ",
        object_storage_bucket=" store-prod-artifacts ",
        object_storage_prefix=" /store/prod/control-plane/ ",
    )

    assert settings.deployment_environment == "prod"
    assert settings.public_base_url == "https://control.store.korsenex.com"
    assert settings.release_version == "1.2.3"
    assert settings.object_storage_bucket == "store-prod-artifacts"
    assert settings.object_storage_prefix == "store/prod/control-plane"
