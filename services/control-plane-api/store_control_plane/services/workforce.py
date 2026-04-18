from __future__ import annotations

import csv
from datetime import timedelta
import hashlib
import io
import secrets

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories import AuditRepository, IdentityRepository, MembershipRepository, TenantRepository, WorkforceRepository
from ..utils import utc_now
from .commercial_access import CommercialAccessService
from .sync_runtime_auth import hash_sync_access_secret

STORE_DESKTOP_ACTIVATION_TTL_MINUTES = 15
STORE_DESKTOP_OFFLINE_UNLOCK_TTL_HOURS = 24
DEFAULT_RUNTIME_PROFILE_BY_SURFACE = {
    "store_desktop": "desktop_spoke",
    "store_mobile": "mobile_store_spoke",
    "inventory_tablet": "inventory_tablet_spoke",
    "customer_display": "customer_display",
}
DEFAULT_BRANCH_RUNTIME_POLICY = {
    "require_shift_for_attendance": False,
    "require_attendance_for_cashier": True,
    "require_assigned_staff_for_device": True,
    "allow_offline_sales": True,
    "max_pending_offline_sales": 25,
}


def build_device_claim_code(installation_id: str) -> str:
    normalized = "".join(character for character in installation_id.upper() if character.isalnum())
    suffix = normalized[-8:] if normalized else "UNBOUND00"
    return f"STORE-{suffix}"


def resolve_device_runtime_profile(
    *,
    session_surface: str,
    is_branch_hub: bool,
    runtime_profile: str | None = None,
) -> str:
    if runtime_profile:
        return runtime_profile
    if is_branch_hub:
        return "branch_hub"
    return DEFAULT_RUNTIME_PROFILE_BY_SURFACE.get(session_surface, "desktop_spoke")


def serialize_device_claim(claim, device) -> dict[str, object]:
    return {
        "id": claim.id,
        "tenant_id": claim.tenant_id,
        "branch_id": claim.branch_id,
        "installation_id": claim.installation_id,
        "claim_code": claim.claim_code,
        "runtime_kind": claim.runtime_kind,
        "hostname": claim.hostname,
        "operating_system": claim.operating_system,
        "architecture": claim.architecture,
        "app_version": claim.app_version,
        "status": claim.status,
        "approved_device_id": claim.approved_device_id,
        "approved_device_code": device.device_code if device is not None else None,
        "created_at": claim.created_at.isoformat(),
        "last_seen_at": claim.last_seen_at.isoformat() if claim.last_seen_at is not None else None,
        "approved_at": claim.approved_at.isoformat() if claim.approved_at is not None else None,
    }


def normalize_store_desktop_activation_code(code: str) -> str:
    normalized = "".join(character for character in code.upper().strip() if character.isalnum())
    if not normalized:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Activation code is required")
    return normalized


def hash_store_desktop_activation_code(code: str) -> str:
    normalized = normalize_store_desktop_activation_code(code)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def build_store_desktop_activation_code() -> str:
    token = secrets.token_hex(6).upper()
    return f"{token[:4]}-{token[4:8]}-{token[8:12]}"


def hash_store_desktop_local_auth_token(token: str) -> str:
    normalized = token.strip()
    if not normalized:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Local auth token is required")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def build_store_desktop_local_auth_token() -> str:
    return secrets.token_urlsafe(32)


def build_runtime_user_subject(*, session_surface: str, staff_profile_id: str) -> str:
    return f"{session_surface}-activation:{staff_profile_id}"


def cashier_session_number(*, branch_code: str, sequence_number: int) -> str:
    normalized_branch_code = "".join(character for character in branch_code.upper() if character.isalnum())
    return f"CSES-{normalized_branch_code}-{sequence_number:04d}"


def attendance_session_number(*, branch_code: str, sequence_number: int) -> str:
    normalized_branch_code = "".join(character for character in branch_code.upper() if character.isalnum())
    return f"ATTD-{normalized_branch_code}-{sequence_number:04d}"


def shift_session_number(*, branch_code: str, sequence_number: int) -> str:
    normalized_branch_code = "".join(character for character in branch_code.upper() if character.isalnum())
    return f"SHFT-{normalized_branch_code}-{sequence_number:04d}"


def serialize_cashier_session(record, *, device, staff_profile, summary: dict[str, object] | None = None) -> dict[str, object]:
    resolved_summary = summary or {}
    return {
        "id": record.id,
        "tenant_id": record.tenant_id,
        "branch_id": record.branch_id,
        "attendance_session_id": record.attendance_session_id,
        "device_registration_id": record.device_registration_id,
        "device_name": device.device_name if device is not None else None,
        "device_code": device.device_code if device is not None else None,
        "staff_profile_id": record.staff_profile_id,
        "staff_full_name": staff_profile.full_name if staff_profile is not None else None,
        "runtime_user_id": record.runtime_user_id,
        "opened_by_user_id": record.opened_by_user_id,
        "closed_by_user_id": record.closed_by_user_id,
        "status": record.status,
        "session_number": record.session_number,
        "opening_float_amount": record.opening_float_amount,
        "opening_note": record.opening_note,
        "closing_note": record.closing_note,
        "force_close_reason": record.force_close_reason,
        "opened_at": record.opened_at,
        "closed_at": record.closed_at,
        "last_activity_at": record.last_activity_at,
        "linked_sales_count": int(resolved_summary.get("linked_sales_count", 0)),
        "linked_returns_count": int(resolved_summary.get("linked_returns_count", 0)),
        "gross_billed_amount": round(float(resolved_summary.get("gross_billed_amount", 0.0)), 2),
    }


def serialize_attendance_session(record, *, device, staff_profile, summary: dict[str, object] | None = None) -> dict[str, object]:
    resolved_summary = summary or {}
    return {
        "id": record.id,
        "tenant_id": record.tenant_id,
        "branch_id": record.branch_id,
        "shift_session_id": record.shift_session_id,
        "device_registration_id": record.device_registration_id,
        "device_name": device.device_name if device is not None else None,
        "device_code": device.device_code if device is not None else None,
        "staff_profile_id": record.staff_profile_id,
        "staff_full_name": staff_profile.full_name if staff_profile is not None else None,
        "runtime_user_id": record.runtime_user_id,
        "opened_by_user_id": record.opened_by_user_id,
        "closed_by_user_id": record.closed_by_user_id,
        "status": record.status,
        "attendance_number": record.attendance_number,
        "clock_in_note": record.clock_in_note,
        "clock_out_note": record.clock_out_note,
        "force_close_reason": record.force_close_reason,
        "opened_at": record.opened_at,
        "closed_at": record.closed_at,
        "last_activity_at": record.last_activity_at,
        "linked_cashier_sessions_count": int(resolved_summary.get("linked_cashier_sessions_count", 0)),
    }


def serialize_shift_session(record, *, summary: dict[str, object] | None = None) -> dict[str, object]:
    resolved_summary = summary or {}
    return {
        "id": record.id,
        "tenant_id": record.tenant_id,
        "branch_id": record.branch_id,
        "opened_by_user_id": record.opened_by_user_id,
        "closed_by_user_id": record.closed_by_user_id,
        "status": record.status,
        "shift_number": record.shift_number,
        "shift_name": record.shift_name,
        "opening_note": record.opening_note,
        "closing_note": record.closing_note,
        "force_close_reason": record.force_close_reason,
        "opened_at": record.opened_at,
        "closed_at": record.closed_at,
        "last_activity_at": record.last_activity_at,
        "linked_attendance_sessions_count": int(resolved_summary.get("linked_attendance_sessions_count", 0)),
        "linked_cashier_sessions_count": int(resolved_summary.get("linked_cashier_sessions_count", 0)),
    }


class WorkforceService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._tenant_repo = TenantRepository(session)
        self._membership_repo = MembershipRepository(session)
        self._workforce_repo = WorkforceRepository(session)
        self._audit_repo = AuditRepository(session)
        self._identity_repo = IdentityRepository(session)
        self._commercial_access = CommercialAccessService(session)

    async def _resolve_runtime_user_for_profile(self, *, profile, synthetic_subject: str, provider: str):
        existing_user = await self._identity_repo.get_user_by_email(profile.email)
        if existing_user is not None and existing_user.external_subject != synthetic_subject:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Staff profile email is already bound to an interactive user",
            )

        runtime_user = await self._identity_repo.ensure_runtime_user(
            email=profile.email,
            full_name=profile.full_name,
            synthetic_subject=synthetic_subject,
            provider=provider,
        )
        await self._membership_repo.activate_pending_memberships(email=profile.email, user_id=runtime_user.id)
        await self._workforce_repo.bind_profiles_for_user(
            email=profile.email,
            user_id=runtime_user.id,
            full_name=profile.full_name,
        )
        return runtime_user

    async def _assert_runtime_branch_membership(self, *, runtime_user_id: str, device) -> None:
        active_branch_memberships = await self._membership_repo.list_active_branch_memberships(runtime_user_id)
        if not any(
            membership.tenant_id == device.tenant_id and membership.branch_id == device.branch_id
            for membership in active_branch_memberships
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Activated staff profile is not assigned to this branch",
            )

    async def _get_branch_runtime_policy_record(self, *, tenant_id: str, branch_id: str):
        return await self._workforce_repo.get_branch_runtime_policy(tenant_id=tenant_id, branch_id=branch_id)

    async def _resolve_branch_runtime_policy(self, *, tenant_id: str, branch_id: str) -> dict[str, object]:
        record = await self._get_branch_runtime_policy_record(tenant_id=tenant_id, branch_id=branch_id)
        if record is None:
            return {
                "id": None,
                "tenant_id": tenant_id,
                "branch_id": branch_id,
                "updated_by_user_id": None,
                **DEFAULT_BRANCH_RUNTIME_POLICY,
            }
        return self._serialize_branch_runtime_policy(record)

    def _serialize_branch_runtime_policy(self, record) -> dict[str, object]:
        return {
            "id": record.id,
            "tenant_id": record.tenant_id,
            "branch_id": record.branch_id,
            "require_shift_for_attendance": bool(record.require_shift_for_attendance),
            "require_attendance_for_cashier": bool(record.require_attendance_for_cashier),
            "require_assigned_staff_for_device": bool(record.require_assigned_staff_for_device),
            "allow_offline_sales": bool(record.allow_offline_sales),
            "max_pending_offline_sales": int(record.max_pending_offline_sales),
            "updated_by_user_id": record.updated_by_user_id,
        }

    async def create_staff_profile(
        self,
        *,
        tenant_id: str,
        actor_user_id: str,
        email: str,
        full_name: str,
        phone_number: str | None,
        primary_branch_id: str | None,
    ):
        tenant = await self._tenant_repo.get_tenant(tenant_id)
        if tenant is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
        if primary_branch_id is not None:
            branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=primary_branch_id)
            if branch is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
        profile = await self._workforce_repo.upsert_staff_profile(
            tenant_id=tenant_id,
            email=email,
            full_name=full_name,
            phone_number=phone_number,
            primary_branch_id=primary_branch_id,
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=primary_branch_id,
            actor_user_id=actor_user_id,
            action="staff_profile.upserted",
            entity_type="staff_profile",
            entity_id=profile.id,
            payload={"email": profile.email},
        )
        await self._session.commit()
        return profile

    async def list_staff_profiles(self, tenant_id: str) -> list[dict[str, object]]:
        tenant = await self._tenant_repo.get_tenant(tenant_id)
        if tenant is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
        profiles = await self._workforce_repo.list_staff_profiles(tenant_id=tenant_id)
        tenant_memberships = await self._membership_repo.list_tenant_memberships_for_tenant(tenant_id)
        branch_memberships = await self._membership_repo.list_branch_memberships_for_tenant(tenant_id)

        records: list[dict[str, object]] = []
        for profile in profiles:
            role_names = {
                membership.role_name
                for membership in tenant_memberships
                if membership.invite_email == profile.email
            }
            branch_ids = {
                membership.branch_id
                for membership in branch_memberships
                if membership.invite_email == profile.email
            }
            role_names.update(
                membership.role_name
                for membership in branch_memberships
                if membership.invite_email == profile.email
            )
            records.append(
                {
                    "id": profile.id,
                    "tenant_id": profile.tenant_id,
                    "user_id": profile.user_id,
                    "email": profile.email,
                    "full_name": profile.full_name,
                    "phone_number": profile.phone_number,
                    "primary_branch_id": profile.primary_branch_id,
                    "status": profile.status,
                    "role_names": sorted(role_names),
                    "branch_ids": sorted(branch_ids),
                }
            )
        return records

    async def register_device(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        actor_user_id: str,
        assigned_staff_profile_id: str | None,
        installation_id: str | None,
        device_name: str,
        device_code: str,
        session_surface: str,
        runtime_profile: str | None = None,
        is_branch_hub: bool = False,
    ) -> dict[str, object]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
        if assigned_staff_profile_id is not None:
            profile = await self._workforce_repo.get_staff_profile_by_id(
                tenant_id=tenant_id,
                staff_profile_id=assigned_staff_profile_id,
            )
            if profile is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff profile not found")
        if is_branch_hub:
            existing_hub = await self._workforce_repo.get_branch_hub_device(tenant_id=tenant_id, branch_id=branch_id)
            if existing_hub is not None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Branch hub already registered")
        existing_device = await self._workforce_repo.get_device_registration_by_code(
            tenant_id=tenant_id,
            branch_id=branch_id,
            device_code=device_code,
        )
        if existing_device is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Device code already registered")
        if installation_id is not None:
            existing_installation = await self._workforce_repo.get_device_registration_by_installation_id(
                tenant_id=tenant_id,
                branch_id=branch_id,
                installation_id=installation_id,
            )
            if existing_installation is not None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Installation already bound")
        resolved_runtime_profile = resolve_device_runtime_profile(
            session_surface=session_surface,
            is_branch_hub=is_branch_hub,
            runtime_profile=runtime_profile,
        )
        sync_access_secret = secrets.token_urlsafe(24) if is_branch_hub else None
        device = await self._workforce_repo.create_device_registration(
            tenant_id=tenant_id,
            branch_id=branch_id,
            assigned_staff_profile_id=assigned_staff_profile_id,
            installation_id=installation_id,
            device_name=device_name,
            device_code=device_code,
            session_surface=session_surface,
            runtime_profile=resolved_runtime_profile,
            is_branch_hub=is_branch_hub,
            sync_secret_hash=hash_sync_access_secret(sync_access_secret) if sync_access_secret else None,
            sync_secret_issued_at=utc_now() if sync_access_secret else None,
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="device.registered",
            entity_type="device_registration",
            entity_id=device.id,
            payload={
                "device_code": device.device_code,
                "session_surface": device.session_surface,
                "runtime_profile": device.runtime_profile,
                "is_branch_hub": device.is_branch_hub,
                "installation_id": device.installation_id,
            },
        )
        await self._session.commit()
        return {
            "id": device.id,
            "tenant_id": device.tenant_id,
            "branch_id": device.branch_id,
            "device_name": device.device_name,
            "device_code": device.device_code,
            "session_surface": device.session_surface,
            "runtime_profile": device.runtime_profile,
            "is_branch_hub": device.is_branch_hub,
            "status": device.status,
            "assigned_staff_profile_id": device.assigned_staff_profile_id,
            "installation_id": device.installation_id,
            "sync_access_secret": sync_access_secret,
        }

    async def list_branch_devices(self, *, tenant_id: str, branch_id: str) -> list[dict[str, object]]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
        devices = await self._workforce_repo.list_branch_devices(tenant_id=tenant_id, branch_id=branch_id)
        profiles = {
            profile.id: profile
            for profile in await self._workforce_repo.list_staff_profiles(tenant_id=tenant_id)
        }
        return [
            {
                "id": device.id,
                "tenant_id": device.tenant_id,
                "branch_id": device.branch_id,
                "device_name": device.device_name,
                "device_code": device.device_code,
                "session_surface": device.session_surface,
                "runtime_profile": device.runtime_profile,
                "is_branch_hub": device.is_branch_hub,
                "status": device.status,
                "assigned_staff_profile_id": device.assigned_staff_profile_id,
                "assigned_staff_full_name": profiles.get(device.assigned_staff_profile_id).full_name
                if device.assigned_staff_profile_id and profiles.get(device.assigned_staff_profile_id)
                else None,
                "installation_id": device.installation_id,
            }
            for device in devices
        ]

    async def get_branch_runtime_policy(self, *, tenant_id: str, branch_id: str) -> dict[str, object]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
        return await self._resolve_branch_runtime_policy(tenant_id=tenant_id, branch_id=branch_id)

    async def update_branch_runtime_policy(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        actor_user_id: str,
        require_shift_for_attendance: bool,
        require_attendance_for_cashier: bool,
        require_assigned_staff_for_device: bool,
        allow_offline_sales: bool,
        max_pending_offline_sales: int,
    ) -> dict[str, object]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
        if max_pending_offline_sales < 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Offline pending-sale limit cannot be negative")
        record = await self._workforce_repo.upsert_branch_runtime_policy(
            tenant_id=tenant_id,
            branch_id=branch_id,
            require_shift_for_attendance=require_shift_for_attendance,
            require_attendance_for_cashier=require_attendance_for_cashier,
            require_assigned_staff_for_device=require_assigned_staff_for_device,
            allow_offline_sales=allow_offline_sales,
            max_pending_offline_sales=max_pending_offline_sales,
            updated_by_user_id=actor_user_id,
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="branch_runtime_policy.updated",
            entity_type="branch_runtime_policy",
            entity_id=record.id,
            payload=self._serialize_branch_runtime_policy(record),
        )
        await self._session.commit()
        return self._serialize_branch_runtime_policy(record)

    async def create_shift_session(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        actor_user_id: str,
        shift_name: str,
        opening_note: str | None,
    ) -> dict[str, object]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
        existing_open_shift = await self._workforce_repo.get_open_shift_session(tenant_id=tenant_id, branch_id=branch_id)
        if existing_open_shift is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A shift session is already open for this branch")
        opened_at = utc_now()
        sequence_number = await self._workforce_repo.next_branch_shift_session_sequence(
            tenant_id=tenant_id,
            branch_id=branch_id,
        )
        record = await self._workforce_repo.create_branch_shift_session(
            tenant_id=tenant_id,
            branch_id=branch_id,
            opened_by_user_id=actor_user_id,
            shift_number=shift_session_number(branch_code=branch.code, sequence_number=sequence_number),
            shift_name=shift_name.strip(),
            opening_note=opening_note,
            opened_at=opened_at,
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="shift_session.opened",
            entity_type="branch_shift_session",
            entity_id=record.id,
            payload={"shift_number": record.shift_number, "shift_name": record.shift_name},
        )
        await self._session.commit()
        return serialize_shift_session(record)

    async def list_branch_shift_sessions(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        status: str | None = None,
    ) -> list[dict[str, object]]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
        records = await self._workforce_repo.list_branch_shift_sessions(
            tenant_id=tenant_id,
            branch_id=branch_id,
            status=status,
        )
        summaries = await self._workforce_repo.summarize_shift_sessions(shift_session_ids=[record.id for record in records])
        return [serialize_shift_session(record, summary=summaries.get(record.id)) for record in records]

    async def get_shift_session(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        shift_session_id: str,
    ) -> dict[str, object]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
        record = await self._workforce_repo.get_branch_shift_session(
            tenant_id=tenant_id,
            branch_id=branch_id,
            shift_session_id=shift_session_id,
        )
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shift session not found")
        summary = (await self._workforce_repo.summarize_shift_sessions(shift_session_ids=[record.id])).get(record.id)
        return serialize_shift_session(record, summary=summary)

    async def close_shift_session(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        shift_session_id: str,
        actor_user_id: str,
        closing_note: str | None,
    ) -> dict[str, object]:
        record = await self._workforce_repo.get_branch_shift_session(
            tenant_id=tenant_id,
            branch_id=branch_id,
            shift_session_id=shift_session_id,
        )
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shift session not found")
        if record.status != "OPEN":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only open shift sessions can be closed")
        open_attendance_sessions = await self._workforce_repo.get_open_attendance_sessions_by_shift_session(
            tenant_id=tenant_id,
            branch_id=branch_id,
            shift_session_id=shift_session_id,
        )
        if open_attendance_sessions:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Close linked attendance sessions before closing the shift.")
        open_cashier_sessions = await self._workforce_repo.get_open_cashier_sessions_by_shift_session(
            tenant_id=tenant_id,
            branch_id=branch_id,
            shift_session_id=shift_session_id,
        )
        if open_cashier_sessions:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Close linked cashier sessions before closing the shift.")
        closed_at = utc_now()
        await self._workforce_repo.close_branch_shift_session(
            shift_session=record,
            closed_by_user_id=actor_user_id,
            status="CLOSED",
            closing_note=closing_note,
            force_close_reason=None,
            closed_at=closed_at,
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="shift_session.closed",
            entity_type="branch_shift_session",
            entity_id=record.id,
            payload={"shift_number": record.shift_number},
        )
        await self._session.commit()
        return await self.get_shift_session(tenant_id=tenant_id, branch_id=branch_id, shift_session_id=shift_session_id)

    async def force_close_shift_session(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        shift_session_id: str,
        actor_user_id: str,
        reason: str,
    ) -> dict[str, object]:
        record = await self._workforce_repo.get_branch_shift_session(
            tenant_id=tenant_id,
            branch_id=branch_id,
            shift_session_id=shift_session_id,
        )
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shift session not found")
        if record.status != "OPEN":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only open shift sessions can be force-closed")
        open_attendance_sessions = await self._workforce_repo.get_open_attendance_sessions_by_shift_session(
            tenant_id=tenant_id,
            branch_id=branch_id,
            shift_session_id=shift_session_id,
        )
        if open_attendance_sessions:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Force-close linked attendance sessions before force-closing the shift.")
        open_cashier_sessions = await self._workforce_repo.get_open_cashier_sessions_by_shift_session(
            tenant_id=tenant_id,
            branch_id=branch_id,
            shift_session_id=shift_session_id,
        )
        if open_cashier_sessions:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Force-close linked cashier sessions before force-closing the shift.")
        closed_at = utc_now()
        await self._workforce_repo.close_branch_shift_session(
            shift_session=record,
            closed_by_user_id=actor_user_id,
            status="FORCED_CLOSED",
            closing_note=record.closing_note,
            force_close_reason=reason,
            closed_at=closed_at,
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="shift_session.force_closed",
            entity_type="branch_shift_session",
            entity_id=record.id,
            payload={"shift_number": record.shift_number, "reason": reason},
        )
        await self._session.commit()
        return await self.get_shift_session(tenant_id=tenant_id, branch_id=branch_id, shift_session_id=shift_session_id)

    async def list_workforce_audit_events(
        self,
        *,
        tenant_id: str,
        branch_id: str,
    ) -> list[dict[str, object]]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
        events = await self._audit_repo.list_for_tenant(
            tenant_id,
            branch_id=branch_id,
            action_prefixes=(
                "branch_runtime_policy.",
                "shift_session.",
                "attendance_session.",
                "cashier_session.",
            ),
        )
        return [
            {
                "id": event.id,
                "action": event.action,
                "entity_type": event.entity_type,
                "entity_id": event.entity_id,
                "tenant_id": event.tenant_id,
                "branch_id": event.branch_id,
                "created_at": event.created_at,
                "payload": event.payload,
            }
            for event in events
        ]

    async def export_workforce_audit_events(
        self,
        *,
        tenant_id: str,
        branch_id: str,
    ) -> dict[str, str]:
        events = await self.list_workforce_audit_events(tenant_id=tenant_id, branch_id=branch_id)
        buffer = io.StringIO()
        writer = csv.writer(buffer, lineterminator="\n")
        writer.writerow(["created_at", "action", "entity_type", "entity_id", "branch_id", "payload"])
        for event in events:
            writer.writerow(
                [
                    event["created_at"].isoformat(),
                    event["action"],
                    event["entity_type"],
                    event["entity_id"],
                    event["branch_id"],
                    event["payload"],
                ]
            )
        issued_at = utc_now().strftime("%Y%m%d-%H%M%S")
        return {
            "filename": f"workforce-audit-{issued_at}.csv",
            "content_type": "text/csv",
            "content": buffer.getvalue(),
        }

    async def create_cashier_session(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        actor_user_id: str,
        device_registration_id: str,
        staff_profile_id: str,
        opening_float_amount: float,
        opening_note: str | None,
    ) -> dict[str, object]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
        device = await self._workforce_repo.get_device_registration(
            tenant_id=tenant_id,
            branch_id=branch_id,
            device_id=device_registration_id,
        )
        if device is None or device.status != "ACTIVE" or device.session_surface != "store_desktop":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device registration not found")
        profile = await self._workforce_repo.get_staff_profile_by_id(
            tenant_id=tenant_id,
            staff_profile_id=staff_profile_id,
        )
        if profile is None or profile.status != "ACTIVE":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff profile not found")
        actor_user = await self._identity_repo.get_user_by_id(actor_user_id)
        if actor_user is None or actor_user.email != profile.email:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cashier session must match the active staff profile")
        if profile.user_id is None:
            await self._workforce_repo.bind_profiles_for_user(
                email=profile.email,
                user_id=actor_user.id,
                full_name=profile.full_name,
            )
        elif profile.user_id != actor_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cashier session must match the active staff profile")
        branch_runtime_policy = await self._resolve_branch_runtime_policy(tenant_id=tenant_id, branch_id=branch_id)
        if branch_runtime_policy["require_assigned_staff_for_device"] and device.assigned_staff_profile_id != staff_profile_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Device registration is not assigned to this staff profile")

        existing_device_session = await self._workforce_repo.get_open_cashier_session_by_device(
            tenant_id=tenant_id,
            branch_id=branch_id,
            device_registration_id=device_registration_id,
        )
        if existing_device_session is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A cashier session is already open for this device")
        existing_staff_session = await self._workforce_repo.get_open_cashier_session_by_staff_profile(
            tenant_id=tenant_id,
            branch_id=branch_id,
            staff_profile_id=staff_profile_id,
        )
        if existing_staff_session is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A cashier session is already open for this staff profile")
        open_attendance_session = await self._workforce_repo.get_open_attendance_session_by_device(
            tenant_id=tenant_id,
            branch_id=branch_id,
            device_registration_id=device_registration_id,
        )
        attendance_session = None
        if (
            open_attendance_session is not None
            and open_attendance_session.staff_profile_id == staff_profile_id
            and open_attendance_session.runtime_user_id == actor_user_id
        ):
            attendance_session = open_attendance_session
        if branch_runtime_policy["require_attendance_for_cashier"] and attendance_session is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Open an attendance session before opening a cashier session.",
            )

        opened_at = utc_now()
        sequence_number = await self._workforce_repo.next_branch_cashier_session_sequence(
            tenant_id=tenant_id,
            branch_id=branch_id,
        )
        record = await self._workforce_repo.create_branch_cashier_session(
            tenant_id=tenant_id,
            branch_id=branch_id,
            attendance_session_id=attendance_session.id,
            device_registration_id=device_registration_id,
            staff_profile_id=staff_profile_id,
            runtime_user_id=actor_user_id,
            opened_by_user_id=actor_user_id,
            session_number=cashier_session_number(branch_code=branch.code, sequence_number=sequence_number),
            opening_float_amount=round(float(opening_float_amount), 2),
            opening_note=opening_note,
            opened_at=opened_at,
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="cashier_session.opened",
            entity_type="branch_cashier_session",
            entity_id=record.id,
            payload={
                "device_registration_id": device_registration_id,
                "staff_profile_id": staff_profile_id,
                "session_number": record.session_number,
            },
        )
        await self._session.commit()
        return serialize_cashier_session(record, device=device, staff_profile=profile)

    async def create_attendance_session(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        actor_user_id: str,
        device_registration_id: str,
        staff_profile_id: str,
        clock_in_note: str | None,
    ) -> dict[str, object]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
        device = await self._workforce_repo.get_device_registration(
            tenant_id=tenant_id,
            branch_id=branch_id,
            device_id=device_registration_id,
        )
        if device is None or device.status != "ACTIVE":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device registration not found")
        profile = await self._workforce_repo.get_staff_profile_by_id(
            tenant_id=tenant_id,
            staff_profile_id=staff_profile_id,
        )
        if profile is None or profile.status != "ACTIVE":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff profile not found")
        actor_user = await self._identity_repo.get_user_by_id(actor_user_id)
        if actor_user is None or actor_user.email != profile.email:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Attendance session must match the active staff profile")
        if profile.user_id is None:
            await self._workforce_repo.bind_profiles_for_user(
                email=profile.email,
                user_id=actor_user.id,
                full_name=profile.full_name,
            )
        elif profile.user_id != actor_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Attendance session must match the active staff profile")
        branch_runtime_policy = await self._resolve_branch_runtime_policy(tenant_id=tenant_id, branch_id=branch_id)
        if branch_runtime_policy["require_assigned_staff_for_device"] and device.assigned_staff_profile_id != staff_profile_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Device registration is not assigned to this staff profile")

        existing_device_session = await self._workforce_repo.get_open_attendance_session_by_device(
            tenant_id=tenant_id,
            branch_id=branch_id,
            device_registration_id=device_registration_id,
        )
        if existing_device_session is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An attendance session is already open for this device")
        existing_staff_session = await self._workforce_repo.get_open_attendance_session_by_staff_profile(
            tenant_id=tenant_id,
            branch_id=branch_id,
            staff_profile_id=staff_profile_id,
        )
        if existing_staff_session is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An attendance session is already open for this staff profile")
        open_shift_session = await self._workforce_repo.get_open_shift_session(
            tenant_id=tenant_id,
            branch_id=branch_id,
        )
        if branch_runtime_policy["require_shift_for_attendance"] and open_shift_session is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Open a shift session before opening attendance.",
            )

        opened_at = utc_now()
        sequence_number = await self._workforce_repo.next_branch_attendance_session_sequence(
            tenant_id=tenant_id,
            branch_id=branch_id,
        )
        record = await self._workforce_repo.create_branch_attendance_session(
            tenant_id=tenant_id,
            branch_id=branch_id,
            shift_session_id=open_shift_session.id if open_shift_session is not None else None,
            device_registration_id=device_registration_id,
            staff_profile_id=staff_profile_id,
            runtime_user_id=actor_user_id,
            opened_by_user_id=actor_user_id,
            attendance_number=attendance_session_number(branch_code=branch.code, sequence_number=sequence_number),
            clock_in_note=clock_in_note,
            opened_at=opened_at,
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="attendance_session.opened",
            entity_type="branch_attendance_session",
            entity_id=record.id,
            payload={
                "device_registration_id": device_registration_id,
                "staff_profile_id": staff_profile_id,
                "attendance_number": record.attendance_number,
                "shift_session_id": record.shift_session_id,
            },
        )
        await self._session.commit()
        return serialize_attendance_session(record, device=device, staff_profile=profile)

    async def list_branch_attendance_sessions(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        status: str | None = None,
    ) -> list[dict[str, object]]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
        records = await self._workforce_repo.list_branch_attendance_sessions(
            tenant_id=tenant_id,
            branch_id=branch_id,
            status=status,
        )
        devices_by_id = {
            device.id: device
            for device in await self._workforce_repo.list_branch_devices(tenant_id=tenant_id, branch_id=branch_id)
        }
        staff_profiles_by_id = {
            profile.id: profile
            for profile in await self._workforce_repo.list_staff_profiles(tenant_id=tenant_id)
        }
        summaries = await self._workforce_repo.summarize_attendance_sessions(
            attendance_session_ids=[record.id for record in records]
        )
        return [
            serialize_attendance_session(
                record,
                device=devices_by_id.get(record.device_registration_id),
                staff_profile=staff_profiles_by_id.get(record.staff_profile_id),
                summary=summaries.get(record.id),
            )
            for record in records
        ]

    async def get_attendance_session(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        attendance_session_id: str,
    ) -> dict[str, object]:
        record = await self._workforce_repo.get_branch_attendance_session(
            tenant_id=tenant_id,
            branch_id=branch_id,
            attendance_session_id=attendance_session_id,
        )
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attendance session not found")
        device = await self._workforce_repo.get_device_registration(
            tenant_id=tenant_id,
            branch_id=branch_id,
            device_id=record.device_registration_id,
        )
        profile = await self._workforce_repo.get_staff_profile_by_id(
            tenant_id=tenant_id,
            staff_profile_id=record.staff_profile_id,
        )
        summary = (await self._workforce_repo.summarize_attendance_sessions(attendance_session_ids=[record.id])).get(record.id)
        return serialize_attendance_session(record, device=device, staff_profile=profile, summary=summary)

    async def close_attendance_session(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        attendance_session_id: str,
        actor_user_id: str,
        clock_out_note: str | None,
    ) -> dict[str, object]:
        record = await self._workforce_repo.get_branch_attendance_session(
            tenant_id=tenant_id,
            branch_id=branch_id,
            attendance_session_id=attendance_session_id,
        )
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attendance session not found")
        if record.status != "OPEN":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only open attendance sessions can be closed")
        if record.runtime_user_id != actor_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the active cashier can close this attendance session")
        open_cashier_session = await self._workforce_repo.get_open_cashier_session_by_attendance_session(
            tenant_id=tenant_id,
            branch_id=branch_id,
            attendance_session_id=attendance_session_id,
        )
        if open_cashier_session is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Close the linked cashier session before clocking out.",
            )
        closed_at = utc_now()
        await self._workforce_repo.close_branch_attendance_session(
            attendance_session=record,
            closed_by_user_id=actor_user_id,
            status="CLOSED",
            clock_out_note=clock_out_note,
            force_close_reason=None,
            closed_at=closed_at,
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="attendance_session.closed",
            entity_type="branch_attendance_session",
            entity_id=record.id,
            payload={"attendance_number": record.attendance_number},
        )
        await self._session.commit()
        return await self.get_attendance_session(
            tenant_id=tenant_id,
            branch_id=branch_id,
            attendance_session_id=attendance_session_id,
        )

    async def force_close_attendance_session(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        attendance_session_id: str,
        actor_user_id: str,
        reason: str,
    ) -> dict[str, object]:
        record = await self._workforce_repo.get_branch_attendance_session(
            tenant_id=tenant_id,
            branch_id=branch_id,
            attendance_session_id=attendance_session_id,
        )
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attendance session not found")
        if record.status != "OPEN":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only open attendance sessions can be force-closed")
        open_cashier_session = await self._workforce_repo.get_open_cashier_session_by_attendance_session(
            tenant_id=tenant_id,
            branch_id=branch_id,
            attendance_session_id=attendance_session_id,
        )
        if open_cashier_session is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Force-close the linked cashier session before force-closing attendance.",
            )
        closed_at = utc_now()
        await self._workforce_repo.close_branch_attendance_session(
            attendance_session=record,
            closed_by_user_id=actor_user_id,
            status="FORCED_CLOSED",
            clock_out_note=record.clock_out_note,
            force_close_reason=reason,
            closed_at=closed_at,
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="attendance_session.force_closed",
            entity_type="branch_attendance_session",
            entity_id=record.id,
            payload={"attendance_number": record.attendance_number, "reason": reason},
        )
        await self._session.commit()
        return await self.get_attendance_session(
            tenant_id=tenant_id,
            branch_id=branch_id,
            attendance_session_id=attendance_session_id,
        )

    async def list_branch_cashier_sessions(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        status: str | None = None,
    ) -> list[dict[str, object]]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
        records = await self._workforce_repo.list_branch_cashier_sessions(
            tenant_id=tenant_id,
            branch_id=branch_id,
            status=status,
        )
        devices_by_id = {
            device.id: device
            for device in await self._workforce_repo.list_branch_devices(tenant_id=tenant_id, branch_id=branch_id)
        }
        staff_profiles_by_id = {
            profile.id: profile
            for profile in await self._workforce_repo.list_staff_profiles(tenant_id=tenant_id)
        }
        summaries = await self._workforce_repo.summarize_cashier_sessions(
            cashier_session_ids=[record.id for record in records]
        )
        return [
            serialize_cashier_session(
                record,
                device=devices_by_id.get(record.device_registration_id),
                staff_profile=staff_profiles_by_id.get(record.staff_profile_id),
                summary=summaries.get(record.id),
            )
            for record in records
        ]

    async def get_cashier_session(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        cashier_session_id: str,
    ) -> dict[str, object]:
        record = await self._workforce_repo.get_branch_cashier_session(
            tenant_id=tenant_id,
            branch_id=branch_id,
            cashier_session_id=cashier_session_id,
        )
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cashier session not found")
        device = await self._workforce_repo.get_device_registration(
            tenant_id=tenant_id,
            branch_id=branch_id,
            device_id=record.device_registration_id,
        )
        profile = await self._workforce_repo.get_staff_profile_by_id(
            tenant_id=tenant_id,
            staff_profile_id=record.staff_profile_id,
        )
        summary = (await self._workforce_repo.summarize_cashier_sessions(cashier_session_ids=[record.id])).get(record.id)
        return serialize_cashier_session(record, device=device, staff_profile=profile, summary=summary)

    async def close_cashier_session(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        cashier_session_id: str,
        actor_user_id: str,
        closing_note: str | None,
    ) -> dict[str, object]:
        record = await self._workforce_repo.get_branch_cashier_session(
            tenant_id=tenant_id,
            branch_id=branch_id,
            cashier_session_id=cashier_session_id,
        )
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cashier session not found")
        if record.status != "OPEN":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only open cashier sessions can be closed")
        if record.runtime_user_id != actor_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the active cashier can close this session")
        closed_at = utc_now()
        await self._workforce_repo.close_branch_cashier_session(
            cashier_session=record,
            closed_by_user_id=actor_user_id,
            status="CLOSED",
            closing_note=closing_note,
            force_close_reason=None,
            closed_at=closed_at,
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="cashier_session.closed",
            entity_type="branch_cashier_session",
            entity_id=record.id,
            payload={"session_number": record.session_number},
        )
        await self._session.commit()
        return await self.get_cashier_session(
            tenant_id=tenant_id,
            branch_id=branch_id,
            cashier_session_id=cashier_session_id,
        )

    async def force_close_cashier_session(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        cashier_session_id: str,
        actor_user_id: str,
        reason: str,
    ) -> dict[str, object]:
        record = await self._workforce_repo.get_branch_cashier_session(
            tenant_id=tenant_id,
            branch_id=branch_id,
            cashier_session_id=cashier_session_id,
        )
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cashier session not found")
        if record.status != "OPEN":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only open cashier sessions can be force-closed")
        closed_at = utc_now()
        await self._workforce_repo.close_branch_cashier_session(
            cashier_session=record,
            closed_by_user_id=actor_user_id,
            status="FORCED_CLOSED",
            closing_note=record.closing_note,
            force_close_reason=reason,
            closed_at=closed_at,
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="cashier_session.force_closed",
            entity_type="branch_cashier_session",
            entity_id=record.id,
            payload={"session_number": record.session_number, "reason": reason},
        )
        await self._session.commit()
        return await self.get_cashier_session(
            tenant_id=tenant_id,
            branch_id=branch_id,
            cashier_session_id=cashier_session_id,
        )

    async def require_open_cashier_session(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        cashier_session_id: str,
        actor_user_id: str | None,
    ):
        record = await self._workforce_repo.get_branch_cashier_session(
            tenant_id=tenant_id,
            branch_id=branch_id,
            cashier_session_id=cashier_session_id,
        )
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cashier session not found")
        if record.status != "OPEN":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cashier session is not open")
        if actor_user_id is not None and record.runtime_user_id != actor_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cashier session does not belong to the active actor")
        return record

    async def touch_cashier_session_activity(self, *, cashier_session, activity_at=None) -> None:
        await self._workforce_repo.touch_branch_cashier_session_activity(
            cashier_session=cashier_session,
            activity_at=activity_at or utc_now(),
        )

    async def resolve_runtime_device_claim(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        actor_user_id: str,
        installation_id: str,
        runtime_kind: str,
        hostname: str | None,
        operating_system: str | None,
        architecture: str | None,
        app_version: str | None,
    ) -> dict[str, object]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")

        claim_code = build_device_claim_code(installation_id)
        seen_at = utc_now()
        claim = await self._workforce_repo.get_device_claim_by_installation_id(
            tenant_id=tenant_id,
            branch_id=branch_id,
            installation_id=installation_id,
        )
        if claim is None:
            claim = await self._workforce_repo.create_device_claim(
                tenant_id=tenant_id,
                branch_id=branch_id,
                installation_id=installation_id,
                claim_code=claim_code,
                runtime_kind=runtime_kind,
                hostname=hostname,
                operating_system=operating_system,
                architecture=architecture,
                app_version=app_version,
                seen_at=seen_at,
            )
            await self._audit_repo.record(
                tenant_id=tenant_id,
                branch_id=branch_id,
                actor_user_id=actor_user_id,
                action="runtime_device_claim.created",
                entity_type="device_claim",
                entity_id=claim.id,
                payload={"claim_code": claim.claim_code, "runtime_kind": claim.runtime_kind},
            )
        else:
            await self._workforce_repo.touch_device_claim(
                claim=claim,
                runtime_kind=runtime_kind,
                hostname=hostname,
                operating_system=operating_system,
                architecture=architecture,
                app_version=app_version,
                seen_at=seen_at,
            )
            await self._audit_repo.record(
                tenant_id=tenant_id,
                branch_id=branch_id,
                actor_user_id=actor_user_id,
                action="runtime_device_claim.seen",
                entity_type="device_claim",
                entity_id=claim.id,
                payload={"claim_code": claim.claim_code, "status": claim.status},
            )

        bound_device = None
        if claim.approved_device_id is not None:
            bound_device = await self._workforce_repo.get_device_registration_by_id(device_id=claim.approved_device_id)
        elif claim.status == "APPROVED":
            bound_device = await self._workforce_repo.get_device_registration_by_installation_id(
                tenant_id=tenant_id,
                branch_id=branch_id,
                installation_id=installation_id,
            )
            if bound_device is not None:
                await self._workforce_repo.approve_device_claim(
                    claim=claim,
                    approved_device_id=bound_device.id,
                    approved_by_user_id=claim.approved_by_user_id or actor_user_id,
                    approved_at=claim.approved_at or seen_at,
                )

        await self._session.commit()
        return {
            "claim_id": claim.id,
            "claim_code": claim.claim_code,
            "status": claim.status,
            "bound_device_id": bound_device.id if bound_device is not None else None,
            "bound_device_name": bound_device.device_name if bound_device is not None else None,
            "bound_device_code": bound_device.device_code if bound_device is not None else None,
        }

    async def list_branch_device_claims(self, *, tenant_id: str, branch_id: str) -> list[dict[str, object]]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
        claims = await self._workforce_repo.list_branch_device_claims(tenant_id=tenant_id, branch_id=branch_id)
        devices = {
            device.id: device
            for device in await self._workforce_repo.list_branch_devices(tenant_id=tenant_id, branch_id=branch_id)
        }
        return [serialize_device_claim(claim, devices.get(claim.approved_device_id)) for claim in claims]

    async def approve_device_claim(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        claim_id: str,
        actor_user_id: str,
        assigned_staff_profile_id: str | None,
        device_name: str,
        device_code: str,
        session_surface: str,
        runtime_profile: str | None = None,
        is_branch_hub: bool = False,
    ) -> dict[str, object]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
        claim = await self._workforce_repo.get_device_claim_by_id(
            tenant_id=tenant_id,
            branch_id=branch_id,
            claim_id=claim_id,
        )
        if claim is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device claim not found")
        if assigned_staff_profile_id is not None:
            profile = await self._workforce_repo.get_staff_profile_by_id(
                tenant_id=tenant_id,
                staff_profile_id=assigned_staff_profile_id,
            )
            if profile is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff profile not found")

        device = None
        sync_access_secret: str | None = None
        if claim.approved_device_id is not None:
            device = await self._workforce_repo.get_device_registration_by_id(device_id=claim.approved_device_id)
        if device is None:
            device = await self._workforce_repo.get_device_registration_by_installation_id(
                tenant_id=tenant_id,
                branch_id=branch_id,
                installation_id=claim.installation_id,
            )
        if is_branch_hub:
            existing_hub = await self._workforce_repo.get_branch_hub_device(tenant_id=tenant_id, branch_id=branch_id)
            if existing_hub is not None and (device is None or existing_hub.id != device.id):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Branch hub already registered")
            if device is not None and not device.is_branch_hub:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Existing approved device is not registered as branch hub",
                )
        if device is None:
            existing_code = await self._workforce_repo.get_device_registration_by_code(
                tenant_id=tenant_id,
                branch_id=branch_id,
                device_code=device_code,
            )
            if existing_code is not None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Device code already registered")
            resolved_runtime_profile = resolve_device_runtime_profile(
                session_surface=session_surface,
                is_branch_hub=is_branch_hub,
                runtime_profile=runtime_profile,
            )
            sync_access_secret = secrets.token_urlsafe(24) if is_branch_hub else None
            device = await self._workforce_repo.create_device_registration(
                tenant_id=tenant_id,
                branch_id=branch_id,
                assigned_staff_profile_id=assigned_staff_profile_id,
                installation_id=claim.installation_id,
                device_name=device_name,
                device_code=device_code,
                session_surface=session_surface,
                runtime_profile=resolved_runtime_profile,
                is_branch_hub=is_branch_hub,
                sync_secret_hash=hash_sync_access_secret(sync_access_secret) if sync_access_secret else None,
                sync_secret_issued_at=utc_now() if sync_access_secret else None,
            )
            await self._audit_repo.record(
                tenant_id=tenant_id,
                branch_id=branch_id,
                actor_user_id=actor_user_id,
                action="device.registered",
                entity_type="device_registration",
                entity_id=device.id,
                payload={
                    "device_code": device.device_code,
                    "session_surface": device.session_surface,
                    "runtime_profile": device.runtime_profile,
                    "is_branch_hub": device.is_branch_hub,
                    "installation_id": device.installation_id,
                    "approved_from_claim": claim.id,
                },
            )

        approved_at = utc_now()
        await self._workforce_repo.approve_device_claim(
            claim=claim,
            approved_device_id=device.id,
            approved_by_user_id=actor_user_id,
            approved_at=approved_at,
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="runtime_device_claim.approved",
            entity_type="device_claim",
            entity_id=claim.id,
            payload={"claim_code": claim.claim_code, "device_id": device.id},
        )
        await self._session.commit()
        return {
            "claim": serialize_device_claim(claim, device),
            "device": {
                "id": device.id,
                "tenant_id": device.tenant_id,
                "branch_id": device.branch_id,
                "device_name": device.device_name,
                "device_code": device.device_code,
                "session_surface": device.session_surface,
                "runtime_profile": device.runtime_profile,
                "is_branch_hub": device.is_branch_hub,
                "status": device.status,
                "assigned_staff_profile_id": device.assigned_staff_profile_id,
                "installation_id": device.installation_id,
                "sync_access_secret": sync_access_secret,
            },
        }

    async def issue_store_desktop_activation(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        device_id: str,
        actor_user_id: str,
    ) -> dict[str, object]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")

        device = await self._workforce_repo.get_device_registration(
            tenant_id=tenant_id,
            branch_id=branch_id,
            device_id=device_id,
        )
        if device is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
        if device.status != "ACTIVE" or device.session_surface != "store_desktop" or not device.installation_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Approved packaged store desktop device required",
            )
        await self._commercial_access.assert_runtime_activation_allowed(tenant_id=device.tenant_id)
        if not device.assigned_staff_profile_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assigned staff profile required before issuing desktop activation",
            )

        profile = await self._workforce_repo.get_staff_profile_by_id(
            tenant_id=tenant_id,
            staff_profile_id=device.assigned_staff_profile_id,
        )
        if profile is None or profile.status != "ACTIVE":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff profile not found")

        await self._workforce_repo.supersede_store_desktop_activations(device_id=device.id)
        activation_version = await self._workforce_repo.get_next_store_desktop_activation_version(device_id=device.id)
        activation_code = build_store_desktop_activation_code()
        activation = await self._workforce_repo.create_store_desktop_activation(
            tenant_id=tenant_id,
            branch_id=branch_id,
            device_id=device.id,
            staff_profile_id=profile.id,
            activation_code_hash=hash_store_desktop_activation_code(activation_code),
            activation_version=activation_version,
            issued_by_user_id=actor_user_id,
            expires_at=utc_now() + timedelta(minutes=STORE_DESKTOP_ACTIVATION_TTL_MINUTES),
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="device.desktop_activation.issued",
            entity_type="store_desktop_activation",
            entity_id=activation.id,
            payload={"device_id": device.id, "staff_profile_id": profile.id},
        )
        await self._session.commit()
        return {
            "device_id": device.id,
            "staff_profile_id": profile.id,
            "activation_code": activation_code,
            "status": activation.status,
            "expires_at": activation.expires_at.isoformat(),
        }

    async def issue_runtime_activation(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        device_id: str,
        actor_user_id: str,
    ) -> dict[str, object]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")

        device = await self._workforce_repo.get_device_registration(
            tenant_id=tenant_id,
            branch_id=branch_id,
            device_id=device_id,
        )
        if device is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
        if device.status != "ACTIVE" or device.session_surface == "store_desktop" or not device.installation_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Approved non-desktop runtime device required",
            )
        await self._commercial_access.assert_runtime_activation_allowed(tenant_id=device.tenant_id)
        if not device.assigned_staff_profile_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assigned staff profile required before issuing runtime activation",
            )

        profile = await self._workforce_repo.get_staff_profile_by_id(
            tenant_id=tenant_id,
            staff_profile_id=device.assigned_staff_profile_id,
        )
        if profile is None or profile.status != "ACTIVE":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff profile not found")

        await self._workforce_repo.supersede_runtime_device_activations(device_id=device.id)
        activation_version = await self._workforce_repo.get_next_runtime_device_activation_version(device_id=device.id)
        activation_code = build_store_desktop_activation_code()
        activation = await self._workforce_repo.create_runtime_device_activation(
            tenant_id=tenant_id,
            branch_id=branch_id,
            device_id=device.id,
            staff_profile_id=profile.id,
            activation_code_hash=hash_store_desktop_activation_code(activation_code),
            activation_version=activation_version,
            issued_by_user_id=actor_user_id,
            expires_at=utc_now() + timedelta(minutes=STORE_DESKTOP_ACTIVATION_TTL_MINUTES),
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="device.runtime_activation.issued",
            entity_type="runtime_activation",
            entity_id=activation.id,
            payload={
                "device_id": device.id,
                "staff_profile_id": profile.id,
                "session_surface": device.session_surface,
                "runtime_profile": device.runtime_profile,
            },
        )
        await self._session.commit()
        return {
            "device_id": device.id,
            "staff_profile_id": profile.id,
            "activation_code": activation_code,
            "status": activation.status,
            "expires_at": activation.expires_at.isoformat(),
            "runtime_profile": device.runtime_profile,
            "session_surface": device.session_surface,
        }

    async def redeem_store_desktop_activation(
        self,
        *,
        installation_id: str,
        activation_code: str,
        session_ttl_minutes: int,
    ) -> dict[str, object]:
        device = await self._workforce_repo.get_device_registration_by_installation_id_global(
            installation_id=installation_id,
        )
        if device is None or device.status != "ACTIVE" or device.session_surface != "store_desktop":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Desktop activation is invalid")
        access = await self._commercial_access.assert_runtime_activation_allowed(tenant_id=device.tenant_id)

        activation = await self._workforce_repo.get_store_desktop_activation(
            device_id=device.id,
            activation_code_hash=hash_store_desktop_activation_code(activation_code),
        )
        if activation is None or activation.expires_at < utc_now():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Desktop activation is invalid")

        profile = await self._workforce_repo.get_staff_profile_by_id(
            tenant_id=device.tenant_id,
            staff_profile_id=activation.staff_profile_id,
        )
        if profile is None or profile.status != "ACTIVE":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Desktop activation is invalid")
        runtime_user = await self._resolve_runtime_user_for_profile(
            profile=profile,
            synthetic_subject=build_runtime_user_subject(
                session_surface=device.session_surface,
                staff_profile_id=profile.id,
            ),
            provider=f"{device.session_surface}_activation",
        )
        await self._assert_runtime_branch_membership(runtime_user_id=runtime_user.id, device=device)

        redeemed_at = utc_now()
        local_auth_token = build_store_desktop_local_auth_token()
        offline_hours = self._commercial_access.resolve_offline_runtime_hours(
            access=access,
            fallback_hours=STORE_DESKTOP_OFFLINE_UNLOCK_TTL_HOURS,
        )
        offline_valid_until = redeemed_at + timedelta(hours=offline_hours)
        await self._workforce_repo.redeem_store_desktop_activation(
            activation=activation,
            local_auth_token_hash=hash_store_desktop_local_auth_token(local_auth_token),
            redeemed_at=redeemed_at,
            offline_valid_until=offline_valid_until,
        )
        session_record = await self._identity_repo.create_session(
            user_id=runtime_user.id,
            ttl_minutes=session_ttl_minutes,
        )
        await self._audit_repo.record(
            tenant_id=device.tenant_id,
            branch_id=device.branch_id,
            actor_user_id=runtime_user.id,
            action="device.desktop_activation.redeemed",
            entity_type="store_desktop_activation",
            entity_id=activation.id,
            payload={"device_id": device.id, "staff_profile_id": profile.id},
        )
        await self._session.commit()
        return {
            "access_token": session_record.token,
            "token_type": "Bearer",
            "expires_at": session_record.expires_at.isoformat(),
            "device_id": device.id,
            "staff_profile_id": profile.id,
            "local_auth_token": local_auth_token,
            "offline_valid_until": offline_valid_until.isoformat(),
            "activation_version": activation.activation_version,
        }

    async def redeem_runtime_activation(
        self,
        *,
        installation_id: str,
        activation_code: str,
        session_ttl_minutes: int,
    ) -> dict[str, object]:
        device = await self._workforce_repo.get_device_registration_by_installation_id_global(
            installation_id=installation_id,
        )
        if device is None or device.status != "ACTIVE" or device.session_surface == "store_desktop":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Runtime activation is invalid")
        await self._commercial_access.assert_runtime_activation_allowed(tenant_id=device.tenant_id)

        activation = await self._workforce_repo.get_runtime_device_activation(
            device_id=device.id,
            activation_code_hash=hash_store_desktop_activation_code(activation_code),
        )
        if activation is None or activation.expires_at < utc_now():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Runtime activation is invalid")

        profile = await self._workforce_repo.get_staff_profile_by_id(
            tenant_id=device.tenant_id,
            staff_profile_id=activation.staff_profile_id,
        )
        if profile is None or profile.status != "ACTIVE":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Runtime activation is invalid")
        runtime_user = await self._resolve_runtime_user_for_profile(
            profile=profile,
            synthetic_subject=build_runtime_user_subject(
                session_surface=device.session_surface,
                staff_profile_id=profile.id,
            ),
            provider=f"{device.session_surface}_activation",
        )
        await self._assert_runtime_branch_membership(runtime_user_id=runtime_user.id, device=device)

        redeemed_at = utc_now()
        session_record = await self._identity_repo.create_session(
            user_id=runtime_user.id,
            ttl_minutes=session_ttl_minutes,
        )
        activation.status = "ACTIVE"
        activation.redeemed_at = redeemed_at
        await self._audit_repo.record(
            tenant_id=device.tenant_id,
            branch_id=device.branch_id,
            actor_user_id=runtime_user.id,
            action="device.runtime_activation.redeemed",
            entity_type="runtime_activation",
            entity_id=activation.id,
            payload={
                "device_id": device.id,
                "staff_profile_id": profile.id,
                "session_surface": device.session_surface,
                "runtime_profile": device.runtime_profile,
            },
        )
        await self._session.commit()
        return {
            "access_token": session_record.token,
            "token_type": "Bearer",
            "expires_at": session_record.expires_at.isoformat(),
            "device_id": device.id,
            "staff_profile_id": profile.id,
            "runtime_profile": device.runtime_profile,
            "session_surface": device.session_surface,
        }

    async def unlock_store_desktop_runtime(
        self,
        *,
        installation_id: str,
        local_auth_token: str,
        session_ttl_minutes: int,
    ) -> dict[str, object]:
        device = await self._workforce_repo.get_device_registration_by_installation_id_global(
            installation_id=installation_id,
        )
        if device is None or device.status != "ACTIVE" or device.session_surface != "store_desktop":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Store desktop unlock is invalid")
        access = await self._commercial_access.assert_runtime_session_allowed(tenant_id=device.tenant_id)

        activation = await self._workforce_repo.get_active_store_desktop_activation_by_local_auth_token(
            device_id=device.id,
            local_auth_token_hash=hash_store_desktop_local_auth_token(local_auth_token),
        )
        if activation is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Store desktop unlock is invalid")

        profile = await self._workforce_repo.get_staff_profile_by_id(
            tenant_id=device.tenant_id,
            staff_profile_id=activation.staff_profile_id,
        )
        if profile is None or profile.status != "ACTIVE":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Store desktop unlock is invalid")

        runtime_user = await self._resolve_runtime_user_for_profile(
            profile=profile,
            synthetic_subject=build_runtime_user_subject(
                session_surface=device.session_surface,
                staff_profile_id=profile.id,
            ),
            provider=f"{device.session_surface}_activation",
        )
        await self._assert_runtime_branch_membership(runtime_user_id=runtime_user.id, device=device)

        unlocked_at = utc_now()
        offline_hours = self._commercial_access.resolve_offline_runtime_hours(
            access=access,
            fallback_hours=STORE_DESKTOP_OFFLINE_UNLOCK_TTL_HOURS,
        )
        offline_valid_until = unlocked_at + timedelta(hours=offline_hours)
        await self._workforce_repo.touch_store_desktop_activation_unlock(
            activation=activation,
            unlocked_at=unlocked_at,
            offline_valid_until=offline_valid_until,
        )
        session_record = await self._identity_repo.create_session(
            user_id=runtime_user.id,
            ttl_minutes=session_ttl_minutes,
        )
        await self._audit_repo.record(
            tenant_id=device.tenant_id,
            branch_id=device.branch_id,
            actor_user_id=runtime_user.id,
            action="device.desktop_activation.unlocked",
            entity_type="store_desktop_activation",
            entity_id=activation.id,
            payload={"device_id": device.id, "staff_profile_id": profile.id},
        )
        await self._session.commit()
        return {
            "access_token": session_record.token,
            "token_type": "Bearer",
            "expires_at": session_record.expires_at.isoformat(),
            "device_id": device.id,
            "staff_profile_id": profile.id,
            "local_auth_token": local_auth_token,
            "offline_valid_until": offline_valid_until.isoformat(),
            "activation_version": activation.activation_version,
        }
