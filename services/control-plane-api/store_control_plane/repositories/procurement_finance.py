from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import PurchaseInvoice, PurchaseInvoiceLine, SupplierPayment, SupplierReturn, SupplierReturnLine
from ..utils import new_id


@dataclass(slots=True)
class PersistedPurchaseInvoiceBundle:
    purchase_invoice: PurchaseInvoice
    lines: list[PurchaseInvoiceLine]


@dataclass(slots=True)
class PersistedSupplierReturnBundle:
    supplier_return: SupplierReturn
    lines: list[SupplierReturnLine]


class ProcurementFinanceRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def next_branch_purchase_invoice_sequence(self, *, tenant_id: str, branch_id: str) -> int:
        statement = select(func.count(PurchaseInvoice.id)).where(
            PurchaseInvoice.tenant_id == tenant_id,
            PurchaseInvoice.branch_id == branch_id,
        )
        count = await self._session.scalar(statement)
        return int(count or 0) + 1

    async def next_branch_supplier_credit_note_sequence(self, *, tenant_id: str, branch_id: str) -> int:
        statement = select(func.count(SupplierReturn.id)).where(
            SupplierReturn.tenant_id == tenant_id,
            SupplierReturn.branch_id == branch_id,
        )
        count = await self._session.scalar(statement)
        return int(count or 0) + 1

    async def next_branch_supplier_payment_sequence(self, *, tenant_id: str, branch_id: str) -> int:
        statement = select(func.count(SupplierPayment.id)).where(
            SupplierPayment.tenant_id == tenant_id,
            SupplierPayment.branch_id == branch_id,
        )
        count = await self._session.scalar(statement)
        return int(count or 0) + 1

    async def get_purchase_invoice_for_goods_receipt(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        goods_receipt_id: str,
    ) -> PurchaseInvoice | None:
        statement = select(PurchaseInvoice).where(
            PurchaseInvoice.tenant_id == tenant_id,
            PurchaseInvoice.branch_id == branch_id,
            PurchaseInvoice.goods_receipt_id == goods_receipt_id,
        )
        return await self._session.scalar(statement)

    async def get_purchase_invoice(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        purchase_invoice_id: str,
    ) -> PurchaseInvoice | None:
        statement = select(PurchaseInvoice).where(
            PurchaseInvoice.tenant_id == tenant_id,
            PurchaseInvoice.branch_id == branch_id,
            PurchaseInvoice.id == purchase_invoice_id,
        )
        return await self._session.scalar(statement)

    async def create_purchase_invoice(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        supplier_id: str,
        goods_receipt_id: str,
        invoice_number: str,
        invoice_date,
        due_date,
        payment_terms_days: int,
        subtotal: float,
        cgst_total: float,
        sgst_total: float,
        igst_total: float,
        grand_total: float,
        lines: list[dict[str, float | str]],
    ) -> PersistedPurchaseInvoiceBundle:
        purchase_invoice = PurchaseInvoice(
            id=new_id(),
            tenant_id=tenant_id,
            branch_id=branch_id,
            supplier_id=supplier_id,
            goods_receipt_id=goods_receipt_id,
            invoice_number=invoice_number,
            invoice_date=invoice_date,
            due_date=due_date,
            payment_terms_days=payment_terms_days,
            subtotal=subtotal,
            cgst_total=cgst_total,
            sgst_total=sgst_total,
            igst_total=igst_total,
            grand_total=grand_total,
        )
        self._session.add(purchase_invoice)
        await self._session.flush()

        created_lines: list[PurchaseInvoiceLine] = []
        for line in lines:
            record = PurchaseInvoiceLine(
                id=new_id(),
                purchase_invoice_id=purchase_invoice.id,
                product_id=str(line["product_id"]),
                quantity=float(line["quantity"]),
                unit_cost=float(line["unit_cost"]),
                gst_rate=float(line["gst_rate"]),
                line_subtotal=float(line["line_subtotal"]),
                tax_total=float(line["tax_total"]),
                line_total=float(line["line_total"]),
            )
            self._session.add(record)
            created_lines.append(record)
        await self._session.flush()
        return PersistedPurchaseInvoiceBundle(purchase_invoice=purchase_invoice, lines=created_lines)

    async def list_branch_purchase_invoices(self, *, tenant_id: str, branch_id: str) -> list[PurchaseInvoice]:
        statement = (
            select(PurchaseInvoice)
            .where(
                PurchaseInvoice.tenant_id == tenant_id,
                PurchaseInvoice.branch_id == branch_id,
            )
            .order_by(PurchaseInvoice.invoice_date.asc(), PurchaseInvoice.invoice_number.asc())
        )
        return list((await self._session.scalars(statement)).all())

    async def list_purchase_invoice_lines_for_invoices(
        self,
        *,
        purchase_invoice_ids: list[str],
    ) -> dict[str, list[PurchaseInvoiceLine]]:
        if not purchase_invoice_ids:
            return {}
        statement = (
            select(PurchaseInvoiceLine)
            .where(PurchaseInvoiceLine.purchase_invoice_id.in_(purchase_invoice_ids))
            .order_by(PurchaseInvoiceLine.created_at.asc(), PurchaseInvoiceLine.id.asc())
        )
        grouped: dict[str, list[PurchaseInvoiceLine]] = defaultdict(list)
        for record in (await self._session.scalars(statement)).all():
            grouped[record.purchase_invoice_id].append(record)
        return dict(grouped)

    async def create_supplier_return(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        supplier_id: str,
        purchase_invoice_id: str,
        supplier_credit_note_number: str,
        issued_on,
        subtotal: float,
        cgst_total: float,
        sgst_total: float,
        igst_total: float,
        grand_total: float,
        lines: list[dict[str, float | str]],
    ) -> PersistedSupplierReturnBundle:
        supplier_return = SupplierReturn(
            id=new_id(),
            tenant_id=tenant_id,
            branch_id=branch_id,
            supplier_id=supplier_id,
            purchase_invoice_id=purchase_invoice_id,
            supplier_credit_note_number=supplier_credit_note_number,
            issued_on=issued_on,
            subtotal=subtotal,
            cgst_total=cgst_total,
            sgst_total=sgst_total,
            igst_total=igst_total,
            grand_total=grand_total,
        )
        self._session.add(supplier_return)
        await self._session.flush()

        created_lines: list[SupplierReturnLine] = []
        for line in lines:
            record = SupplierReturnLine(
                id=new_id(),
                supplier_return_id=supplier_return.id,
                product_id=str(line["product_id"]),
                quantity=float(line["quantity"]),
                unit_cost=float(line["unit_cost"]),
                gst_rate=float(line["gst_rate"]),
                line_subtotal=float(line["line_subtotal"]),
                tax_total=float(line["tax_total"]),
                line_total=float(line["line_total"]),
            )
            self._session.add(record)
            created_lines.append(record)
        await self._session.flush()
        return PersistedSupplierReturnBundle(supplier_return=supplier_return, lines=created_lines)

    async def list_branch_supplier_returns(self, *, tenant_id: str, branch_id: str) -> list[SupplierReturn]:
        statement = (
            select(SupplierReturn)
            .where(
                SupplierReturn.tenant_id == tenant_id,
                SupplierReturn.branch_id == branch_id,
            )
            .order_by(SupplierReturn.issued_on.asc(), SupplierReturn.supplier_credit_note_number.asc())
        )
        return list((await self._session.scalars(statement)).all())

    async def list_supplier_returns_for_purchase_invoice(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        purchase_invoice_id: str,
    ) -> list[SupplierReturn]:
        statement = (
            select(SupplierReturn)
            .where(
                SupplierReturn.tenant_id == tenant_id,
                SupplierReturn.branch_id == branch_id,
                SupplierReturn.purchase_invoice_id == purchase_invoice_id,
            )
            .order_by(SupplierReturn.issued_on.asc(), SupplierReturn.supplier_credit_note_number.asc())
        )
        return list((await self._session.scalars(statement)).all())

    async def list_supplier_return_lines_for_returns(
        self,
        *,
        supplier_return_ids: list[str],
    ) -> dict[str, list[SupplierReturnLine]]:
        if not supplier_return_ids:
            return {}
        statement = (
            select(SupplierReturnLine)
            .where(SupplierReturnLine.supplier_return_id.in_(supplier_return_ids))
            .order_by(SupplierReturnLine.created_at.asc(), SupplierReturnLine.id.asc())
        )
        grouped: dict[str, list[SupplierReturnLine]] = defaultdict(list)
        for record in (await self._session.scalars(statement)).all():
            grouped[record.supplier_return_id].append(record)
        return dict(grouped)

    async def create_supplier_payment(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        supplier_id: str,
        purchase_invoice_id: str,
        payment_number: str,
        paid_on,
        payment_method: str,
        amount: float,
        reference: str | None,
    ) -> SupplierPayment:
        payment = SupplierPayment(
            id=new_id(),
            tenant_id=tenant_id,
            branch_id=branch_id,
            supplier_id=supplier_id,
            purchase_invoice_id=purchase_invoice_id,
            payment_number=payment_number,
            paid_on=paid_on,
            payment_method=payment_method,
            amount=amount,
            reference=reference,
        )
        self._session.add(payment)
        await self._session.flush()
        return payment

    async def list_branch_supplier_payments(self, *, tenant_id: str, branch_id: str) -> list[SupplierPayment]:
        statement = (
            select(SupplierPayment)
            .where(
                SupplierPayment.tenant_id == tenant_id,
                SupplierPayment.branch_id == branch_id,
            )
            .order_by(SupplierPayment.paid_on.asc(), SupplierPayment.payment_number.asc())
        )
        return list((await self._session.scalars(statement)).all())

    async def list_supplier_payments_for_purchase_invoice(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        purchase_invoice_id: str,
    ) -> list[SupplierPayment]:
        statement = (
            select(SupplierPayment)
            .where(
                SupplierPayment.tenant_id == tenant_id,
                SupplierPayment.branch_id == branch_id,
                SupplierPayment.purchase_invoice_id == purchase_invoice_id,
            )
            .order_by(SupplierPayment.paid_on.asc(), SupplierPayment.payment_number.asc())
        )
        return list((await self._session.scalars(statement)).all())
