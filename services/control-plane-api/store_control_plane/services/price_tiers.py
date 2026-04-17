from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories import AuditRepository, CatalogRepository, TenantRepository


def _normalize_code(value: str) -> str:
    normalized = value.strip().upper()
    if not normalized:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Price tier code is required")
    return normalized


def _normalize_display_name(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Price tier display name is required")
    return normalized


def _normalize_status(value: str) -> str:
    normalized = value.strip().upper()
    if normalized not in {"ACTIVE", "DISABLED"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported price tier status")
    return normalized


class PriceTierService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._tenant_repo = TenantRepository(session)
        self._catalog_repo = CatalogRepository(session)
        self._audit_repo = AuditRepository(session)

    async def create_price_tier(
        self,
        *,
        tenant_id: str,
        actor_user_id: str,
        code: str,
        display_name: str,
        status_value: str,
    ) -> dict[str, object]:
        await self._require_tenant(tenant_id)
        normalized_code = _normalize_code(code)
        existing = await self._catalog_repo.get_price_tier_by_code(tenant_id=tenant_id, code=normalized_code)
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Price tier code already exists")
        record = await self._catalog_repo.create_price_tier(
            tenant_id=tenant_id,
            code=normalized_code,
            display_name=_normalize_display_name(display_name),
            status=_normalize_status(status_value),
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=None,
            actor_user_id=actor_user_id,
            action="price_tier.created",
            entity_type="price_tier",
            entity_id=record.id,
            payload={"code": record.code},
        )
        await self._session.commit()
        return self._serialize_price_tier(record)

    async def update_price_tier(
        self,
        *,
        tenant_id: str,
        price_tier_id: str,
        actor_user_id: str,
        display_name: str | None,
        status_value: str | None,
    ) -> dict[str, object]:
        await self._require_tenant(tenant_id)
        record = await self._require_price_tier(tenant_id=tenant_id, price_tier_id=price_tier_id)
        if display_name is not None:
            record.display_name = _normalize_display_name(display_name)
        if status_value is not None:
            record.status = _normalize_status(status_value)
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=None,
            actor_user_id=actor_user_id,
            action="price_tier.updated",
            entity_type="price_tier",
            entity_id=record.id,
            payload={"code": record.code, "status": record.status},
        )
        await self._session.commit()
        return self._serialize_price_tier(record)

    async def list_price_tiers(self, *, tenant_id: str) -> dict[str, object]:
        await self._require_tenant(tenant_id)
        records = await self._catalog_repo.list_price_tiers(tenant_id=tenant_id)
        return {"records": [self._serialize_price_tier(record) for record in records]}

    async def upsert_branch_price_tier_price(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        actor_user_id: str,
        product_id: str,
        price_tier_id: str,
        selling_price: float,
    ) -> dict[str, object]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
        product = await self._catalog_repo.get_product(tenant_id=tenant_id, product_id=product_id)
        if product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Catalog product not found")
        price_tier = await self._require_price_tier(tenant_id=tenant_id, price_tier_id=price_tier_id)
        branch_item_map = {
            item.product_id: item
            for item in await self._catalog_repo.list_branch_catalog_items(tenant_id=tenant_id, branch_id=branch_id)
        }
        branch_item = branch_item_map.get(product_id)
        record = await self._catalog_repo.upsert_branch_price_tier_price(
            tenant_id=tenant_id,
            branch_id=branch_id,
            product_id=product_id,
            price_tier_id=price_tier_id,
            selling_price=selling_price,
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="branch_price_tier_price.upserted",
            entity_type="branch_price_tier_price",
            entity_id=record.id,
            payload={"product_id": product_id, "price_tier_id": price_tier_id},
        )
        await self._session.commit()
        return self._serialize_branch_price_tier_price(
            record=record,
            product=product,
            price_tier=price_tier,
            branch_item=branch_item,
        )

    async def list_branch_price_tier_prices(
        self,
        *,
        tenant_id: str,
        branch_id: str,
    ) -> dict[str, object]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
        products = {
            product.id: product
            for product in await self._catalog_repo.list_products(tenant_id=tenant_id)
        }
        tiers = {
            tier.id: tier
            for tier in await self._catalog_repo.list_price_tiers(tenant_id=tenant_id)
        }
        branch_items = {
            item.product_id: item
            for item in await self._catalog_repo.list_branch_catalog_items(tenant_id=tenant_id, branch_id=branch_id)
        }
        records = await self._catalog_repo.list_branch_price_tier_prices(tenant_id=tenant_id, branch_id=branch_id)
        serialized: list[dict[str, object]] = []
        for record in records:
            product = products.get(record.product_id)
            price_tier = tiers.get(record.price_tier_id)
            if product is None or price_tier is None:
                continue
            serialized.append(
                self._serialize_branch_price_tier_price(
                    record=record,
                    product=product,
                    price_tier=price_tier,
                    branch_item=branch_items.get(record.product_id),
                )
            )
        return {"records": serialized}

    async def _require_tenant(self, tenant_id: str) -> None:
        tenant = await self._tenant_repo.get_tenant(tenant_id)
        if tenant is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    async def _require_price_tier(self, *, tenant_id: str, price_tier_id: str):
        record = await self._catalog_repo.get_price_tier(tenant_id=tenant_id, price_tier_id=price_tier_id)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Price tier not found")
        return record

    @staticmethod
    def _serialize_price_tier(record) -> dict[str, object]:
        return {
            "id": record.id,
            "tenant_id": record.tenant_id,
            "code": record.code,
            "display_name": record.display_name,
            "status": record.status,
            "created_at": record.created_at,
            "updated_at": record.updated_at,
        }

    @staticmethod
    def _serialize_branch_price_tier_price(*, record, product, price_tier, branch_item) -> dict[str, object]:
        effective_base_selling_price = (
            branch_item.selling_price_override
            if branch_item is not None and branch_item.selling_price_override is not None
            else product.selling_price
        )
        return {
            "id": record.id,
            "tenant_id": record.tenant_id,
            "branch_id": record.branch_id,
            "product_id": record.product_id,
            "product_name": product.name,
            "sku_code": product.sku_code,
            "price_tier_id": record.price_tier_id,
            "price_tier_code": price_tier.code,
            "price_tier_display_name": price_tier.display_name,
            "base_selling_price": product.selling_price,
            "effective_base_selling_price": effective_base_selling_price,
            "selling_price": record.selling_price,
            "created_at": record.created_at,
            "updated_at": record.updated_at,
        }
