from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories import CatalogRepository, CustomerProfileRepository, TenantRepository
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
        self._catalog_repo = CatalogRepository(session)
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
        price_tiers = await self._list_price_tier_records(
            tenant_id=tenant_id,
            price_tier_ids=[record.default_price_tier_id for record in records if record.default_price_tier_id],
        )
        return {"records": [self._serialize_profile(record, price_tiers.get(record.default_price_tier_id)) for record in records]}

    async def create_customer_profile(
        self,
        *,
        tenant_id: str,
        full_name: str,
        phone: str | None,
        email: str | None,
        gstin: str | None,
        default_note: str | None,
        default_price_tier_id: str | None,
        tags: list[str] | None,
    ) -> dict[str, object]:
        await self._require_tenant(tenant_id)
        normalized_name = _normalize_name(full_name)
        if normalized_name is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Customer full name is required")
        normalized_gstin = normalize_gstin(gstin)
        price_tier = await self._resolve_assignable_price_tier(tenant_id=tenant_id, price_tier_id=default_price_tier_id)
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
            default_price_tier_id=price_tier.id if price_tier is not None else None,
            tags=_normalize_tags(tags),
        )
        return self._serialize_profile(record, price_tier)

    async def get_customer_profile(self, *, tenant_id: str, customer_profile_id: str) -> dict[str, object]:
        await self._require_tenant(tenant_id)
        record = await self._require_profile(tenant_id=tenant_id, customer_profile_id=customer_profile_id)
        price_tier = await self._get_price_tier_record(tenant_id=tenant_id, price_tier_id=record.default_price_tier_id)
        return self._serialize_profile(record, price_tier)

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
        if "default_price_tier_id" in updates:
            price_tier = await self._resolve_assignable_price_tier(
                tenant_id=tenant_id,
                price_tier_id=updates.get("default_price_tier_id"),
            )
            record.default_price_tier_id = price_tier.id if price_tier is not None else None
        else:
            price_tier = await self._get_price_tier_record(tenant_id=tenant_id, price_tier_id=record.default_price_tier_id)

        await self._session.flush()
        return self._serialize_profile(record, price_tier)

    async def archive_customer_profile(self, *, tenant_id: str, customer_profile_id: str) -> dict[str, object]:
        await self._require_tenant(tenant_id)
        record = await self._require_profile(tenant_id=tenant_id, customer_profile_id=customer_profile_id)
        record.status = "ARCHIVED"
        await self._session.flush()
        price_tier = await self._get_price_tier_record(tenant_id=tenant_id, price_tier_id=record.default_price_tier_id)
        return self._serialize_profile(record, price_tier)

    async def reactivate_customer_profile(self, *, tenant_id: str, customer_profile_id: str) -> dict[str, object]:
        await self._require_tenant(tenant_id)
        record = await self._require_profile(tenant_id=tenant_id, customer_profile_id=customer_profile_id)
        record.status = "ACTIVE"
        await self._session.flush()
        price_tier = await self._get_price_tier_record(tenant_id=tenant_id, price_tier_id=record.default_price_tier_id)
        return self._serialize_profile(record, price_tier)

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

    async def _resolve_assignable_price_tier(self, *, tenant_id: str, price_tier_id: str | None):
        if price_tier_id is None:
            return None
        record = await self._catalog_repo.get_price_tier(tenant_id=tenant_id, price_tier_id=price_tier_id)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Price tier not found")
        if record.status != "ACTIVE":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Customer default price tier must be active")
        return record

    async def _get_price_tier_record(self, *, tenant_id: str, price_tier_id: str | None):
        if price_tier_id is None:
            return None
        return await self._catalog_repo.get_price_tier(tenant_id=tenant_id, price_tier_id=price_tier_id)

    async def _list_price_tier_records(self, *, tenant_id: str, price_tier_ids: list[str]) -> dict[str, object]:
        unique_ids = sorted({price_tier_id for price_tier_id in price_tier_ids if price_tier_id})
        if not unique_ids:
            return {}
        return await self._catalog_repo.list_price_tiers_by_ids(tenant_id=tenant_id, price_tier_ids=unique_ids)

    @staticmethod
    def _serialize_profile(record, price_tier=None) -> dict[str, object]:
        return {
            "id": record.id,
            "tenant_id": record.tenant_id,
            "full_name": record.full_name,
            "phone": record.phone,
            "email": record.email,
            "gstin": record.gstin,
            "default_note": record.default_note,
            "default_price_tier_id": record.default_price_tier_id,
            "default_price_tier_code": price_tier.code if price_tier is not None else None,
            "default_price_tier_display_name": price_tier.display_name if price_tier is not None else None,
            "tags": list(record.tags or []),
            "status": record.status,
            "created_at": record.created_at,
            "updated_at": record.updated_at,
        }
