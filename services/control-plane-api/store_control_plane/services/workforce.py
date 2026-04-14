from __future__ import annotations

import secrets

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories import AuditRepository, MembershipRepository, TenantRepository, WorkforceRepository
from ..utils import utc_now
from .sync_runtime_auth import hash_sync_access_secret


def build_device_claim_code(installation_id: str) -> str:
    normalized = "".join(character for character in installation_id.upper() if character.isalnum())
    suffix = normalized[-8:] if normalized else "UNBOUND00"
    return f"STORE-{suffix}"


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


class WorkforceService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._tenant_repo = TenantRepository(session)
        self._membership_repo = MembershipRepository(session)
        self._workforce_repo = WorkforceRepository(session)
        self._audit_repo = AuditRepository(session)

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
        sync_access_secret = secrets.token_urlsafe(24) if is_branch_hub else None
        device = await self._workforce_repo.create_device_registration(
            tenant_id=tenant_id,
            branch_id=branch_id,
            assigned_staff_profile_id=assigned_staff_profile_id,
            installation_id=installation_id,
            device_name=device_name,
            device_code=device_code,
            session_surface=session_surface,
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
        if claim.approved_device_id is not None:
            device = await self._workforce_repo.get_device_registration_by_id(device_id=claim.approved_device_id)
        if device is None:
            device = await self._workforce_repo.get_device_registration_by_installation_id(
                tenant_id=tenant_id,
                branch_id=branch_id,
                installation_id=claim.installation_id,
            )
        if device is None:
            existing_code = await self._workforce_repo.get_device_registration_by_code(
                tenant_id=tenant_id,
                branch_id=branch_id,
                device_code=device_code,
            )
            if existing_code is not None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Device code already registered")
            device = await self._workforce_repo.create_device_registration(
                tenant_id=tenant_id,
                branch_id=branch_id,
                assigned_staff_profile_id=assigned_staff_profile_id,
                installation_id=claim.installation_id,
                device_name=device_name,
                device_code=device_code,
                session_surface=session_surface,
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
                "is_branch_hub": device.is_branch_hub,
                "status": device.status,
                "assigned_staff_profile_id": device.assigned_staff_profile_id,
                "installation_id": device.installation_id,
                "sync_access_secret": None,
            },
        }
