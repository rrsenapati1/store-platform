from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories import AuditRepository, BarcodeRepository, InventoryRepository, TenantRepository
from .checkout_pricing import CheckoutPricingService
from .barcode_policy import allocate_barcode, build_barcode_label_preview, normalize_barcode


class BarcodeService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._tenant_repo = TenantRepository(session)
        self._barcode_repo = BarcodeRepository(session)
        self._inventory_repo = InventoryRepository(session)
        self._audit_repo = AuditRepository(session)
        self._checkout_pricing_service = CheckoutPricingService(session)

    async def allocate_product_barcode(
        self,
        *,
        tenant_id: str,
        product_id: str,
        actor_user_id: str,
        requested_barcode: str | None,
    ) -> dict[str, str]:
        tenant = await self._tenant_repo.get_tenant(tenant_id)
        if tenant is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
        product = await self._barcode_repo.get_product(tenant_id=tenant_id, product_id=product_id)
        if product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Catalog product not found")

        manual_barcode = normalize_barcode(requested_barcode or "")
        existing_barcode = normalize_barcode(product.barcode or "")
        if manual_barcode:
            barcode = manual_barcode
            source = "MANUAL"
        elif existing_barcode:
            barcode = existing_barcode
            source = "EXISTING"
        else:
            barcode = allocate_barcode(tenant_name=tenant.name, sku_value=product.sku_code)
            source = "ALLOCATED"

        duplicate = await self._barcode_repo.get_product_by_barcode(tenant_id=tenant_id, barcode=barcode)
        if duplicate is not None and duplicate.id != product.id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Barcode is already assigned to another catalog product")

        await self._barcode_repo.set_product_barcode(product=product, barcode=barcode)
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=None,
            actor_user_id=actor_user_id,
            action="catalog_product.barcode_allocated",
            entity_type="catalog_product",
            entity_id=product.id,
            payload={"barcode": barcode, "source": source},
        )
        await self._session.commit()
        return {"product_id": product.id, "barcode": barcode, "source": source}

    async def lookup_branch_catalog_scan(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        barcode: str,
    ) -> dict[str, object]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
        normalized_barcode = normalize_barcode(barcode)
        record = await self._barcode_repo.find_branch_product_by_barcode(
            tenant_id=tenant_id,
            branch_id=branch_id,
            barcode=normalized_barcode,
        )
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Catalog barcode not found")
        product, item = record
        stock_on_hand = await self._inventory_repo.stock_on_hand(
            tenant_id=tenant_id,
            branch_id=branch_id,
            product_id=product.id,
        )
        effective_selling_price = item.selling_price_override if item.selling_price_override is not None else product.selling_price
        automatic_discount_hint = await self._checkout_pricing_service.describe_scan_automatic_discount_hint(
            tenant_id=tenant_id,
            product_id=product.id,
            category_code=product.category_code,
            unit_selling_price=effective_selling_price,
        )
        return {
            "product_id": product.id,
            "product_name": product.name,
            "sku_code": product.sku_code,
            "barcode": normalized_barcode,
            "mrp": product.mrp,
            "selling_price": effective_selling_price,
            "stock_on_hand": stock_on_hand,
            "availability_status": item.availability_status,
            "reorder_point": item.reorder_point,
            "target_stock": item.target_stock,
            "automatic_discount_hint": automatic_discount_hint,
        }

    async def preview_branch_barcode_label(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        product_id: str,
        actor_user_id: str,
    ) -> dict[str, str]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
        product = await self._barcode_repo.get_product(tenant_id=tenant_id, product_id=product_id)
        if product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Catalog product not found")
        item = await self._barcode_repo.get_branch_catalog_item(tenant_id=tenant_id, branch_id=branch_id, product_id=product_id)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch catalog item not found")

        barcode = normalize_barcode(product.barcode or "")
        if not barcode:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Catalog product barcode is not allocated")
        effective_selling_price = item.selling_price_override if item.selling_price_override is not None else product.selling_price
        label = build_barcode_label_preview(
            sku_value=product.sku_code,
            product_name=product.name,
            barcode=barcode,
            selling_price=effective_selling_price,
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="catalog_product.barcode_label_previewed",
            entity_type="catalog_product",
            entity_id=product.id,
            payload={"barcode": barcode},
        )
        await self._session.commit()
        return {"product_id": product.id, **label}
