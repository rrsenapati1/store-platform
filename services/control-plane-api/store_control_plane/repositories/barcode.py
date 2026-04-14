from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import BranchCatalogItem, CatalogProduct


class BarcodeRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_product(self, *, tenant_id: str, product_id: str) -> CatalogProduct | None:
        statement = select(CatalogProduct).where(
            CatalogProduct.tenant_id == tenant_id,
            CatalogProduct.id == product_id,
        )
        return await self._session.scalar(statement)

    async def get_product_by_barcode(self, *, tenant_id: str, barcode: str) -> CatalogProduct | None:
        statement = select(CatalogProduct).where(
            CatalogProduct.tenant_id == tenant_id,
            CatalogProduct.barcode == barcode,
        )
        return await self._session.scalar(statement)

    async def set_product_barcode(self, *, product: CatalogProduct, barcode: str) -> CatalogProduct:
        product.barcode = barcode
        await self._session.flush()
        return product

    async def get_branch_catalog_item(self, *, tenant_id: str, branch_id: str, product_id: str) -> BranchCatalogItem | None:
        statement = select(BranchCatalogItem).where(
            BranchCatalogItem.tenant_id == tenant_id,
            BranchCatalogItem.branch_id == branch_id,
            BranchCatalogItem.product_id == product_id,
        )
        return await self._session.scalar(statement)

    async def find_branch_product_by_barcode(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        barcode: str,
    ) -> tuple[CatalogProduct, BranchCatalogItem] | None:
        statement = (
            select(CatalogProduct, BranchCatalogItem)
            .join(BranchCatalogItem, BranchCatalogItem.product_id == CatalogProduct.id)
            .where(
                CatalogProduct.tenant_id == tenant_id,
                CatalogProduct.barcode == barcode,
                BranchCatalogItem.tenant_id == tenant_id,
                BranchCatalogItem.branch_id == branch_id,
            )
        )
        row = (await self._session.execute(statement)).first()
        if row is None:
            return None
        return row[0], row[1]
