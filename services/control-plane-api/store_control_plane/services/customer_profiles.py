from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories import CustomerProfileRepository, TenantRepository
from ..utils import new_id
from .purchase_policy import normalize_gstin


def _normalize_name(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _normalize_optional(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _normalize_tags(tags: list[str] | None) -> list[str]:
    if not tags:
        return []
    normalized: list[str] = []
    seen: set[str] = set()
    for tag in tags:
        cleaned = (tag or "").strip()
        if not cleaned:
            continue
        lowered = cleaned.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        normalized.append(cleaned)
    return normalized


class CustomerProfileService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._tenant_repo = TenantRepository(session)
        self._profile_repo = CustomerProfileRepository(session)

    async def list_customer_profiles(
        self,
        *,
        tenant_id: str,
        query: str | None,
        status_filter: str | None,
    ) -> dict[str, object]:
        await self._require_tenant(tenant_id)
        normalized_status = self._normalize_status_filter(status_filter)
        records = await self._profile_repo.list_profiles(
            tenant_id=tenant_id,
            query=_normalize_optional(query),
            status=normalized_status,
        )
        return {"records": [self._serialize_profile(record) for record in records]}

    async def create_customer_profile(
        self,
        *,
        tenant_id: str,
        full_name: str,
        phone: str | None,
        email: str | None,
        gstin: str | None,
        default_note: str | None,
        tags: list[str] | None,
    ) -> dict[str, object]:
        await self._require_tenant(tenant_id)
        normalized_name = _normalize_name(full_name)
        if normalized_name is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Customer full name is required")
        normalized_gstin = normalize_gstin(gstin)
        if normalized_gstin is not None:
            existing = await self._profile_repo.get_profile_by_gstin(tenant_id=tenant_id, gstin=normalized_gstin)
            if existing is not None:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Customer GSTIN already exists")
        record = await self._profile_repo.create_profile(
            tenant_id=tenant_id,
            customer_profile_id=new_id(),
            full_name=normalized_name,
            phone=_normalize_optional(phone),
            email=_normalize_optional(email),
            gstin=normalized_gstin,
            default_note=_normalize_optional(default_note),
            tags=_normalize_tags(tags),
        )
        return self._serialize_profile(record)

    async def get_customer_profile(self, *, tenant_id: str, customer_profile_id: str) -> dict[str, object]:
        await self._require_tenant(tenant_id)
        record = await self._require_profile(tenant_id=tenant_id, customer_profile_id=customer_profile_id)
        return self._serialize_profile(record)

    async def update_customer_profile(
        self,
        *,
        tenant_id: str,
        customer_profile_id: str,
        updates: dict[str, object],
    ) -> dict[str, object]:
        await self._require_tenant(tenant_id)
        record = await self._require_profile(tenant_id=tenant_id, customer_profile_id=customer_profile_id)

        if "full_name" in updates:
            normalized_name = _normalize_name(updates.get("full_name"))
            if normalized_name is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Customer full name is required")
            record.full_name = normalized_name
        if "phone" in updates:
            record.phone = _normalize_optional(updates.get("phone"))
        if "email" in updates:
            record.email = _normalize_optional(updates.get("email"))
        if "default_note" in updates:
            record.default_note = _normalize_optional(updates.get("default_note"))
        if "tags" in updates:
            record.tags = _normalize_tags(updates.get("tags"))
        if "gstin" in updates:
            normalized_gstin = normalize_gstin(updates.get("gstin"))
            if normalized_gstin is not None:
                existing = await self._profile_repo.get_profile_by_gstin(tenant_id=tenant_id, gstin=normalized_gstin)
                if existing is not None and existing.id != record.id:
                    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Customer GSTIN already exists")
            record.gstin = normalized_gstin

        await self._session.flush()
        return self._serialize_profile(record)

    async def archive_customer_profile(self, *, tenant_id: str, customer_profile_id: str) -> dict[str, object]:
        await self._require_tenant(tenant_id)
        record = await self._require_profile(tenant_id=tenant_id, customer_profile_id=customer_profile_id)
        record.status = "ARCHIVED"
        await self._session.flush()
        return self._serialize_profile(record)

    async def reactivate_customer_profile(self, *, tenant_id: str, customer_profile_id: str) -> dict[str, object]:
        await self._require_tenant(tenant_id)
        record = await self._require_profile(tenant_id=tenant_id, customer_profile_id=customer_profile_id)
        record.status = "ACTIVE"
        await self._session.flush()
        return self._serialize_profile(record)

    async def require_active_profile(self, *, tenant_id: str, customer_profile_id: str):
        record = await self._require_profile(tenant_id=tenant_id, customer_profile_id=customer_profile_id)
        if record.status != "ACTIVE":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Customer profile is archived")
        return record

    async def _require_tenant(self, tenant_id: str) -> None:
        tenant = await self._tenant_repo.get_tenant(tenant_id)
        if tenant is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    async def _require_profile(self, *, tenant_id: str, customer_profile_id: str):
        record = await self._profile_repo.get_profile(tenant_id=tenant_id, customer_profile_id=customer_profile_id)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer profile not found")
        return record

    @staticmethod
    def _normalize_status_filter(value: str | None) -> str | None:
        normalized = _normalize_optional(value)
        if normalized is None:
            return None
        upper = normalized.upper()
        if upper not in {"ACTIVE", "ARCHIVED"}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported customer profile status")
        return upper

    @staticmethod
    def _serialize_profile(record) -> dict[str, object]:
        return {
            "id": record.id,
            "tenant_id": record.tenant_id,
            "full_name": record.full_name,
            "phone": record.phone,
            "email": record.email,
            "gstin": record.gstin,
            "default_note": record.default_note,
            "tags": list(record.tags or []),
            "status": record.status,
            "created_at": record.created_at,
            "updated_at": record.updated_at,
        }
