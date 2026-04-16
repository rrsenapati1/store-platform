from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import BranchCatalogItem, CatalogProduct
from ..utils import new_id


class CatalogRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create_product(
        self,
        *,
        tenant_id: str,
        name: str,
        sku_code: str,
        barcode: str,
        hsn_sac_code: str,
        gst_rate: float,
        mrp: float,
        category_code: str | None,
        selling_price: float,
    ) -> CatalogProduct:
        product = CatalogProduct(
            id=new_id(),
            tenant_id=tenant_id,
            name=name,
            sku_code=sku_code,
            barcode=barcode,
            hsn_sac_code=hsn_sac_code,
            gst_rate=gst_rate,
            mrp=mrp,
            category_code=category_code,
            selling_price=selling_price,
            status="ACTIVE",
        )
        self._session.add(product)
        await self._session.flush()
        return product

    async def list_products(self, *, tenant_id: str) -> list[CatalogProduct]:
        statement = (
            select(CatalogProduct)
            .where(CatalogProduct.tenant_id == tenant_id)
            .order_by(CatalogProduct.created_at.asc(), CatalogProduct.id.asc())
        )
        return list((await self._session.scalars(statement)).all())

    async def get_product(self, *, tenant_id: str, product_id: str) -> CatalogProduct | None:
        statement = select(CatalogProduct).where(
            CatalogProduct.tenant_id == tenant_id,
            CatalogProduct.id == product_id,
        )
        return await self._session.scalar(statement)

    async def upsert_branch_catalog_item(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        product_id: str,
        selling_price_override: float | None,
        availability_status: str,
        reorder_point: float | None,
        target_stock: float | None,
    ) -> BranchCatalogItem:
        statement = select(BranchCatalogItem).where(
            BranchCatalogItem.tenant_id == tenant_id,
            BranchCatalogItem.branch_id == branch_id,
            BranchCatalogItem.product_id == product_id,
        )
        item = await self._session.scalar(statement)
        if item is None:
            item = BranchCatalogItem(
                id=new_id(),
                tenant_id=tenant_id,
                branch_id=branch_id,
                product_id=product_id,
                selling_price_override=selling_price_override,
                availability_status=availability_status,
                reorder_point=reorder_point,
                target_stock=target_stock,
            )
            self._session.add(item)
        else:
            item.selling_price_override = selling_price_override
            item.availability_status = availability_status
            item.reorder_point = reorder_point
            item.target_stock = target_stock
        await self._session.flush()
        return item

    async def list_branch_catalog_items(self, *, tenant_id: str, branch_id: str) -> list[BranchCatalogItem]:
        statement = (
            select(BranchCatalogItem)
            .where(
                BranchCatalogItem.tenant_id == tenant_id,
                BranchCatalogItem.branch_id == branch_id,
            )
            .order_by(BranchCatalogItem.created_at.asc(), BranchCatalogItem.id.asc())
        )
        return list((await self._session.scalars(statement)).all())
