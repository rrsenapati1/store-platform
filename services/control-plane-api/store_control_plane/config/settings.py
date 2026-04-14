from __future__ import annotations

from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Store Control Plane API"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:54321/store_control_plane"
    deployment_environment: str = "dev"
    public_base_url: str = "http://127.0.0.1:8000"
    release_version: str = "dev"
    korsenex_idp_mode: str = "jwks"
    korsenex_idp_jwks_url: str | None = None
    korsenex_idp_issuer: str | None = None
    korsenex_idp_audience: str | None = None
    korsenex_idp_algorithms: Annotated[list[str], NoDecode] = Field(default_factory=lambda: ["RS256"])
    korsenex_idp_jwks_timeout_seconds: float = 5.0
    korsenex_idp_jwks_cache_seconds: int = 300
    session_ttl_minutes: int = 720
    legacy_write_mode: str = "shadow"
    platform_admin_emails: Annotated[list[str], NoDecode] = Field(default_factory=list)
    operations_worker_poll_seconds: int = 5
    operations_worker_batch_size: int = 25
    operations_worker_lease_seconds: int = 60
    operations_job_retry_delay_seconds: int = 60
    operations_job_retention_hours: int = 168
    compliance_secret_key: str | None = None
    compliance_irp_mode: str = "disabled"
    compliance_irp_client_id: str | None = None
    compliance_irp_client_secret: str | None = None
    compliance_irp_auth_url: str | None = None
    compliance_irp_generate_irn_url: str | None = None
    compliance_irp_get_by_document_url: str | None = None
    compliance_irp_get_gstin_details_url: str | None = None
    compliance_irp_public_key_pem: str | None = None
    compliance_irp_timeout_seconds: float = 10.0
    subscription_provider_mode: str = "stub"
    subscription_checkout_base_url: str = "https://payments.store.local"
    cashfree_webhook_secret: str | None = None
    razorpay_webhook_secret: str | None = None
    object_storage_endpoint_url: str | None = None
    object_storage_region: str | None = None
    object_storage_bucket: str | None = None
    object_storage_prefix: str = "store-control-plane/dev"
    object_storage_access_key_id: str | None = None
    object_storage_secret_access_key: str | None = None
    object_storage_session_token: str | None = None
    object_storage_force_path_style: bool = False
    backup_artifact_prefix: str = "postgres-backups"
    restore_artifact_prefix: str = "restore-drills"
    desktop_release_artifact_prefix: str = "desktop-releases"
    backup_retention_days: int = 14

    model_config = SettingsConfigDict(
        env_prefix="STORE_CONTROL_PLANE_",
        env_file=".env",
        extra="ignore",
    )

    @field_validator("platform_admin_emails", mode="before")
    @classmethod
    def _normalize_platform_admin_emails(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip().lower() for item in value.split(",") if item.strip()]
        return value

    @field_validator(
        "deployment_environment",
        "public_base_url",
        "release_version",
        "korsenex_idp_jwks_url",
        "korsenex_idp_issuer",
        "korsenex_idp_audience",
        "compliance_irp_auth_url",
        "compliance_irp_generate_irn_url",
        "compliance_irp_get_by_document_url",
        "compliance_irp_get_gstin_details_url",
        "subscription_checkout_base_url",
        "object_storage_endpoint_url",
        "object_storage_region",
        "object_storage_bucket",
        "object_storage_access_key_id",
        "object_storage_secret_access_key",
        "object_storage_session_token",
        mode="before",
    )
    @classmethod
    def _normalize_trimmed_strings(cls, value: object) -> object:
        if isinstance(value, str):
            normalized = value.strip()
            return normalized or None
        return value

    @field_validator("public_base_url", "korsenex_idp_jwks_url", "korsenex_idp_issuer", "subscription_checkout_base_url", "object_storage_endpoint_url", mode="after")
    @classmethod
    def _normalize_urls(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.rstrip("/")

    @field_validator(
        "object_storage_prefix",
        "backup_artifact_prefix",
        "restore_artifact_prefix",
        "desktop_release_artifact_prefix",
        mode="before",
    )
    @classmethod
    def _normalize_storage_prefixes(cls, value: object) -> object:
        if isinstance(value, str):
            normalized = value.strip().strip("/")
            return normalized or None
        return value

    @field_validator("deployment_environment", mode="after")
    @classmethod
    def _normalize_deployment_environment(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized in {"dev", "staging", "prod"}:
            return normalized
        return value

    @field_validator("korsenex_idp_algorithms", mode="before")
    @classmethod
    def _normalize_algorithms(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("legacy_write_mode", mode="before")
    @classmethod
    def _normalize_legacy_write_mode(cls, value: object) -> object:
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"shadow", "cutover"}:
                return normalized
        return value

    @field_validator("compliance_irp_mode", mode="before")
    @classmethod
    def _normalize_compliance_irp_mode(cls, value: object) -> object:
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"disabled", "stub", "iris_direct"}:
                return normalized
        return value

    @field_validator("subscription_provider_mode", mode="before")
    @classmethod
    def _normalize_subscription_provider_mode(cls, value: object) -> object:
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"stub", "cashfree", "razorpay"}:
                return normalized
        return value


def build_settings(
    *,
    database_url: str | None = None,
    deployment_environment: str | None = None,
    public_base_url: str | None = None,
    release_version: str | None = None,
    korsenex_idp_mode: str | None = None,
    korsenex_idp_jwks_url: str | None = None,
    korsenex_idp_issuer: str | None = None,
    korsenex_idp_audience: str | None = None,
    legacy_write_mode: str | None = None,
    platform_admin_emails: list[str] | None = None,
    compliance_secret_key: str | None = None,
    compliance_irp_mode: str | None = None,
    subscription_provider_mode: str | None = None,
    subscription_checkout_base_url: str | None = None,
    object_storage_bucket: str | None = None,
    object_storage_prefix: str | None = None,
) -> Settings:
    overrides: dict[str, object] = {}
    if database_url is not None:
        overrides["database_url"] = database_url
    if deployment_environment is not None:
        overrides["deployment_environment"] = deployment_environment
    if public_base_url is not None:
        overrides["public_base_url"] = public_base_url
    if release_version is not None:
        overrides["release_version"] = release_version
    if korsenex_idp_mode is not None:
        overrides["korsenex_idp_mode"] = korsenex_idp_mode
    if korsenex_idp_jwks_url is not None:
        overrides["korsenex_idp_jwks_url"] = korsenex_idp_jwks_url
    if korsenex_idp_issuer is not None:
        overrides["korsenex_idp_issuer"] = korsenex_idp_issuer
    if korsenex_idp_audience is not None:
        overrides["korsenex_idp_audience"] = korsenex_idp_audience
    if legacy_write_mode is not None:
        overrides["legacy_write_mode"] = legacy_write_mode
    if platform_admin_emails is not None:
        overrides["platform_admin_emails"] = [item.lower() for item in platform_admin_emails]
    if compliance_secret_key is not None:
        overrides["compliance_secret_key"] = compliance_secret_key
    if compliance_irp_mode is not None:
        overrides["compliance_irp_mode"] = compliance_irp_mode
    if subscription_provider_mode is not None:
        overrides["subscription_provider_mode"] = subscription_provider_mode
    if subscription_checkout_base_url is not None:
        overrides["subscription_checkout_base_url"] = subscription_checkout_base_url
    if object_storage_bucket is not None:
        overrides["object_storage_bucket"] = object_storage_bucket
    if object_storage_prefix is not None:
        overrides["object_storage_prefix"] = object_storage_prefix
    return Settings(**overrides)
