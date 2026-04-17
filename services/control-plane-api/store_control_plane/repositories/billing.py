from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import CheckoutPaymentSession, CreditNote, CreditNoteTaxLine, ExchangeOrder, InvoiceTaxLine, Payment, Sale, SaleLine, SaleReturn, SaleReturnLine, SalesInvoice
from ..utils import new_id


@dataclass(slots=True)
class PersistedSaleBundle:
    sale: Sale
    invoice: SalesInvoice
    lines: list[SaleLine]
    tax_lines: list[InvoiceTaxLine]
    payments: list[Payment]


@dataclass(slots=True)
class SaleBundle:
    sale: Sale
    invoice: SalesInvoice
    payments: list[Payment]
    lines: list[SaleLine]
    tax_lines: list[InvoiceTaxLine]


@dataclass(slots=True)
class PersistedSaleReturnBundle:
    sale_return: SaleReturn
    credit_note: CreditNote
    lines: list[SaleReturnLine]
    tax_lines: list[CreditNoteTaxLine]


@dataclass(slots=True)
class PersistedExchangeBundle:
    exchange_order: ExchangeOrder
    sale_return: PersistedSaleReturnBundle
    replacement_sale: PersistedSaleBundle


class BillingRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def next_branch_sale_sequence(self, *, tenant_id: str, branch_id: str) -> int:
        statement = select(func.count(SalesInvoice.id)).where(
            SalesInvoice.tenant_id == tenant_id,
            SalesInvoice.branch_id == branch_id,
        )
        count = await self._session.scalar(statement)
        return int(count or 0) + 1

    async def next_branch_credit_note_sequence(self, *, tenant_id: str, branch_id: str) -> int:
        statement = select(func.count(CreditNote.id)).where(
            CreditNote.tenant_id == tenant_id,
            CreditNote.branch_id == branch_id,
        )
        count = await self._session.scalar(statement)
        return int(count or 0) + 1

    async def create_sale(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        customer_profile_id: str | None,
        customer_name: str,
        customer_gstin: str | None,
        promotion_campaign_id: str | None,
        promotion_code_id: str | None,
        customer_voucher_id: str | None,
        gift_card_id: str | None,
        customer_voucher_name: str | None,
        gift_card_code: str | None,
        gift_card_amount: float,
        promotion_code: str | None,
        promotion_discount_amount: float,
        customer_voucher_discount_total: float,
        invoice_kind: str,
        irn_status: str,
        issued_on,
        invoice_number: str,
        subtotal: float,
        tax_total: float,
        cgst_total: float,
        sgst_total: float,
        igst_total: float,
        grand_total: float,
        loyalty_points_redeemed: int,
        loyalty_discount_amount: float,
        loyalty_points_earned: int,
        payment_method: str | None,
        payments: list[dict[str, float | str]] | None,
        lines: list[dict[str, float | str]],
        tax_lines: list[dict[str, float | str]],
        automatic_campaign_name: str | None = None,
        automatic_discount_total: float = 0.0,
        promotion_code_discount_total: float = 0.0,
        mrp_total: float = 0.0,
        selling_price_subtotal: float = 0.0,
        total_discount: float = 0.0,
        invoice_total: float = 0.0,
        cashier_session_id: str | None = None,
    ) -> PersistedSaleBundle:
        sale = Sale(
            id=new_id(),
            tenant_id=tenant_id,
            branch_id=branch_id,
            cashier_session_id=cashier_session_id,
            customer_profile_id=customer_profile_id,
            customer_name=customer_name,
            customer_gstin=customer_gstin,
            automatic_campaign_name=automatic_campaign_name,
            automatic_discount_total=automatic_discount_total,
            promotion_campaign_id=promotion_campaign_id,
            promotion_code_id=promotion_code_id,
            customer_voucher_id=customer_voucher_id,
            gift_card_id=gift_card_id,
            customer_voucher_name=customer_voucher_name,
            gift_card_code=gift_card_code,
            gift_card_amount=gift_card_amount,
            promotion_code=promotion_code,
            promotion_discount_amount=promotion_discount_amount,
            promotion_code_discount_total=promotion_code_discount_total,
            customer_voucher_discount_total=customer_voucher_discount_total,
            invoice_kind=invoice_kind,
            irn_status=irn_status,
            loyalty_points_redeemed=loyalty_points_redeemed,
            loyalty_discount_amount=loyalty_discount_amount,
            loyalty_points_earned=loyalty_points_earned,
            mrp_total=mrp_total,
            selling_price_subtotal=selling_price_subtotal,
            total_discount=total_discount,
            invoice_total=invoice_total,
            subtotal=subtotal,
            tax_total=tax_total,
            grand_total=grand_total,
        )
        self._session.add(sale)
        await self._session.flush()

        created_lines: list[SaleLine] = []
        for line in lines:
            record = SaleLine(
                id=new_id(),
                sale_id=sale.id,
                product_id=str(line["product_id"]),
                quantity=float(line["quantity"]),
                mrp=float(line.get("mrp", line.get("unit_price", 0.0))),
                unit_selling_price=float(line.get("unit_selling_price", line["unit_price"])),
                unit_price=float(line["unit_price"]),
                gst_rate=float(line["gst_rate"]),
                automatic_discount_amount=float(line.get("automatic_discount_amount", 0.0)),
                promotion_code_discount_amount=float(line.get("promotion_code_discount_amount", 0.0)),
                customer_voucher_discount_amount=float(line.get("customer_voucher_discount_amount") or 0.0),
                promotion_discount_source=line.get("promotion_discount_source"),
                taxable_amount=float(line.get("taxable_amount", line["line_subtotal"])),
                tax_amount=float(line.get("tax_amount", line["tax_total"])),
                line_subtotal=float(line["line_subtotal"]),
                tax_total=float(line["tax_total"]),
                line_total=float(line["line_total"]),
            )
            self._session.add(record)
            created_lines.append(record)

        invoice = SalesInvoice(
            id=new_id(),
            sale_id=sale.id,
            tenant_id=tenant_id,
            branch_id=branch_id,
            invoice_number=invoice_number,
            issued_on=issued_on,
            subtotal=subtotal,
            cgst_total=cgst_total,
            sgst_total=sgst_total,
            igst_total=igst_total,
            grand_total=grand_total,
        )
        self._session.add(invoice)
        await self._session.flush()

        created_tax_lines: list[InvoiceTaxLine] = []
        for line in tax_lines:
            record = InvoiceTaxLine(
                id=new_id(),
                sales_invoice_id=invoice.id,
                tax_type=str(line["tax_type"]),
                tax_rate=float(line["tax_rate"]),
                taxable_amount=float(line["taxable_amount"]),
                tax_amount=float(line["tax_amount"]),
            )
            self._session.add(record)
            created_tax_lines.append(record)

        created_payments: list[Payment] = []
        payment_rows = payments if payments is not None else [{"payment_method": payment_method or "", "amount": grand_total}]
        for payment_row in payment_rows:
            payment = Payment(
                id=new_id(),
                sale_id=sale.id,
                payment_method=str(payment_row["payment_method"]),
                amount=float(payment_row["amount"]),
            )
            self._session.add(payment)
            created_payments.append(payment)
        await self._session.flush()

        return PersistedSaleBundle(
            sale=sale,
            invoice=invoice,
            lines=created_lines,
            tax_lines=created_tax_lines,
            payments=created_payments,
        )

    async def create_checkout_payment_session(
        self,
        *,
        session_id: str,
        tenant_id: str,
        branch_id: str,
        actor_user_id: str | None,
        customer_profile_id: str | None,
        provider_name: str,
        provider_order_id: str,
        provider_payment_session_id: str | None,
        payment_method: str,
        handoff_surface: str,
        provider_payment_mode: str,
        lifecycle_status: str,
        provider_status: str,
        order_amount: float,
        currency_code: str,
        cart_summary_hash: str,
        cart_snapshot: dict,
        customer_name: str,
        customer_gstin: str | None,
        action_payload: dict,
        action_expires_at,
        qr_payload: dict,
        qr_expires_at,
        provider_response_payload: dict,
        cashier_session_id: str | None = None,
    ) -> CheckoutPaymentSession:
        record = CheckoutPaymentSession(
            id=session_id,
            tenant_id=tenant_id,
            branch_id=branch_id,
            cashier_session_id=cashier_session_id,
            actor_user_id=actor_user_id,
            customer_profile_id=customer_profile_id,
            provider_name=provider_name,
            provider_order_id=provider_order_id,
            provider_payment_session_id=provider_payment_session_id,
            payment_method=payment_method,
            handoff_surface=handoff_surface,
            provider_payment_mode=provider_payment_mode,
            lifecycle_status=lifecycle_status,
            provider_status=provider_status,
            order_amount=order_amount,
            currency_code=currency_code,
            cart_summary_hash=cart_summary_hash,
            cart_snapshot=cart_snapshot,
            customer_name=customer_name,
            customer_gstin=customer_gstin,
            action_payload=action_payload,
            action_expires_at=action_expires_at,
            qr_payload=qr_payload,
            qr_expires_at=qr_expires_at,
            provider_response_payload=provider_response_payload,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def list_checkout_payment_sessions(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        limit: int = 10,
    ) -> list[CheckoutPaymentSession]:
        statement = (
            select(CheckoutPaymentSession)
            .where(
                CheckoutPaymentSession.tenant_id == tenant_id,
                CheckoutPaymentSession.branch_id == branch_id,
            )
            .order_by(CheckoutPaymentSession.created_at.desc(), CheckoutPaymentSession.id.desc())
            .limit(limit)
        )
        return list((await self._session.scalars(statement)).all())

    async def create_sale_return(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        sale_id: str,
        status: str,
        refund_amount: float,
        refund_method: str,
        issued_on,
        credit_note_number: str,
        subtotal: float,
        cgst_total: float,
        sgst_total: float,
        igst_total: float,
        grand_total: float,
        lines: list[dict[str, float | str]],
        tax_lines: list[dict[str, float | str]],
        cashier_session_id: str | None = None,
    ) -> PersistedSaleReturnBundle:
        sale_return = SaleReturn(
            id=new_id(),
            tenant_id=tenant_id,
            branch_id=branch_id,
            cashier_session_id=cashier_session_id,
            sale_id=sale_id,
            status=status,
            refund_amount=refund_amount,
            refund_method=refund_method,
        )
        self._session.add(sale_return)
        await self._session.flush()

        created_lines: list[SaleReturnLine] = []
        for line in lines:
            record = SaleReturnLine(
                id=new_id(),
                sale_return_id=sale_return.id,
                product_id=str(line["product_id"]),
                quantity=float(line["quantity"]),
                unit_price=float(line["unit_price"]),
                gst_rate=float(line["gst_rate"]),
                line_subtotal=float(line["line_subtotal"]),
                tax_total=float(line["tax_total"]),
                line_total=float(line["line_total"]),
            )
            self._session.add(record)
            created_lines.append(record)

        credit_note = CreditNote(
            id=new_id(),
            sale_return_id=sale_return.id,
            tenant_id=tenant_id,
            branch_id=branch_id,
            credit_note_number=credit_note_number,
            issued_on=issued_on,
            subtotal=subtotal,
            cgst_total=cgst_total,
            sgst_total=sgst_total,
            igst_total=igst_total,
            grand_total=grand_total,
        )
        self._session.add(credit_note)
        await self._session.flush()

        created_tax_lines: list[CreditNoteTaxLine] = []
        for line in tax_lines:
            record = CreditNoteTaxLine(
                id=new_id(),
                credit_note_id=credit_note.id,
                tax_type=str(line["tax_type"]),
                tax_rate=float(line["tax_rate"]),
                taxable_amount=float(line["taxable_amount"]),
                tax_amount=float(line["tax_amount"]),
            )
            self._session.add(record)
            created_tax_lines.append(record)

        await self._session.flush()
        return PersistedSaleReturnBundle(
            sale_return=sale_return,
            credit_note=credit_note,
            lines=created_lines,
            tax_lines=created_tax_lines,
        )

    async def list_branch_sales(self, *, tenant_id: str, branch_id: str) -> list[tuple[Sale, SalesInvoice, list[Payment]]]:
        statement = (
            select(Sale, SalesInvoice)
            .join(SalesInvoice, SalesInvoice.sale_id == Sale.id)
            .where(
                Sale.tenant_id == tenant_id,
                Sale.branch_id == branch_id,
            )
            .order_by(SalesInvoice.issued_on.asc(), SalesInvoice.invoice_number.asc())
        )
        result = await self._session.execute(statement)
        records = result.all()
        sales = [sale for sale, _ in records]
        payments_by_sale_id = await self.list_payments_for_sales(sale_ids=[sale.id for sale in sales])
        return [(sale, invoice, payments_by_sale_id.get(sale.id, [])) for sale, invoice in records]

    async def get_sale_bundle(self, *, tenant_id: str, branch_id: str, sale_id: str) -> SaleBundle | None:
        statement = (
            select(Sale, SalesInvoice)
            .join(SalesInvoice, SalesInvoice.sale_id == Sale.id)
            .where(
                Sale.tenant_id == tenant_id,
                Sale.branch_id == branch_id,
                Sale.id == sale_id,
            )
        )
        result = await self._session.execute(statement)
        record = result.first()
        if record is None:
            return None
        sale, invoice = record
        lines = (await self.list_sale_lines_for_sales(sale_ids=[sale.id])).get(sale.id, [])
        tax_lines = (await self.list_tax_lines_for_invoices(invoice_ids=[invoice.id])).get(invoice.id, [])
        payments = (await self.list_payments_for_sales(sale_ids=[sale.id])).get(sale.id, [])
        return SaleBundle(sale=sale, invoice=invoice, payments=payments, lines=lines, tax_lines=tax_lines)

    async def get_checkout_payment_session(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        checkout_payment_session_id: str,
    ) -> CheckoutPaymentSession | None:
        statement = select(CheckoutPaymentSession).where(
            CheckoutPaymentSession.tenant_id == tenant_id,
            CheckoutPaymentSession.branch_id == branch_id,
            CheckoutPaymentSession.id == checkout_payment_session_id,
        )
        return await self._session.scalar(statement)

    async def get_checkout_payment_session_by_provider_order(
        self,
        *,
        provider_name: str,
        provider_order_id: str,
    ) -> CheckoutPaymentSession | None:
        statement = select(CheckoutPaymentSession).where(
            CheckoutPaymentSession.provider_name == provider_name,
            CheckoutPaymentSession.provider_order_id == provider_order_id,
        )
        return await self._session.scalar(statement)

    async def list_sale_lines_for_sales(self, *, sale_ids: list[str]) -> dict[str, list[SaleLine]]:
        if not sale_ids:
            return {}
        statement = (
            select(SaleLine)
            .where(SaleLine.sale_id.in_(sale_ids))
            .order_by(SaleLine.created_at.asc(), SaleLine.id.asc())
        )
        grouped: dict[str, list[SaleLine]] = defaultdict(list)
        for record in (await self._session.scalars(statement)).all():
            grouped[record.sale_id].append(record)
        return dict(grouped)

    async def list_tax_lines_for_invoices(self, *, invoice_ids: list[str]) -> dict[str, list[InvoiceTaxLine]]:
        if not invoice_ids:
            return {}
        statement = (
            select(InvoiceTaxLine)
            .where(InvoiceTaxLine.sales_invoice_id.in_(invoice_ids))
            .order_by(InvoiceTaxLine.created_at.asc(), InvoiceTaxLine.id.asc())
        )
        grouped: dict[str, list[InvoiceTaxLine]] = defaultdict(list)
        for record in (await self._session.scalars(statement)).all():
            grouped[record.sales_invoice_id].append(record)
        return dict(grouped)

    async def list_payments_for_sales(self, *, sale_ids: list[str]) -> dict[str, list[Payment]]:
        if not sale_ids:
            return {}
        statement = (
            select(Payment)
            .where(Payment.sale_id.in_(sale_ids))
            .order_by(Payment.created_at.asc(), Payment.id.asc())
        )
        grouped: dict[str, list[Payment]] = defaultdict(list)
        for record in (await self._session.scalars(statement)).all():
            grouped[record.sale_id].append(record)
        return dict(grouped)

    async def list_sale_returns_for_sale(self, *, tenant_id: str, branch_id: str, sale_id: str) -> list[SaleReturn]:
        statement = (
            select(SaleReturn)
            .where(
                SaleReturn.tenant_id == tenant_id,
                SaleReturn.branch_id == branch_id,
                SaleReturn.sale_id == sale_id,
            )
            .order_by(SaleReturn.created_at.asc(), SaleReturn.id.asc())
        )
        return list((await self._session.scalars(statement)).all())

    async def list_sale_return_lines_for_returns(self, *, sale_return_ids: list[str]) -> dict[str, list[SaleReturnLine]]:
        if not sale_return_ids:
            return {}
        statement = (
            select(SaleReturnLine)
            .where(SaleReturnLine.sale_return_id.in_(sale_return_ids))
            .order_by(SaleReturnLine.created_at.asc(), SaleReturnLine.id.asc())
        )
        grouped: dict[str, list[SaleReturnLine]] = defaultdict(list)
        for record in (await self._session.scalars(statement)).all():
            grouped[record.sale_return_id].append(record)
        return dict(grouped)

    async def list_credit_note_tax_lines_for_credit_notes(self, *, credit_note_ids: list[str]) -> dict[str, list[CreditNoteTaxLine]]:
        if not credit_note_ids:
            return {}
        statement = (
            select(CreditNoteTaxLine)
            .where(CreditNoteTaxLine.credit_note_id.in_(credit_note_ids))
            .order_by(CreditNoteTaxLine.created_at.asc(), CreditNoteTaxLine.id.asc())
        )
        grouped: dict[str, list[CreditNoteTaxLine]] = defaultdict(list)
        for record in (await self._session.scalars(statement)).all():
            grouped[record.credit_note_id].append(record)
        return dict(grouped)

    async def list_branch_sale_returns(
        self,
        *,
        tenant_id: str,
        branch_id: str,
    ) -> list[tuple[SaleReturn, CreditNote, Sale, SalesInvoice]]:
        statement = (
            select(SaleReturn, CreditNote, Sale, SalesInvoice)
            .join(CreditNote, CreditNote.sale_return_id == SaleReturn.id)
            .join(Sale, Sale.id == SaleReturn.sale_id)
            .join(SalesInvoice, SalesInvoice.sale_id == Sale.id)
            .where(
                SaleReturn.tenant_id == tenant_id,
                SaleReturn.branch_id == branch_id,
            )
            .order_by(CreditNote.issued_on.asc(), CreditNote.credit_note_number.asc())
        )
        result = await self._session.execute(statement)
        return [(sale_return, credit_note, sale, invoice) for sale_return, credit_note, sale, invoice in result.all()]

    async def get_sale_return(self, *, tenant_id: str, branch_id: str, sale_return_id: str) -> SaleReturn | None:
        statement = select(SaleReturn).where(
            SaleReturn.tenant_id == tenant_id,
            SaleReturn.branch_id == branch_id,
            SaleReturn.id == sale_return_id,
        )
        return await self._session.scalar(statement)

    async def get_credit_note_for_sale_return(self, *, sale_return_id: str) -> CreditNote | None:
        statement = select(CreditNote).where(CreditNote.sale_return_id == sale_return_id)
        return await self._session.scalar(statement)

    async def create_exchange_order(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        original_sale_id: str,
        replacement_sale_id: str,
        sale_return_id: str,
        status: str,
        balance_direction: str,
        balance_amount: float,
        settlement_method: str,
    ) -> ExchangeOrder:
        exchange_order = ExchangeOrder(
            id=new_id(),
            tenant_id=tenant_id,
            branch_id=branch_id,
            original_sale_id=original_sale_id,
            replacement_sale_id=replacement_sale_id,
            sale_return_id=sale_return_id,
            status=status,
            balance_direction=balance_direction,
            balance_amount=balance_amount,
            settlement_method=settlement_method,
        )
        self._session.add(exchange_order)
        await self._session.flush()
        return exchange_order
