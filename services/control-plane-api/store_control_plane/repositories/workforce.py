from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import BranchAttendanceSession, BranchCashierSession, BranchRuntimePolicy, BranchShiftSession, DeviceClaim, DeviceRegistration, Sale, SaleReturn, SpokeRuntimeActivation, StaffProfile, StoreDesktopActivation
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

    async def get_branch_runtime_policy(
        self,
        *,
        tenant_id: str,
        branch_id: str,
    ) -> BranchRuntimePolicy | None:
        statement = select(BranchRuntimePolicy).where(
            BranchRuntimePolicy.tenant_id == tenant_id,
            BranchRuntimePolicy.branch_id == branch_id,
        )
        return await self._session.scalar(statement)

    async def upsert_branch_runtime_policy(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        require_shift_for_attendance: bool,
        require_attendance_for_cashier: bool,
        require_assigned_staff_for_device: bool,
        allow_offline_sales: bool,
        max_pending_offline_sales: int,
        updated_by_user_id: str | None,
    ) -> BranchRuntimePolicy:
        record = await self.get_branch_runtime_policy(tenant_id=tenant_id, branch_id=branch_id)
        if record is None:
            record = BranchRuntimePolicy(
                id=new_id(),
                tenant_id=tenant_id,
                branch_id=branch_id,
                require_shift_for_attendance=require_shift_for_attendance,
                require_attendance_for_cashier=require_attendance_for_cashier,
                require_assigned_staff_for_device=require_assigned_staff_for_device,
                allow_offline_sales=allow_offline_sales,
                max_pending_offline_sales=max_pending_offline_sales,
                updated_by_user_id=updated_by_user_id,
            )
            self._session.add(record)
        else:
            record.require_shift_for_attendance = require_shift_for_attendance
            record.require_attendance_for_cashier = require_attendance_for_cashier
            record.require_assigned_staff_for_device = require_assigned_staff_for_device
            record.allow_offline_sales = allow_offline_sales
            record.max_pending_offline_sales = max_pending_offline_sales
            record.updated_by_user_id = updated_by_user_id
        await self._session.flush()
        return record

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

    async def next_branch_cashier_session_sequence(self, *, tenant_id: str, branch_id: str) -> int:
        statement = select(func.count(BranchCashierSession.id)).where(
            BranchCashierSession.tenant_id == tenant_id,
            BranchCashierSession.branch_id == branch_id,
        )
        count = await self._session.scalar(statement)
        return int(count or 0) + 1

    async def next_branch_attendance_session_sequence(self, *, tenant_id: str, branch_id: str) -> int:
        statement = select(func.count(BranchAttendanceSession.id)).where(
            BranchAttendanceSession.tenant_id == tenant_id,
            BranchAttendanceSession.branch_id == branch_id,
        )
        count = await self._session.scalar(statement)
        return int(count or 0) + 1

    async def next_branch_shift_session_sequence(self, *, tenant_id: str, branch_id: str) -> int:
        statement = select(func.count(BranchShiftSession.id)).where(
            BranchShiftSession.tenant_id == tenant_id,
            BranchShiftSession.branch_id == branch_id,
        )
        count = await self._session.scalar(statement)
        return int(count or 0) + 1

    async def create_branch_cashier_session(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        attendance_session_id: str | None,
        device_registration_id: str,
        staff_profile_id: str,
        runtime_user_id: str | None,
        opened_by_user_id: str | None,
        session_number: str,
        opening_float_amount: float,
        opening_note: str | None,
        opened_at,
    ) -> BranchCashierSession:
        record = BranchCashierSession(
            id=new_id(),
            tenant_id=tenant_id,
            branch_id=branch_id,
            attendance_session_id=attendance_session_id,
            device_registration_id=device_registration_id,
            staff_profile_id=staff_profile_id,
            runtime_user_id=runtime_user_id,
            opened_by_user_id=opened_by_user_id,
            status="OPEN",
            session_number=session_number,
            opening_float_amount=opening_float_amount,
            opening_note=opening_note,
            opened_at=opened_at,
            last_activity_at=opened_at,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def create_branch_attendance_session(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        shift_session_id: str | None,
        device_registration_id: str,
        staff_profile_id: str,
        runtime_user_id: str | None,
        opened_by_user_id: str | None,
        attendance_number: str,
        clock_in_note: str | None,
        opened_at,
    ) -> BranchAttendanceSession:
        record = BranchAttendanceSession(
            id=new_id(),
            tenant_id=tenant_id,
            branch_id=branch_id,
            shift_session_id=shift_session_id,
            device_registration_id=device_registration_id,
            staff_profile_id=staff_profile_id,
            runtime_user_id=runtime_user_id,
            opened_by_user_id=opened_by_user_id,
            status="OPEN",
            attendance_number=attendance_number,
            clock_in_note=clock_in_note,
            opened_at=opened_at,
            last_activity_at=opened_at,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def create_branch_shift_session(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        opened_by_user_id: str | None,
        shift_number: str,
        shift_name: str,
        opening_note: str | None,
        opened_at,
    ) -> BranchShiftSession:
        record = BranchShiftSession(
            id=new_id(),
            tenant_id=tenant_id,
            branch_id=branch_id,
            opened_by_user_id=opened_by_user_id,
            status="OPEN",
            shift_number=shift_number,
            shift_name=shift_name,
            opening_note=opening_note,
            opened_at=opened_at,
            last_activity_at=opened_at,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def get_branch_cashier_session(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        cashier_session_id: str,
    ) -> BranchCashierSession | None:
        statement = select(BranchCashierSession).where(
            BranchCashierSession.tenant_id == tenant_id,
            BranchCashierSession.branch_id == branch_id,
            BranchCashierSession.id == cashier_session_id,
        )
        return await self._session.scalar(statement)

    async def get_branch_attendance_session(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        attendance_session_id: str,
    ) -> BranchAttendanceSession | None:
        statement = select(BranchAttendanceSession).where(
            BranchAttendanceSession.tenant_id == tenant_id,
            BranchAttendanceSession.branch_id == branch_id,
            BranchAttendanceSession.id == attendance_session_id,
        )
        return await self._session.scalar(statement)

    async def get_branch_shift_session(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        shift_session_id: str,
    ) -> BranchShiftSession | None:
        statement = select(BranchShiftSession).where(
            BranchShiftSession.tenant_id == tenant_id,
            BranchShiftSession.branch_id == branch_id,
            BranchShiftSession.id == shift_session_id,
        )
        return await self._session.scalar(statement)

    async def get_open_shift_session(
        self,
        *,
        tenant_id: str,
        branch_id: str,
    ) -> BranchShiftSession | None:
        statement = (
            select(BranchShiftSession)
            .where(
                BranchShiftSession.tenant_id == tenant_id,
                BranchShiftSession.branch_id == branch_id,
                BranchShiftSession.status == "OPEN",
            )
            .order_by(BranchShiftSession.opened_at.desc(), BranchShiftSession.id.desc())
        )
        return await self._session.scalar(statement)

    async def get_open_cashier_session_by_device(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        device_registration_id: str,
    ) -> BranchCashierSession | None:
        statement = select(BranchCashierSession).where(
            BranchCashierSession.tenant_id == tenant_id,
            BranchCashierSession.branch_id == branch_id,
            BranchCashierSession.device_registration_id == device_registration_id,
            BranchCashierSession.status == "OPEN",
        )
        return await self._session.scalar(statement)

    async def get_open_cashier_session_by_staff_profile(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        staff_profile_id: str,
    ) -> BranchCashierSession | None:
        statement = select(BranchCashierSession).where(
            BranchCashierSession.tenant_id == tenant_id,
            BranchCashierSession.branch_id == branch_id,
            BranchCashierSession.staff_profile_id == staff_profile_id,
            BranchCashierSession.status == "OPEN",
        )
        return await self._session.scalar(statement)

    async def get_open_cashier_session_by_attendance_session(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        attendance_session_id: str,
    ) -> BranchCashierSession | None:
        statement = select(BranchCashierSession).where(
            BranchCashierSession.tenant_id == tenant_id,
            BranchCashierSession.branch_id == branch_id,
            BranchCashierSession.attendance_session_id == attendance_session_id,
            BranchCashierSession.status == "OPEN",
        )
        return await self._session.scalar(statement)

    async def get_open_attendance_session_by_device(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        device_registration_id: str,
    ) -> BranchAttendanceSession | None:
        statement = select(BranchAttendanceSession).where(
            BranchAttendanceSession.tenant_id == tenant_id,
            BranchAttendanceSession.branch_id == branch_id,
            BranchAttendanceSession.device_registration_id == device_registration_id,
            BranchAttendanceSession.status == "OPEN",
        )
        return await self._session.scalar(statement)

    async def get_open_attendance_session_by_staff_profile(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        staff_profile_id: str,
    ) -> BranchAttendanceSession | None:
        statement = select(BranchAttendanceSession).where(
            BranchAttendanceSession.tenant_id == tenant_id,
            BranchAttendanceSession.branch_id == branch_id,
            BranchAttendanceSession.staff_profile_id == staff_profile_id,
            BranchAttendanceSession.status == "OPEN",
        )
        return await self._session.scalar(statement)

    async def list_branch_cashier_sessions(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        status: str | None = None,
    ) -> list[BranchCashierSession]:
        statement = select(BranchCashierSession).where(
            BranchCashierSession.tenant_id == tenant_id,
            BranchCashierSession.branch_id == branch_id,
        )
        if status is not None:
            statement = statement.where(BranchCashierSession.status == status)
        statement = statement.order_by(BranchCashierSession.opened_at.desc(), BranchCashierSession.id.desc())
        return list((await self._session.scalars(statement)).all())

    async def list_branch_attendance_sessions(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        status: str | None = None,
    ) -> list[BranchAttendanceSession]:
        statement = select(BranchAttendanceSession).where(
            BranchAttendanceSession.tenant_id == tenant_id,
            BranchAttendanceSession.branch_id == branch_id,
        )
        if status is not None:
            statement = statement.where(BranchAttendanceSession.status == status)
        statement = statement.order_by(BranchAttendanceSession.opened_at.desc(), BranchAttendanceSession.id.desc())
        return list((await self._session.scalars(statement)).all())

    async def list_branch_shift_sessions(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        status: str | None = None,
    ) -> list[BranchShiftSession]:
        statement = select(BranchShiftSession).where(
            BranchShiftSession.tenant_id == tenant_id,
            BranchShiftSession.branch_id == branch_id,
        )
        if status is not None:
            statement = statement.where(BranchShiftSession.status == status)
        statement = statement.order_by(BranchShiftSession.opened_at.desc(), BranchShiftSession.id.desc())
        return list((await self._session.scalars(statement)).all())

    async def close_branch_cashier_session(
        self,
        *,
        cashier_session: BranchCashierSession,
        closed_by_user_id: str | None,
        status: str,
        closing_note: str | None,
        force_close_reason: str | None,
        closed_at,
    ) -> BranchCashierSession:
        cashier_session.status = status
        cashier_session.closed_by_user_id = closed_by_user_id
        cashier_session.closing_note = closing_note
        cashier_session.force_close_reason = force_close_reason
        cashier_session.closed_at = closed_at
        cashier_session.last_activity_at = closed_at
        await self._session.flush()
        return cashier_session

    async def close_branch_attendance_session(
        self,
        *,
        attendance_session: BranchAttendanceSession,
        closed_by_user_id: str | None,
        status: str,
        clock_out_note: str | None,
        force_close_reason: str | None,
        closed_at,
    ) -> BranchAttendanceSession:
        attendance_session.status = status
        attendance_session.closed_by_user_id = closed_by_user_id
        attendance_session.clock_out_note = clock_out_note
        attendance_session.force_close_reason = force_close_reason
        attendance_session.closed_at = closed_at
        attendance_session.last_activity_at = closed_at
        await self._session.flush()
        return attendance_session

    async def close_branch_shift_session(
        self,
        *,
        shift_session: BranchShiftSession,
        closed_by_user_id: str | None,
        status: str,
        closing_note: str | None,
        force_close_reason: str | None,
        closed_at,
    ) -> BranchShiftSession:
        shift_session.status = status
        shift_session.closed_by_user_id = closed_by_user_id
        shift_session.closing_note = closing_note
        shift_session.force_close_reason = force_close_reason
        shift_session.closed_at = closed_at
        shift_session.last_activity_at = closed_at
        await self._session.flush()
        return shift_session

    async def touch_branch_cashier_session_activity(
        self,
        *,
        cashier_session: BranchCashierSession,
        activity_at,
    ) -> BranchCashierSession:
        cashier_session.last_activity_at = activity_at
        await self._session.flush()
        return cashier_session

    async def get_open_attendance_sessions_by_shift_session(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        shift_session_id: str,
    ) -> list[BranchAttendanceSession]:
        statement = select(BranchAttendanceSession).where(
            BranchAttendanceSession.tenant_id == tenant_id,
            BranchAttendanceSession.branch_id == branch_id,
            BranchAttendanceSession.shift_session_id == shift_session_id,
            BranchAttendanceSession.status == "OPEN",
        )
        return list((await self._session.scalars(statement)).all())

    async def get_open_cashier_sessions_by_shift_session(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        shift_session_id: str,
    ) -> list[BranchCashierSession]:
        statement = select(BranchCashierSession).join(
            BranchAttendanceSession,
            BranchAttendanceSession.id == BranchCashierSession.attendance_session_id,
        ).where(
            BranchCashierSession.tenant_id == tenant_id,
            BranchCashierSession.branch_id == branch_id,
            BranchCashierSession.status == "OPEN",
            BranchAttendanceSession.shift_session_id == shift_session_id,
        )
        return list((await self._session.scalars(statement)).all())

    async def summarize_cashier_sessions(self, *, cashier_session_ids: list[str]) -> dict[str, dict[str, float | int]]:
        if not cashier_session_ids:
            return {}

        sales_statement = (
            select(
                Sale.cashier_session_id,
                func.count(Sale.id),
                func.coalesce(func.sum(Sale.grand_total), 0.0),
            )
            .where(Sale.cashier_session_id.in_(cashier_session_ids))
            .group_by(Sale.cashier_session_id)
        )
        sales_rows = (await self._session.execute(sales_statement)).all()
        sales_by_session_id = {
            str(cashier_session_id): {"linked_sales_count": int(count), "gross_billed_amount": float(gross_amount or 0.0)}
            for cashier_session_id, count, gross_amount in sales_rows
            if cashier_session_id is not None
        }

        returns_statement = (
            select(SaleReturn.cashier_session_id, func.count(SaleReturn.id))
            .where(SaleReturn.cashier_session_id.in_(cashier_session_ids))
            .group_by(SaleReturn.cashier_session_id)
        )
        returns_rows = (await self._session.execute(returns_statement)).all()
        returns_by_session_id = {
            str(cashier_session_id): int(count)
            for cashier_session_id, count in returns_rows
            if cashier_session_id is not None
        }

        summaries: dict[str, dict[str, float | int]] = {}
        for cashier_session_id in cashier_session_ids:
            sales_summary = sales_by_session_id.get(
                cashier_session_id,
                {"linked_sales_count": 0, "gross_billed_amount": 0.0},
            )
            summaries[cashier_session_id] = {
                "linked_sales_count": int(sales_summary["linked_sales_count"]),
                "linked_returns_count": returns_by_session_id.get(cashier_session_id, 0),
                "gross_billed_amount": round(float(sales_summary["gross_billed_amount"]), 2),
            }
        return summaries

    async def summarize_attendance_sessions(self, *, attendance_session_ids: list[str]) -> dict[str, dict[str, int]]:
        if not attendance_session_ids:
            return {}

        statement = (
            select(BranchCashierSession.attendance_session_id, func.count(BranchCashierSession.id))
            .where(BranchCashierSession.attendance_session_id.in_(attendance_session_ids))
            .group_by(BranchCashierSession.attendance_session_id)
        )
        rows = (await self._session.execute(statement)).all()
        counts = {
            str(attendance_session_id): int(count)
            for attendance_session_id, count in rows
            if attendance_session_id is not None
        }
        return {
            attendance_session_id: {
                "linked_cashier_sessions_count": counts.get(attendance_session_id, 0),
            }
            for attendance_session_id in attendance_session_ids
        }

    async def summarize_shift_sessions(self, *, shift_session_ids: list[str]) -> dict[str, dict[str, int]]:
        if not shift_session_ids:
            return {}

        attendance_statement = (
            select(BranchAttendanceSession.shift_session_id, func.count(BranchAttendanceSession.id))
            .where(BranchAttendanceSession.shift_session_id.in_(shift_session_ids))
            .group_by(BranchAttendanceSession.shift_session_id)
        )
        attendance_rows = (await self._session.execute(attendance_statement)).all()
        attendance_counts = {
            str(shift_session_id): int(count)
            for shift_session_id, count in attendance_rows
            if shift_session_id is not None
        }

        cashier_statement = (
            select(BranchAttendanceSession.shift_session_id, func.count(BranchCashierSession.id))
            .join(
                BranchCashierSession,
                BranchCashierSession.attendance_session_id == BranchAttendanceSession.id,
            )
            .where(BranchAttendanceSession.shift_session_id.in_(shift_session_ids))
            .group_by(BranchAttendanceSession.shift_session_id)
        )
        cashier_rows = (await self._session.execute(cashier_statement)).all()
        cashier_counts = {
            str(shift_session_id): int(count)
            for shift_session_id, count in cashier_rows
            if shift_session_id is not None
        }

        return {
            shift_session_id: {
                "linked_attendance_sessions_count": attendance_counts.get(shift_session_id, 0),
                "linked_cashier_sessions_count": cashier_counts.get(shift_session_id, 0),
            }
            for shift_session_id in shift_session_ids
        }
