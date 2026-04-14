from __future__ import annotations

from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories import AuditRepository, CatalogRepository, InventoryRepository, ProcurementFinanceRepository, PurchasingRepository, SupplierReportingRepository, TenantRepository
from ..utils import utc_now
from .procurement_finance_policy import (
    build_purchase_invoice_draft,
    build_supplier_payables_report,
    build_supplier_return_draft,
    ensure_purchase_invoice_not_already_created,
    ensure_supplier_payment_within_outstanding,
    purchase_invoice_number,
    supplier_credit_note_number,
    supplier_payment_number,
)


class ProcurementFinanceService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._tenant_repo = TenantRepository(session)
        self._catalog_repo = CatalogRepository(session)
        self._inventory_repo = InventoryRepository(session)
        self._purchasing_repo = PurchasingRepository(session)
        self._finance_repo = ProcurementFinanceRepository(session)
        self._supplier_reporting_repo = SupplierReportingRepository(session)
        self._audit_repo = AuditRepository(session)

    async def create_purchase_invoice(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        actor_user_id: str,
        goods_receipt_id: str,
    ) -> dict[str, object]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
        if branch.gstin is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Branch GSTIN is required for supplier billing")

        goods_receipt = await self._inventory_repo.get_goods_receipt(
            tenant_id=tenant_id,
            branch_id=branch_id,
            goods_receipt_id=goods_receipt_id,
        )
        if goods_receipt is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goods receipt not found")

        existing_invoice = await self._finance_repo.get_purchase_invoice_for_goods_receipt(
            tenant_id=tenant_id,
            branch_id=branch_id,
            goods_receipt_id=goods_receipt_id,
        )
        try:
            ensure_purchase_invoice_not_already_created(goods_receipt_id=goods_receipt_id, existing_purchase_invoice=existing_invoice)
        except ValueError as error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

        supplier = await self._purchasing_repo.get_supplier(tenant_id=tenant_id, supplier_id=goods_receipt.supplier_id)
        if supplier is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")

        goods_receipt_lines = (
            await self._inventory_repo.list_goods_receipt_lines_for_receipts(goods_receipt_ids=[goods_receipt.id])
        ).get(goods_receipt.id, [])
        products = {
            product.id: product
            for product in await self._catalog_repo.list_products(tenant_id=tenant_id)
        }

        try:
            draft = build_purchase_invoice_draft(
                goods_receipt_lines=[
                    {
                        "product_id": line.product_id,
                        "quantity": line.quantity,
                        "unit_cost": line.unit_cost,
                    }
                    for line in goods_receipt_lines
                ],
                products_by_id=products,
                supplier_gstin=supplier.gstin,
                branch_gstin=branch.gstin,
            )
        except ValueError as error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

        invoice_date = utc_now().date()
        sequence_number = await self._finance_repo.next_branch_purchase_invoice_sequence(tenant_id=tenant_id, branch_id=branch_id)
        persisted = await self._finance_repo.create_purchase_invoice(
            tenant_id=tenant_id,
            branch_id=branch_id,
            supplier_id=supplier.id,
            goods_receipt_id=goods_receipt.id,
            invoice_number=purchase_invoice_number(branch_code=branch.code, issued_on=invoice_date, sequence_number=sequence_number),
            invoice_date=invoice_date,
            due_date=invoice_date + timedelta(days=supplier.payment_terms_days),
            payment_terms_days=supplier.payment_terms_days,
            subtotal=draft.subtotal,
            cgst_total=draft.cgst_total,
            sgst_total=draft.sgst_total,
            igst_total=draft.igst_total,
            grand_total=draft.grand_total,
            lines=[
                {
                    "product_id": line.product_id,
                    "quantity": line.quantity,
                    "unit_cost": line.unit_cost,
                    "gst_rate": line.gst_rate,
                    "line_subtotal": line.line_subtotal,
                    "tax_total": line.tax_total,
                    "line_total": line.line_total,
                }
                for line in draft.lines
            ],
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="purchase_invoice.created",
            entity_type="purchase_invoice",
            entity_id=persisted.purchase_invoice.id,
            payload={
                "goods_receipt_id": goods_receipt.id,
                "invoice_number": persisted.purchase_invoice.invoice_number,
                "grand_total": persisted.purchase_invoice.grand_total,
            },
        )
        await self._supplier_reporting_repo.mark_branch_snapshots_dirty(tenant_id=tenant_id, branch_id=branch_id)
        await self._session.commit()
        return self._serialize_purchase_invoice(
            purchase_invoice=persisted.purchase_invoice,
            lines=persisted.lines,
            products_by_id=products,
        )

    async def list_purchase_invoices(self, *, tenant_id: str, branch_id: str) -> list[dict[str, object]]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
        purchase_invoices = await self._finance_repo.list_branch_purchase_invoices(tenant_id=tenant_id, branch_id=branch_id)
        goods_receipts = {
            receipt.id: receipt
            for receipt in await self._inventory_repo.list_branch_goods_receipts(tenant_id=tenant_id, branch_id=branch_id)
        }
        suppliers = {
            supplier["supplier_id"]: supplier
            for supplier in await self._list_suppliers(tenant_id=tenant_id)
        }
        return [
            {
                "purchase_invoice_id": purchase_invoice.id,
                "purchase_invoice_number": purchase_invoice.invoice_number,
                "supplier_id": purchase_invoice.supplier_id,
                "supplier_name": suppliers.get(purchase_invoice.supplier_id, {}).get("name", purchase_invoice.supplier_id),
                "goods_receipt_id": purchase_invoice.goods_receipt_id,
                "goods_receipt_number": goods_receipts[purchase_invoice.goods_receipt_id].goods_receipt_number
                if purchase_invoice.goods_receipt_id in goods_receipts
                else purchase_invoice.goods_receipt_id,
                "invoice_date": purchase_invoice.invoice_date,
                "due_date": purchase_invoice.due_date,
                "grand_total": purchase_invoice.grand_total,
            }
            for purchase_invoice in purchase_invoices
        ]

    async def create_supplier_return(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        purchase_invoice_id: str,
        actor_user_id: str,
        lines: list[dict[str, float | str]],
    ) -> dict[str, object]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
        if branch.gstin is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Branch GSTIN is required for supplier billing")

        purchase_invoice = await self._finance_repo.get_purchase_invoice(
            tenant_id=tenant_id,
            branch_id=branch_id,
            purchase_invoice_id=purchase_invoice_id,
        )
        if purchase_invoice is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase invoice not found")

        supplier = await self._purchasing_repo.get_supplier(tenant_id=tenant_id, supplier_id=purchase_invoice.supplier_id)
        if supplier is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")

        purchase_invoice_lines = (
            await self._finance_repo.list_purchase_invoice_lines_for_invoices(purchase_invoice_ids=[purchase_invoice.id])
        ).get(purchase_invoice.id, [])
        products = {
            product.id: product
            for product in await self._catalog_repo.list_products(tenant_id=tenant_id)
        }
        invoice_lines_by_product_id = {
            line.product_id: {
                "product_id": line.product_id,
                "product_name": products[line.product_id].name,
                "sku_code": products[line.product_id].sku_code,
                "quantity": line.quantity,
                "unit_cost": line.unit_cost,
                "gst_rate": line.gst_rate,
            }
            for line in purchase_invoice_lines
            if line.product_id in products
        }
        existing_returns = await self._finance_repo.list_supplier_returns_for_purchase_invoice(
            tenant_id=tenant_id,
            branch_id=branch_id,
            purchase_invoice_id=purchase_invoice_id,
        )
        return_lines_by_return_id = await self._finance_repo.list_supplier_return_lines_for_returns(
            supplier_return_ids=[record.id for record in existing_returns]
        )
        prior_returned_quantities_by_product_id: dict[str, float] = {}
        for persisted_lines in return_lines_by_return_id.values():
            for return_line in persisted_lines:
                prior_returned_quantities_by_product_id[return_line.product_id] = round(
                    prior_returned_quantities_by_product_id.get(return_line.product_id, 0.0) + return_line.quantity,
                    2,
                )

        try:
            draft = build_supplier_return_draft(
                invoice_lines_by_product_id=invoice_lines_by_product_id,
                prior_returned_quantities_by_product_id=prior_returned_quantities_by_product_id,
                requested_lines=lines,
                supplier_gstin=supplier.gstin,
                branch_gstin=branch.gstin,
            )
        except ValueError as error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

        issued_on = utc_now().date()
        sequence_number = await self._finance_repo.next_branch_supplier_credit_note_sequence(tenant_id=tenant_id, branch_id=branch_id)
        persisted = await self._finance_repo.create_supplier_return(
            tenant_id=tenant_id,
            branch_id=branch_id,
            supplier_id=supplier.id,
            purchase_invoice_id=purchase_invoice.id,
            supplier_credit_note_number=supplier_credit_note_number(
                branch_code=branch.code,
                issued_on=issued_on,
                sequence_number=sequence_number,
            ),
            issued_on=issued_on,
            subtotal=draft.subtotal,
            cgst_total=draft.cgst_total,
            sgst_total=draft.sgst_total,
            igst_total=draft.igst_total,
            grand_total=draft.grand_total,
            lines=[
                {
                    "product_id": line.product_id,
                    "quantity": line.quantity,
                    "unit_cost": line.unit_cost,
                    "gst_rate": line.gst_rate,
                    "line_subtotal": line.line_subtotal,
                    "tax_total": line.tax_total,
                    "line_total": line.line_total,
                }
                for line in draft.lines
            ],
        )
        await self._inventory_repo.create_inventory_ledger_entries(
            entries=[
                {
                    "tenant_id": tenant_id,
                    "branch_id": branch_id,
                    "product_id": line.product_id,
                    "entry_type": "SUPPLIER_RETURN",
                    "quantity": -abs(line.quantity),
                    "reference_type": "supplier_return",
                    "reference_id": persisted.supplier_return.id,
                }
                for line in draft.lines
            ]
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="supplier_return.created",
            entity_type="supplier_return",
            entity_id=persisted.supplier_return.id,
            payload={
                "purchase_invoice_id": purchase_invoice.id,
                "supplier_credit_note_number": persisted.supplier_return.supplier_credit_note_number,
                "grand_total": persisted.supplier_return.grand_total,
            },
        )
        await self._supplier_reporting_repo.mark_branch_snapshots_dirty(tenant_id=tenant_id, branch_id=branch_id)
        await self._session.commit()
        return self._serialize_supplier_return(
            supplier_return=persisted.supplier_return,
            lines=persisted.lines,
            products_by_id=products,
        )

    async def create_supplier_payment(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        purchase_invoice_id: str,
        actor_user_id: str,
        amount: float,
        payment_method: str,
        reference: str | None,
    ) -> dict[str, object]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")

        purchase_invoice = await self._finance_repo.get_purchase_invoice(
            tenant_id=tenant_id,
            branch_id=branch_id,
            purchase_invoice_id=purchase_invoice_id,
        )
        if purchase_invoice is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase invoice not found")

        supplier_returns = await self._finance_repo.list_supplier_returns_for_purchase_invoice(
            tenant_id=tenant_id,
            branch_id=branch_id,
            purchase_invoice_id=purchase_invoice_id,
        )
        supplier_payments = await self._finance_repo.list_supplier_payments_for_purchase_invoice(
            tenant_id=tenant_id,
            branch_id=branch_id,
            purchase_invoice_id=purchase_invoice_id,
        )
        try:
            ensure_supplier_payment_within_outstanding(
                invoice_total=purchase_invoice.grand_total,
                credit_note_total=sum(record.grand_total for record in supplier_returns),
                paid_total=sum(record.amount for record in supplier_payments),
                payment_amount=amount,
            )
        except ValueError as error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

        paid_on = utc_now().date()
        sequence_number = await self._finance_repo.next_branch_supplier_payment_sequence(tenant_id=tenant_id, branch_id=branch_id)
        payment = await self._finance_repo.create_supplier_payment(
            tenant_id=tenant_id,
            branch_id=branch_id,
            supplier_id=purchase_invoice.supplier_id,
            purchase_invoice_id=purchase_invoice.id,
            payment_number=supplier_payment_number(branch_code=branch.code, paid_on=paid_on, sequence_number=sequence_number),
            paid_on=paid_on,
            payment_method=payment_method,
            amount=amount,
            reference=reference,
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="supplier_payment.recorded",
            entity_type="supplier_payment",
            entity_id=payment.id,
            payload={
                "purchase_invoice_id": purchase_invoice.id,
                "payment_number": payment.payment_number,
                "amount": payment.amount,
            },
        )
        await self._supplier_reporting_repo.mark_branch_snapshots_dirty(tenant_id=tenant_id, branch_id=branch_id)
        await self._session.commit()
        return {
            "id": payment.id,
            "tenant_id": payment.tenant_id,
            "branch_id": payment.branch_id,
            "supplier_id": payment.supplier_id,
            "purchase_invoice_id": payment.purchase_invoice_id,
            "payment_number": payment.payment_number,
            "paid_on": payment.paid_on,
            "payment_method": payment.payment_method,
            "amount": payment.amount,
            "reference": payment.reference,
        }

    async def supplier_payables_report(self, *, tenant_id: str, branch_id: str) -> dict[str, object]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
        purchase_invoices = await self._finance_repo.list_branch_purchase_invoices(tenant_id=tenant_id, branch_id=branch_id)
        supplier_returns = await self._finance_repo.list_branch_supplier_returns(tenant_id=tenant_id, branch_id=branch_id)
        supplier_payments = await self._finance_repo.list_branch_supplier_payments(tenant_id=tenant_id, branch_id=branch_id)
        suppliers = {
            supplier["supplier_id"]: supplier
            for supplier in await self._list_suppliers(tenant_id=tenant_id)
        }
        return build_supplier_payables_report(
            branch_id=branch_id,
            purchase_invoices=[
                {
                    "id": record.id,
                    "supplier_id": record.supplier_id,
                    "invoice_number": record.invoice_number,
                    "grand_total": record.grand_total,
                }
                for record in purchase_invoices
            ],
            supplier_returns=[
                {
                    "purchase_invoice_id": record.purchase_invoice_id,
                    "grand_total": record.grand_total,
                }
                for record in supplier_returns
            ],
            supplier_payments=[
                {
                    "purchase_invoice_id": record.purchase_invoice_id,
                    "amount": record.amount,
                }
                for record in supplier_payments
            ],
            suppliers_by_id=suppliers,
        )

    async def _list_suppliers(self, *, tenant_id: str) -> list[dict[str, object]]:
        suppliers = await self._purchasing_repo.list_suppliers(tenant_id=tenant_id)
        return [
            {
                "supplier_id": supplier.id,
                "name": supplier.name,
                "gstin": supplier.gstin,
                "payment_terms_days": supplier.payment_terms_days,
            }
            for supplier in suppliers
        ]

    def _serialize_purchase_invoice(self, *, purchase_invoice, lines, products_by_id) -> dict[str, object]:
        return {
            "id": purchase_invoice.id,
            "tenant_id": purchase_invoice.tenant_id,
            "branch_id": purchase_invoice.branch_id,
            "supplier_id": purchase_invoice.supplier_id,
            "goods_receipt_id": purchase_invoice.goods_receipt_id,
            "invoice_number": purchase_invoice.invoice_number,
            "invoice_date": purchase_invoice.invoice_date,
            "due_date": purchase_invoice.due_date,
            "payment_terms_days": purchase_invoice.payment_terms_days,
            "subtotal": purchase_invoice.subtotal,
            "cgst_total": purchase_invoice.cgst_total,
            "sgst_total": purchase_invoice.sgst_total,
            "igst_total": purchase_invoice.igst_total,
            "grand_total": purchase_invoice.grand_total,
            "lines": [
                {
                    "product_id": line.product_id,
                    "product_name": products_by_id[line.product_id].name,
                    "sku_code": products_by_id[line.product_id].sku_code,
                    "quantity": line.quantity,
                    "unit_cost": line.unit_cost,
                    "gst_rate": line.gst_rate,
                    "line_subtotal": line.line_subtotal,
                    "tax_total": line.tax_total,
                    "line_total": line.line_total,
                }
                for line in lines
            ],
        }

    def _serialize_supplier_return(self, *, supplier_return, lines, products_by_id) -> dict[str, object]:
        return {
            "id": supplier_return.id,
            "tenant_id": supplier_return.tenant_id,
            "branch_id": supplier_return.branch_id,
            "supplier_id": supplier_return.supplier_id,
            "purchase_invoice_id": supplier_return.purchase_invoice_id,
            "supplier_credit_note_number": supplier_return.supplier_credit_note_number,
            "issued_on": supplier_return.issued_on,
            "subtotal": supplier_return.subtotal,
            "cgst_total": supplier_return.cgst_total,
            "sgst_total": supplier_return.sgst_total,
            "igst_total": supplier_return.igst_total,
            "grand_total": supplier_return.grand_total,
            "lines": [
                {
                    "product_id": line.product_id,
                    "product_name": products_by_id[line.product_id].name,
                    "sku_code": products_by_id[line.product_id].sku_code,
                    "quantity": line.quantity,
                    "unit_cost": line.unit_cost,
                    "gst_rate": line.gst_rate,
                    "line_subtotal": line.line_subtotal,
                    "tax_total": line.tax_total,
                    "line_total": line.line_total,
                }
                for line in lines
            ],
        }
