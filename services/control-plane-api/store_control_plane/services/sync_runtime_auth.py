from __future__ import annotations

import hashlib
from dataclasses import dataclass
from secrets import compare_digest

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories import WorkforceRepository


def hash_sync_access_secret(secret: str) -> str:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


@dataclass(slots=True)
class SyncDeviceContext:
    device_id: str
    tenant_id: str
    branch_id: str
    device_code: str
    device_name: str
    session_surface: str
    runtime_profile: str


class SyncRuntimeAuthService:
    def __init__(self, session: AsyncSession):
        self._workforce_repo = WorkforceRepository(session)

    async def authenticate_hub_device(self, *, device_id: str, device_secret: str) -> SyncDeviceContext:
        device = await self._workforce_repo.get_device_registration_by_id(device_id=device_id)
        if device is None or device.status != "ACTIVE":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid device credentials")
        if not device.is_branch_hub:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Device is not a branch hub")
        if not device.sync_secret_hash:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid device credentials")
        if not compare_digest(device.sync_secret_hash, hash_sync_access_secret(device_secret)):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid device credentials")
        return SyncDeviceContext(
            device_id=device.id,
            tenant_id=device.tenant_id,
            branch_id=device.branch_id,
            device_code=device.device_code,
            device_name=device.device_name,
            session_surface=device.session_surface,
            runtime_profile=device.runtime_profile,
        )
