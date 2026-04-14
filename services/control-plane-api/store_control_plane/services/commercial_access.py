from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories import CommerceRepository
from ..utils import utc_now

COMMERCIAL_SUSPENDED_DETAIL = "Commercial access is suspended for this tenant. Ask the owner to update billing."
COMMERCIAL_GRACE_EXPIRED_DETAIL = "Commercial grace expired for this tenant. Ask the owner to update billing."
COMMERCIAL_GRACE_ACTIVATION_DETAIL = (
    "Commercial grace only allows existing runtime devices. Ask the owner to update billing before activating a new device."
)
COMMERCIAL_DESKTOP_RUNTIME_DISABLED_DETAIL = "The active commercial plan does not include desktop runtime access."
COMMERCIAL_OFFLINE_CONTINUITY_DISABLED_DETAIL = "The active commercial plan does not include offline continuity."


@dataclass(slots=True)
class RuntimeCommercialAccess:
    lifecycle_status: str | None
    grace_until: object | None
    suspend_at: object | None
    offline_runtime_hours: int | None
    feature_flags: dict[str, object]


class CommercialAccessService:
    def __init__(self, session: AsyncSession):
        self._commerce_repo = CommerceRepository(session)

    async def get_runtime_access(self, *, tenant_id: str) -> RuntimeCommercialAccess | None:
        entitlement = await self._commerce_repo.get_tenant_entitlement(tenant_id=tenant_id)
        if entitlement is None:
            return None
        return RuntimeCommercialAccess(
            lifecycle_status=entitlement.lifecycle_status,
            grace_until=entitlement.grace_until,
            suspend_at=entitlement.suspend_at,
            offline_runtime_hours=entitlement.offline_runtime_hours,
            feature_flags=dict(entitlement.feature_flags),
        )

    async def assert_runtime_session_allowed(self, *, tenant_id: str) -> RuntimeCommercialAccess | None:
        access = await self.get_runtime_access(tenant_id=tenant_id)
        self._assert_lifecycle(access=access, allow_grace=True)
        self._assert_feature_flag(
            access=access,
            feature_name="desktop_runtime",
            detail=COMMERCIAL_DESKTOP_RUNTIME_DISABLED_DETAIL,
        )
        return access

    async def assert_runtime_activation_allowed(self, *, tenant_id: str) -> RuntimeCommercialAccess | None:
        access = await self.get_runtime_access(tenant_id=tenant_id)
        self._assert_lifecycle(access=access, allow_grace=False)
        self._assert_feature_flag(
            access=access,
            feature_name="desktop_runtime",
            detail=COMMERCIAL_DESKTOP_RUNTIME_DISABLED_DETAIL,
        )
        return access

    async def assert_offline_continuity_allowed(self, *, tenant_id: str) -> RuntimeCommercialAccess | None:
        access = await self.get_runtime_access(tenant_id=tenant_id)
        self._assert_lifecycle(access=access, allow_grace=True)
        self._assert_feature_flag(
            access=access,
            feature_name="offline_continuity",
            detail=COMMERCIAL_OFFLINE_CONTINUITY_DISABLED_DETAIL,
        )
        return access

    @staticmethod
    def resolve_offline_runtime_hours(
        *,
        access: RuntimeCommercialAccess | None,
        fallback_hours: int,
    ) -> int:
        if access is None or access.offline_runtime_hours is None:
            return fallback_hours
        if access.offline_runtime_hours <= 0:
            return 0
        return min(fallback_hours, access.offline_runtime_hours)

    @staticmethod
    def _assert_feature_flag(
        *,
        access: RuntimeCommercialAccess | None,
        feature_name: str,
        detail: str,
    ) -> None:
        if access is None:
            return
        if feature_name not in access.feature_flags:
            return
        if bool(access.feature_flags.get(feature_name)):
            return
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=detail)

    @staticmethod
    def _assert_lifecycle(*, access: RuntimeCommercialAccess | None, allow_grace: bool) -> None:
        if access is None or access.lifecycle_status is None:
            return
        now = utc_now()
        lifecycle_status = access.lifecycle_status.upper()
        if lifecycle_status == "SUSPENDED":
            raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=COMMERCIAL_SUSPENDED_DETAIL)
        if lifecycle_status == "GRACE":
            grace_deadline = access.grace_until or access.suspend_at
            if grace_deadline is not None and now > grace_deadline:
                raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=COMMERCIAL_GRACE_EXPIRED_DETAIL)
            if not allow_grace:
                raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=COMMERCIAL_GRACE_ACTIVATION_DETAIL)
            return
        if lifecycle_status == "TRIALING" and access.suspend_at is not None and now > access.suspend_at:
            raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=COMMERCIAL_GRACE_EXPIRED_DETAIL)
