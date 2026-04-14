from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import DeviceClaim, DeviceRegistration, StaffProfile
from ..utils import new_id


class WorkforceRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_staff_profile_by_id(self, *, tenant_id: str, staff_profile_id: str) -> StaffProfile | None:
        statement = select(StaffProfile).where(
            StaffProfile.id == staff_profile_id,
            StaffProfile.tenant_id == tenant_id,
        )
        return await self._session.scalar(statement)

    async def get_staff_profile_by_email(self, *, tenant_id: str, email: str) -> StaffProfile | None:
        statement = select(StaffProfile).where(
            StaffProfile.tenant_id == tenant_id,
            StaffProfile.email == email.lower(),
        )
        return await self._session.scalar(statement)

    async def upsert_staff_profile(
        self,
        *,
        tenant_id: str,
        email: str,
        full_name: str,
        phone_number: str | None = None,
        primary_branch_id: str | None = None,
        user_id: str | None = None,
    ) -> StaffProfile:
        profile = await self.get_staff_profile_by_email(tenant_id=tenant_id, email=email)
        if profile is None:
            profile = StaffProfile(
                id=new_id(),
                tenant_id=tenant_id,
                email=email.lower(),
                full_name=full_name,
                phone_number=phone_number,
                primary_branch_id=primary_branch_id,
                user_id=user_id,
                status="ACTIVE",
            )
            self._session.add(profile)
        else:
            profile.full_name = full_name
            if phone_number is not None:
                profile.phone_number = phone_number
            if primary_branch_id is not None:
                profile.primary_branch_id = primary_branch_id
            if user_id is not None:
                profile.user_id = user_id
            profile.status = "ACTIVE"
        await self._session.flush()
        return profile

    async def bind_profiles_for_user(self, *, email: str, user_id: str, full_name: str) -> None:
        statement = select(StaffProfile).where(StaffProfile.email == email.lower())
        for profile in (await self._session.scalars(statement)).all():
            profile.user_id = user_id
            profile.full_name = full_name
            profile.status = "ACTIVE"
        await self._session.flush()

    async def list_staff_profiles(self, *, tenant_id: str) -> list[StaffProfile]:
        statement = (
            select(StaffProfile)
            .where(StaffProfile.tenant_id == tenant_id)
            .order_by(StaffProfile.created_at.asc(), StaffProfile.id.asc())
        )
        return list((await self._session.scalars(statement)).all())

    async def create_device_registration(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        assigned_staff_profile_id: str | None,
        installation_id: str | None,
        device_name: str,
        device_code: str,
        session_surface: str,
        is_branch_hub: bool = False,
        sync_secret_hash: str | None = None,
        sync_secret_issued_at=None,
    ) -> DeviceRegistration:
        device = DeviceRegistration(
            id=new_id(),
            tenant_id=tenant_id,
            branch_id=branch_id,
            assigned_staff_profile_id=assigned_staff_profile_id,
            installation_id=installation_id,
            device_name=device_name,
            device_code=device_code,
            session_surface=session_surface,
            is_branch_hub=is_branch_hub,
            sync_secret_hash=sync_secret_hash,
            sync_secret_issued_at=sync_secret_issued_at,
            status="ACTIVE",
        )
        self._session.add(device)
        await self._session.flush()
        return device

    async def get_device_registration_by_code(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        device_code: str,
    ) -> DeviceRegistration | None:
        statement = select(DeviceRegistration).where(
            DeviceRegistration.tenant_id == tenant_id,
            DeviceRegistration.branch_id == branch_id,
            DeviceRegistration.device_code == device_code,
        )
        return await self._session.scalar(statement)

    async def get_device_registration_by_installation_id(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        installation_id: str,
    ) -> DeviceRegistration | None:
        statement = select(DeviceRegistration).where(
            DeviceRegistration.tenant_id == tenant_id,
            DeviceRegistration.branch_id == branch_id,
            DeviceRegistration.installation_id == installation_id,
        )
        return await self._session.scalar(statement)

    async def list_branch_devices(self, *, tenant_id: str, branch_id: str) -> list[DeviceRegistration]:
        statement = (
            select(DeviceRegistration)
            .where(
                DeviceRegistration.tenant_id == tenant_id,
                DeviceRegistration.branch_id == branch_id,
            )
            .order_by(DeviceRegistration.created_at.asc(), DeviceRegistration.id.asc())
        )
        return list((await self._session.scalars(statement)).all())

    async def get_device_registration(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        device_id: str,
    ) -> DeviceRegistration | None:
        statement = select(DeviceRegistration).where(
            DeviceRegistration.tenant_id == tenant_id,
            DeviceRegistration.branch_id == branch_id,
            DeviceRegistration.id == device_id,
        )
        return await self._session.scalar(statement)

    async def get_device_registration_by_id(self, *, device_id: str) -> DeviceRegistration | None:
        statement = select(DeviceRegistration).where(DeviceRegistration.id == device_id)
        return await self._session.scalar(statement)

    async def get_branch_hub_device(self, *, tenant_id: str, branch_id: str) -> DeviceRegistration | None:
        statement = select(DeviceRegistration).where(
            DeviceRegistration.tenant_id == tenant_id,
            DeviceRegistration.branch_id == branch_id,
            DeviceRegistration.is_branch_hub.is_(True),
            DeviceRegistration.status == "ACTIVE",
        )
        return await self._session.scalar(statement)

    async def touch_device_registration(self, *, device: DeviceRegistration, seen_at) -> DeviceRegistration:
        device.last_seen_at = seen_at
        await self._session.flush()
        return device

    async def get_device_claim_by_id(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        claim_id: str,
    ) -> DeviceClaim | None:
        statement = select(DeviceClaim).where(
            DeviceClaim.tenant_id == tenant_id,
            DeviceClaim.branch_id == branch_id,
            DeviceClaim.id == claim_id,
        )
        return await self._session.scalar(statement)

    async def get_device_claim_by_installation_id(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        installation_id: str,
    ) -> DeviceClaim | None:
        statement = select(DeviceClaim).where(
            DeviceClaim.tenant_id == tenant_id,
            DeviceClaim.branch_id == branch_id,
            DeviceClaim.installation_id == installation_id,
        )
        return await self._session.scalar(statement)

    async def create_device_claim(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        installation_id: str,
        claim_code: str,
        runtime_kind: str,
        hostname: str | None,
        operating_system: str | None,
        architecture: str | None,
        app_version: str | None,
        seen_at,
    ) -> DeviceClaim:
        claim = DeviceClaim(
            id=new_id(),
            tenant_id=tenant_id,
            branch_id=branch_id,
            installation_id=installation_id,
            claim_code=claim_code,
            runtime_kind=runtime_kind,
            hostname=hostname,
            operating_system=operating_system,
            architecture=architecture,
            app_version=app_version,
            status="PENDING",
            last_seen_at=seen_at,
        )
        self._session.add(claim)
        await self._session.flush()
        return claim

    async def touch_device_claim(
        self,
        *,
        claim: DeviceClaim,
        runtime_kind: str,
        hostname: str | None,
        operating_system: str | None,
        architecture: str | None,
        app_version: str | None,
        seen_at,
    ) -> DeviceClaim:
        claim.runtime_kind = runtime_kind
        claim.hostname = hostname
        claim.operating_system = operating_system
        claim.architecture = architecture
        claim.app_version = app_version
        claim.last_seen_at = seen_at
        await self._session.flush()
        return claim

    async def approve_device_claim(
        self,
        *,
        claim: DeviceClaim,
        approved_device_id: str,
        approved_by_user_id: str,
        approved_at,
    ) -> DeviceClaim:
        claim.status = "APPROVED"
        claim.approved_device_id = approved_device_id
        claim.approved_by_user_id = approved_by_user_id
        claim.approved_at = approved_at
        claim.last_seen_at = approved_at
        await self._session.flush()
        return claim

    async def list_branch_device_claims(self, *, tenant_id: str, branch_id: str) -> list[DeviceClaim]:
        statement = (
            select(DeviceClaim)
            .where(
                DeviceClaim.tenant_id == tenant_id,
                DeviceClaim.branch_id == branch_id,
            )
            .order_by(DeviceClaim.created_at.desc(), DeviceClaim.id.desc())
        )
        return list((await self._session.scalars(statement)).all())
