from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories import AuditRepository, CatalogRepository, PurchasingRepository, TenantRepository
from ..utils import utc_now
from .purchase_policy import build_purchase_approval_report, build_purchase_order_totals, decide_purchase_order, normalize_gstin, purchase_order_number, submit_purchase_order_approval


class PurchasingService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._tenant_repo = TenantRepository(session)
        self._catalog_repo = CatalogRepository(session)
        self._purchasing_repo = PurchasingRepository(session)
        self._audit_repo = AuditRepository(session)

    async def create_supplier(
        self,
        *,
        tenant_id: str,
        actor_user_id: str,
        name: str,
        gstin: str | None,
        payment_terms_days: int,
    ):
        tenant = await self._tenant_repo.get_tenant(tenant_id)
        if tenant is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
        supplier = await self._purchasing_repo.create_supplier(
            tenant_id=tenant_id,
            name=name,
            gstin=normalize_gstin(gstin),
            payment_terms_days=payment_terms_days,
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=None,
            actor_user_id=actor_user_id,
            action="supplier.created",
            entity_type="supplier",
            entity_id=supplier.id,
            payload={"name": supplier.name, "gstin": supplier.gstin},
        )
        await self._session.commit()
        return supplier

    async def list_suppliers(self, *, tenant_id: str) -> list[dict[str, object]]:
        tenant = await self._tenant_repo.get_tenant(tenant_id)
        if tenant is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
        suppliers = await self._purchasing_repo.list_suppliers(tenant_id=tenant_id)
        return [
            {
                "supplier_id": supplier.id,
                "tenant_id": supplier.tenant_id,
                "name": supplier.name,
                "gstin": supplier.gstin,
                "payment_terms_days": supplier.payment_terms_days,
                "status": supplier.status,
            }
            for supplier in suppliers
        ]

    async def create_purchase_order(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        actor_user_id: str,
        supplier_id: str,
        lines: list[dict[str, float | str]],
    ) -> dict[str, object]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
        supplier = await self._purchasing_repo.get_supplier(tenant_id=tenant_id, supplier_id=supplier_id)
        if supplier is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")

        products_by_id: dict[str, object] = {}
        for line in lines:
            product_id = str(line["product_id"])
            product = await self._catalog_repo.get_product(tenant_id=tenant_id, product_id=product_id)
            if product is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Catalog product not found")
            products_by_id[product_id] = product

        totals = build_purchase_order_totals(line_inputs=lines, products_by_id=products_by_id)
        sequence_number = await self._purchasing_repo.next_branch_purchase_order_sequence(tenant_id=tenant_id, branch_id=branch_id)
        purchase_order = await self._purchasing_repo.create_purchase_order(
            tenant_id=tenant_id,
            branch_id=branch_id,
            supplier_id=supplier_id,
            purchase_order_number=purchase_order_number(branch_code=branch.code, sequence_number=sequence_number),
            subtotal=totals.subtotal,
            tax_total=totals.tax_total,
            grand_total=totals.grand_total,
            lines=[
                {
                    "product_id": line.product_id,
                    "quantity": line.quantity,
                    "unit_cost": line.unit_cost,
                    "gst_rate": line.gst_rate,
                    "line_total": line.line_total,
                    "tax_total": line.tax_total,
                }
                for line in totals.lines
            ],
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="purchase_order.created",
            entity_type="purchase_order",
            entity_id=purchase_order.id,
            payload={"purchase_order_number": purchase_order.purchase_order_number, "supplier_id": supplier_id},
        )
        await self._session.commit()
        return {
            "id": purchase_order.id,
            "tenant_id": purchase_order.tenant_id,
            "branch_id": purchase_order.branch_id,
            "supplier_id": purchase_order.supplier_id,
            "purchase_order_number": purchase_order.purchase_order_number,
            "approval_status": purchase_order.approval_status,
            "subtotal": purchase_order.subtotal,
            "tax_total": purchase_order.tax_total,
            "grand_total": purchase_order.grand_total,
            "lines": [
                {
                    "product_id": line.product_id,
                    "product_name": line.product_name,
                    "sku_code": line.sku_code,
                    "quantity": line.quantity,
                    "unit_cost": line.unit_cost,
                    "line_total": line.line_total,
                }
                for line in totals.lines
            ],
        }

    async def list_purchase_orders(self, *, tenant_id: str, branch_id: str) -> list[dict[str, object]]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
        purchase_orders = await self._purchasing_repo.list_branch_purchase_orders(tenant_id=tenant_id, branch_id=branch_id)
        lines_by_order_id = await self._purchasing_repo.list_purchase_order_lines_for_orders(
            purchase_order_ids=[purchase_order.id for purchase_order in purchase_orders]
        )
        suppliers = {
            supplier["supplier_id"]: supplier
            for supplier in await self.list_suppliers(tenant_id=tenant_id)
        }
        return [
            {
                "purchase_order_id": purchase_order.id,
                "purchase_order_number": purchase_order.purchase_order_number,
                "supplier_id": purchase_order.supplier_id,
                "supplier_name": suppliers.get(purchase_order.supplier_id, {}).get("name", purchase_order.supplier_id),
                "approval_status": purchase_order.approval_status,
                "line_count": len(lines_by_order_id.get(purchase_order.id, [])),
                "ordered_quantity": round(
                    sum(line.quantity for line in lines_by_order_id.get(purchase_order.id, [])),
                    2,
                ),
                "grand_total": purchase_order.grand_total,
                "approval_requested_note": purchase_order.approval_requested_note,
                "approval_decision_note": purchase_order.approval_decision_note,
            }
            for purchase_order in purchase_orders
        ]

    async def get_purchase_order(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        purchase_order_id: str,
    ) -> dict[str, object]:
        purchase_order = await self._purchasing_repo.get_purchase_order(
            tenant_id=tenant_id,
            branch_id=branch_id,
            purchase_order_id=purchase_order_id,
        )
        if purchase_order is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase order not found")
        return await self._purchase_order_response(tenant_id=tenant_id, purchase_order=purchase_order)

    async def submit_purchase_order(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        purchase_order_id: str,
        actor_user_id: str,
        note: str | None,
    ) -> dict[str, object]:
        purchase_order = await self._purchasing_repo.get_purchase_order(
            tenant_id=tenant_id,
            branch_id=branch_id,
            purchase_order_id=purchase_order_id,
        )
        if purchase_order is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase order not found")
        try:
            submit_purchase_order_approval(
                purchase_order=purchase_order,
                note=note,
                requested_at=utc_now(),
            )
        except ValueError as error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="purchase_order.submitted_for_approval",
            entity_type="purchase_order",
            entity_id=purchase_order.id,
            payload={"purchase_order_number": purchase_order.purchase_order_number},
        )
        await self._session.commit()
        return await self._purchase_order_response(tenant_id=tenant_id, purchase_order=purchase_order)

    async def approve_purchase_order(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        purchase_order_id: str,
        actor_user_id: str,
        note: str | None,
    ) -> dict[str, object]:
        purchase_order = await self._purchasing_repo.get_purchase_order(
            tenant_id=tenant_id,
            branch_id=branch_id,
            purchase_order_id=purchase_order_id,
        )
        if purchase_order is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase order not found")
        try:
            decide_purchase_order(
                purchase_order=purchase_order,
                decision="APPROVED",
                note=note,
                decided_at=utc_now(),
            )
        except ValueError as error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="purchase_order.approved",
            entity_type="purchase_order",
            entity_id=purchase_order.id,
            payload={"purchase_order_number": purchase_order.purchase_order_number},
        )
        await self._session.commit()
        return await self._purchase_order_response(tenant_id=tenant_id, purchase_order=purchase_order)

    async def purchase_approval_report(self, *, tenant_id: str, branch_id: str) -> dict[str, object]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
        purchase_orders = await self.list_purchase_orders(tenant_id=tenant_id, branch_id=branch_id)
        suppliers = {
            supplier["supplier_id"]: supplier
            for supplier in await self.list_suppliers(tenant_id=tenant_id)
        }
        return build_purchase_approval_report(
            branch_id=branch_id,
            purchase_orders=purchase_orders,
            suppliers_by_id=suppliers,
        )

    async def _purchase_order_response(self, *, tenant_id: str, purchase_order) -> dict[str, object]:
        lines_by_order_id = await self._purchasing_repo.list_purchase_order_lines_for_orders(
            purchase_order_ids=[purchase_order.id]
        )
        products = {
            product.id: product
            for product in await self._catalog_repo.list_products(tenant_id=tenant_id)
        }
        return {
            "id": purchase_order.id,
            "tenant_id": purchase_order.tenant_id,
            "branch_id": purchase_order.branch_id,
            "supplier_id": purchase_order.supplier_id,
            "purchase_order_number": purchase_order.purchase_order_number,
            "approval_status": purchase_order.approval_status,
            "subtotal": purchase_order.subtotal,
            "tax_total": purchase_order.tax_total,
            "grand_total": purchase_order.grand_total,
            "lines": [
                {
                    "product_id": line.product_id,
                    "product_name": products.get(line.product_id).name if products.get(line.product_id) else line.product_id,
                    "sku_code": products.get(line.product_id).sku_code if products.get(line.product_id) else line.product_id,
                    "quantity": line.quantity,
                    "unit_cost": line.unit_cost,
                    "line_total": line.line_total,
                }
                for line in lines_by_order_id.get(purchase_order.id, [])
            ],
        }
