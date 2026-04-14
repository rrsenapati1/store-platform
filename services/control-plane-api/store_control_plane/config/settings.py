from __future__ import annotations

from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Store Control Plane API"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:54321/store_control_plane"
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
            if normalized in {"stub"}:
                return normalized
        return value


def build_settings(
    *,
    database_url: str | None = None,
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
) -> Settings:
    overrides: dict[str, object] = {}
    if database_url is not None:
        overrides["database_url"] = database_url
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
    return Settings(**overrides)
