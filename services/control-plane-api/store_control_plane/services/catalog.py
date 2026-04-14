from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories import AuditRepository, CatalogRepository, TenantRepository


class CatalogService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._tenant_repo = TenantRepository(session)
        self._catalog_repo = CatalogRepository(session)
        self._audit_repo = AuditRepository(session)

    async def create_product(
        self,
        *,
        tenant_id: str,
        actor_user_id: str,
        name: str,
        sku_code: str,
        barcode: str,
        hsn_sac_code: str,
        gst_rate: float,
        selling_price: float,
    ):
        tenant = await self._tenant_repo.get_tenant(tenant_id)
        if tenant is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
        product = await self._catalog_repo.create_product(
            tenant_id=tenant_id,
            name=name,
            sku_code=sku_code,
            barcode=barcode,
            hsn_sac_code=hsn_sac_code,
            gst_rate=gst_rate,
            selling_price=selling_price,
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=None,
            actor_user_id=actor_user_id,
            action="catalog_product.created",
            entity_type="catalog_product",
            entity_id=product.id,
            payload={"sku_code": product.sku_code, "barcode": product.barcode},
        )
        await self._session.commit()
        return product

    async def list_products(self, *, tenant_id: str) -> list[dict[str, object]]:
        tenant = await self._tenant_repo.get_tenant(tenant_id)
        if tenant is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
        products = await self._catalog_repo.list_products(tenant_id=tenant_id)
        return [
            {
                "product_id": product.id,
                "tenant_id": product.tenant_id,
                "name": product.name,
                "sku_code": product.sku_code,
                "barcode": product.barcode,
                "hsn_sac_code": product.hsn_sac_code,
                "gst_rate": product.gst_rate,
                "selling_price": product.selling_price,
                "status": product.status,
            }
            for product in products
        ]

    async def upsert_branch_catalog_item(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        actor_user_id: str,
        product_id: str,
        selling_price_override: float | None,
        availability_status: str,
    ) -> dict[str, object]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
        product = await self._catalog_repo.get_product(tenant_id=tenant_id, product_id=product_id)
        if product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Catalog product not found")
        item = await self._catalog_repo.upsert_branch_catalog_item(
            tenant_id=tenant_id,
            branch_id=branch_id,
            product_id=product_id,
            selling_price_override=selling_price_override,
            availability_status=availability_status,
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="branch_catalog_item.upserted",
            entity_type="branch_catalog_item",
            entity_id=item.id,
            payload={"product_id": product_id, "availability_status": availability_status},
        )
        await self._session.commit()
        return {
            "id": item.id,
            "tenant_id": item.tenant_id,
            "branch_id": item.branch_id,
            "product_id": item.product_id,
            "product_name": product.name,
            "sku_code": product.sku_code,
            "barcode": product.barcode,
            "hsn_sac_code": product.hsn_sac_code,
            "gst_rate": product.gst_rate,
            "base_selling_price": product.selling_price,
            "selling_price_override": item.selling_price_override,
            "effective_selling_price": item.selling_price_override if item.selling_price_override is not None else product.selling_price,
            "availability_status": item.availability_status,
        }

    async def list_branch_catalog_items(self, *, tenant_id: str, branch_id: str) -> list[dict[str, object]]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
        products = {
            product.id: product
            for product in await self._catalog_repo.list_products(tenant_id=tenant_id)
        }
        items = await self._catalog_repo.list_branch_catalog_items(tenant_id=tenant_id, branch_id=branch_id)
        records: list[dict[str, object]] = []
        for item in items:
            product = products.get(item.product_id)
            if product is None:
                continue
            records.append(
                {
                    "id": item.id,
                    "tenant_id": item.tenant_id,
                    "branch_id": item.branch_id,
                    "product_id": item.product_id,
                    "product_name": product.name,
                    "sku_code": product.sku_code,
                    "barcode": product.barcode,
                    "hsn_sac_code": product.hsn_sac_code,
                    "gst_rate": product.gst_rate,
                    "base_selling_price": product.selling_price,
                    "selling_price_override": item.selling_price_override,
                    "effective_selling_price": item.selling_price_override if item.selling_price_override is not None else product.selling_price,
                    "availability_status": item.availability_status,
                }
            )
        return records
