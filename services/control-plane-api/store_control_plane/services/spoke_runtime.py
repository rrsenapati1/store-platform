from __future__ import annotations

from datetime import timedelta
import hashlib
import secrets

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories import AuditRepository, TenantRepository, WorkforceRepository
from ..utils import utc_now
from .sync_runtime_auth import SyncDeviceContext

SPOKE_RUNTIME_ACTIVATION_TTL_MINUTES = 15
SUPPORTED_PAIRING_MODES = {"approval_code", "qr"}
SUPPORTED_SPOKE_RUNTIME_PROFILES = {
    "desktop_spoke",
    "mobile_store_spoke",
    "inventory_tablet_spoke",
    "customer_display",
}


def normalize_spoke_runtime_activation_code(code: str) -> str:
    normalized = "".join(character for character in code.upper().strip() if character.isalnum())
    if not normalized:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Activation code is required")
    return normalized


def hash_spoke_runtime_activation_code(code: str) -> str:
    normalized = normalize_spoke_runtime_activation_code(code)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def build_spoke_runtime_activation_code() -> str:
    token = secrets.token_hex(6).upper()
    return f"{token[:4]}-{token[4:8]}-{token[8:12]}"


class SpokeRuntimeService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._tenant_repo = TenantRepository(session)
        self._workforce_repo = WorkforceRepository(session)
        self._audit_repo = AuditRepository(session)

    async def issue_activation(
        self,
        *,
        device: SyncDeviceContext,
        runtime_profile: str,
        pairing_mode: str,
    ) -> dict[str, object]:
        await self._assert_branch_exists(tenant_id=device.tenant_id, branch_id=device.branch_id)
        self._assert_supported_runtime_profile(runtime_profile)
        self._assert_supported_pairing_mode(pairing_mode)
        if device.runtime_profile != "branch_hub":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Device is not a branch hub")

        await self._workforce_repo.supersede_spoke_runtime_activations(
            hub_device_id=device.device_id,
            runtime_profile=runtime_profile,
        )
        activation_code = build_spoke_runtime_activation_code()
        activation = await self._workforce_repo.create_spoke_runtime_activation(
            tenant_id=device.tenant_id,
            branch_id=device.branch_id,
            hub_device_id=device.device_id,
            activation_code_hash=hash_spoke_runtime_activation_code(activation_code),
            pairing_mode=pairing_mode,
            runtime_profile=runtime_profile,
            expires_at=utc_now() + timedelta(minutes=SPOKE_RUNTIME_ACTIVATION_TTL_MINUTES),
        )
        payload = {
            "pairing_mode": pairing_mode,
            "runtime_profile": runtime_profile,
            "hub_device_id": device.device_id,
            "expires_at": activation.expires_at.isoformat(),
        }
        await self._audit_repo.record(
            tenant_id=device.tenant_id,
            branch_id=device.branch_id,
            actor_user_id=None,
            action="spoke_runtime.activation.issued",
            entity_type="spoke_runtime_activation",
            entity_id=activation.id,
            payload=payload,
        )
        await self._session.commit()
        return {
            "activation_code": activation_code,
            "pairing_mode": pairing_mode,
            "runtime_profile": runtime_profile,
            "hub_device_id": device.device_id,
            "expires_at": activation.expires_at.isoformat(),
        }

    async def _assert_branch_exists(self, *, tenant_id: str, branch_id: str) -> None:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")

    def _assert_supported_pairing_mode(self, pairing_mode: str) -> None:
        if pairing_mode not in SUPPORTED_PAIRING_MODES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported spoke pairing mode")

    def _assert_supported_runtime_profile(self, runtime_profile: str) -> None:
        if runtime_profile not in SUPPORTED_SPOKE_RUNTIME_PROFILES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported spoke runtime profile")
