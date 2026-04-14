from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import DeviceClaim, DeviceRegistration, SpokeRuntimeActivation, StaffProfile, StoreDesktopActivation
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
        runtime_profile: str = "desktop_spoke",
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
            runtime_profile=runtime_profile,
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

    async def get_device_registration_by_installation_id_global(self, *, installation_id: str) -> DeviceRegistration | None:
        statement = select(DeviceRegistration).where(DeviceRegistration.installation_id == installation_id)
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

    async def rotate_device_sync_secret(
        self,
        *,
        device: DeviceRegistration,
        sync_secret_hash: str,
        sync_secret_issued_at,
    ) -> DeviceRegistration:
        device.sync_secret_hash = sync_secret_hash
        device.sync_secret_issued_at = sync_secret_issued_at
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

    async def supersede_store_desktop_activations(self, *, device_id: str) -> None:
        statement = select(StoreDesktopActivation).where(
            StoreDesktopActivation.device_id == device_id,
            StoreDesktopActivation.status.in_(("ISSUED", "ACTIVE")),
        )
        for activation in (await self._session.scalars(statement)).all():
            activation.status = "SUPERSEDED"
        await self._session.flush()

    async def get_next_store_desktop_activation_version(self, *, device_id: str) -> int:
        statement = select(func.max(StoreDesktopActivation.activation_version)).where(
            StoreDesktopActivation.device_id == device_id,
        )
        current = await self._session.scalar(statement)
        return int(current or 0) + 1

    async def supersede_runtime_device_activations(self, *, device_id: str) -> None:
        await self.supersede_store_desktop_activations(device_id=device_id)

    async def get_next_runtime_device_activation_version(self, *, device_id: str) -> int:
        return await self.get_next_store_desktop_activation_version(device_id=device_id)

    async def create_store_desktop_activation(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        device_id: str,
        staff_profile_id: str,
        activation_code_hash: str,
        activation_version: int,
        issued_by_user_id: str | None,
        expires_at,
    ) -> StoreDesktopActivation:
        activation = StoreDesktopActivation(
            id=new_id(),
            tenant_id=tenant_id,
            branch_id=branch_id,
            device_id=device_id,
            staff_profile_id=staff_profile_id,
            activation_code_hash=activation_code_hash,
            activation_version=activation_version,
            status="ISSUED",
            issued_by_user_id=issued_by_user_id,
            expires_at=expires_at,
        )
        self._session.add(activation)
        await self._session.flush()
        return activation

    async def create_runtime_device_activation(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        device_id: str,
        staff_profile_id: str,
        activation_code_hash: str,
        activation_version: int,
        issued_by_user_id: str | None,
        expires_at,
    ) -> StoreDesktopActivation:
        return await self.create_store_desktop_activation(
            tenant_id=tenant_id,
            branch_id=branch_id,
            device_id=device_id,
            staff_profile_id=staff_profile_id,
            activation_code_hash=activation_code_hash,
            activation_version=activation_version,
            issued_by_user_id=issued_by_user_id,
            expires_at=expires_at,
        )

    async def create_spoke_runtime_activation(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        hub_device_id: str,
        activation_code_hash: str,
        pairing_mode: str,
        runtime_profile: str,
        expires_at,
    ) -> SpokeRuntimeActivation:
        activation = SpokeRuntimeActivation(
            id=new_id(),
            tenant_id=tenant_id,
            branch_id=branch_id,
            hub_device_id=hub_device_id,
            activation_code_hash=activation_code_hash,
            pairing_mode=pairing_mode,
            runtime_profile=runtime_profile,
            status="ISSUED",
            expires_at=expires_at,
        )
        self._session.add(activation)
        await self._session.flush()
        return activation

    async def supersede_spoke_runtime_activations(
        self,
        *,
        hub_device_id: str,
        runtime_profile: str | None = None,
    ) -> None:
        statement = select(SpokeRuntimeActivation).where(
            SpokeRuntimeActivation.hub_device_id == hub_device_id,
            SpokeRuntimeActivation.status == "ISSUED",
        )
        if runtime_profile is not None:
            statement = statement.where(SpokeRuntimeActivation.runtime_profile == runtime_profile)
        for activation in (await self._session.scalars(statement)).all():
            activation.status = "SUPERSEDED"
        await self._session.flush()

    async def get_store_desktop_activation(
        self,
        *,
        device_id: str,
        activation_code_hash: str,
    ) -> StoreDesktopActivation | None:
        statement = (
            select(StoreDesktopActivation)
            .where(
                StoreDesktopActivation.device_id == device_id,
                StoreDesktopActivation.activation_code_hash == activation_code_hash,
                StoreDesktopActivation.status == "ISSUED",
            )
            .order_by(StoreDesktopActivation.created_at.desc(), StoreDesktopActivation.id.desc())
        )
        return await self._session.scalar(statement)

    async def get_runtime_device_activation(
        self,
        *,
        device_id: str,
        activation_code_hash: str,
    ) -> StoreDesktopActivation | None:
        return await self.get_store_desktop_activation(
            device_id=device_id,
            activation_code_hash=activation_code_hash,
        )

    async def redeem_store_desktop_activation(
        self,
        *,
        activation: StoreDesktopActivation,
        local_auth_token_hash: str,
        redeemed_at,
        offline_valid_until,
    ) -> StoreDesktopActivation:
        activation.status = "ACTIVE"
        activation.local_auth_token_hash = local_auth_token_hash
        activation.redeemed_at = redeemed_at
        activation.last_unlocked_at = redeemed_at
        activation.offline_valid_until = offline_valid_until
        await self._session.flush()
        return activation

    async def get_active_store_desktop_activation_by_local_auth_token(
        self,
        *,
        device_id: str,
        local_auth_token_hash: str,
    ) -> StoreDesktopActivation | None:
        statement = (
            select(StoreDesktopActivation)
            .where(
                StoreDesktopActivation.device_id == device_id,
                StoreDesktopActivation.local_auth_token_hash == local_auth_token_hash,
                StoreDesktopActivation.status == "ACTIVE",
            )
            .order_by(StoreDesktopActivation.created_at.desc(), StoreDesktopActivation.id.desc())
        )
        return await self._session.scalar(statement)

    async def touch_store_desktop_activation_unlock(self, *, activation: StoreDesktopActivation, unlocked_at, offline_valid_until) -> StoreDesktopActivation:
        activation.last_unlocked_at = unlocked_at
        activation.offline_valid_until = offline_valid_until
        await self._session.flush()
        return activation

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
