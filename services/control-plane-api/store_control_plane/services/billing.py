from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories import AuditRepository, BillingRepository, CatalogRepository, InventoryRepository, TenantRepository
from ..utils import utc_now
from .billing_policy import build_sale_draft, ensure_sale_stock_available, sale_invoice_number
from .exchange_policy import build_exchange_settlement
from .returns_policy import build_sale_return_draft, credit_note_number, ensure_refund_amount_allowed


class BillingService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._tenant_repo = TenantRepository(session)
        self._catalog_repo = CatalogRepository(session)
        self._inventory_repo = InventoryRepository(session)
        self._billing_repo = BillingRepository(session)
        self._audit_repo = AuditRepository(session)

    async def create_sale(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        actor_user_id: str,
        customer_name: str,
        customer_gstin: str | None,
        payment_method: str,
        lines: list[dict[str, float | str]],
    ) -> dict[str, object]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
        if branch.gstin is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Branch GSTIN is required for billing")

        products = {
            product.id: product
            for product in await self._catalog_repo.list_products(tenant_id=tenant_id)
        }
        branch_catalog_items = await self._catalog_repo.list_branch_catalog_items(tenant_id=tenant_id, branch_id=branch_id)
        branch_catalog_by_product_id: dict[str, dict[str, object]] = {}
        for item in branch_catalog_items:
            product = products.get(item.product_id)
            if product is None:
                continue
            branch_catalog_by_product_id[item.product_id] = {
                "availability_status": item.availability_status,
                "effective_selling_price": item.selling_price_override if item.selling_price_override is not None else product.selling_price,
            }

        try:
            draft = build_sale_draft(
                line_inputs=lines,
                branch_gstin=branch.gstin,
                customer_name=customer_name,
                customer_gstin=customer_gstin,
                products_by_id=products,
                branch_catalog_items_by_product_id=branch_catalog_by_product_id,
            )
        except ValueError as error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

        for line in draft.lines:
            available_quantity = await self._inventory_repo.stock_on_hand(
                tenant_id=tenant_id,
                branch_id=branch_id,
                product_id=line.product_id,
            )
            try:
                ensure_sale_stock_available(requested_quantity=line.quantity, available_quantity=available_quantity)
            except ValueError as error:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

        sequence_number = await self._billing_repo.next_branch_sale_sequence(tenant_id=tenant_id, branch_id=branch_id)
        persisted = await self._billing_repo.create_sale(
            tenant_id=tenant_id,
            branch_id=branch_id,
            customer_name=draft.customer_name,
            customer_gstin=draft.customer_gstin,
            invoice_kind=draft.invoice_kind,
            irn_status=draft.irn_status,
            issued_on=utc_now().date(),
            invoice_number=sale_invoice_number(branch_code=branch.code, sequence_number=sequence_number),
            subtotal=draft.subtotal,
            tax_total=draft.tax_total,
            cgst_total=draft.cgst_total,
            sgst_total=draft.sgst_total,
            igst_total=draft.igst_total,
            grand_total=draft.grand_total,
            payment_method=payment_method,
            payments=None,
            lines=[
                {
                    "product_id": line.product_id,
                    "quantity": line.quantity,
                    "unit_price": line.unit_price,
                    "gst_rate": line.gst_rate,
                    "line_subtotal": line.line_subtotal,
                    "tax_total": line.tax_total,
                    "line_total": line.line_total,
                }
                for line in draft.lines
            ],
            tax_lines=[
                {
                    "tax_type": line.tax_type,
                    "tax_rate": line.tax_rate,
                    "taxable_amount": line.taxable_amount,
                    "tax_amount": line.tax_amount,
                }
                for line in draft.tax_lines
            ],
        )
        await self._inventory_repo.create_inventory_ledger_entries(
            entries=[
                {
                    "tenant_id": tenant_id,
                    "branch_id": branch_id,
                    "product_id": line.product_id,
                    "entry_type": "SALE",
                    "quantity": -abs(line.quantity),
                    "reference_type": "sale",
                    "reference_id": persisted.sale.id,
                }
                for line in draft.lines
            ]
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="sale.created",
            entity_type="sale",
            entity_id=persisted.sale.id,
            payload={"invoice_number": persisted.invoice.invoice_number, "grand_total": persisted.sale.grand_total},
        )
        await self._session.commit()
        return self._serialize_sale_bundle(
            sale=persisted.sale,
            invoice=persisted.invoice,
            payments=persisted.payments,
            sale_lines=persisted.lines,
            tax_lines=persisted.tax_lines,
            products_by_id=products,
        )

    async def list_sales(self, *, tenant_id: str, branch_id: str) -> list[dict[str, object]]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
        records = await self._billing_repo.list_branch_sales(tenant_id=tenant_id, branch_id=branch_id)
        return [
            {
                "sale_id": sale.id,
                "invoice_number": invoice.invoice_number,
                "customer_name": sale.customer_name,
                "invoice_kind": sale.invoice_kind,
                "irn_status": sale.irn_status,
                "payment_method": self._payment_summary(payments)["payment_method"],
                "grand_total": sale.grand_total,
                "issued_on": invoice.issued_on,
            }
            for sale, invoice, payments in records
        ]

    async def create_sale_return(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        sale_id: str,
        actor_user_id: str,
        refund_amount: float,
        refund_method: str,
        lines: list[dict[str, float | str]],
        can_approve_refund: bool,
    ) -> dict[str, object]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")

        sale_bundle = await self._billing_repo.get_sale_bundle(tenant_id=tenant_id, branch_id=branch_id, sale_id=sale_id)
        if sale_bundle is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found")

        products = {
            product.id: product
            for product in await self._catalog_repo.list_products(tenant_id=tenant_id)
        }
        existing_returns = await self._billing_repo.list_sale_returns_for_sale(
            tenant_id=tenant_id,
            branch_id=branch_id,
            sale_id=sale_id,
        )
        return_lines_by_return_id = await self._billing_repo.list_sale_return_lines_for_returns(
            sale_return_ids=[record.id for record in existing_returns]
        )
        prior_returned_quantities_by_product_id: dict[str, float] = {}
        for return_lines in return_lines_by_return_id.values():
            for return_line in return_lines:
                prior_returned_quantities_by_product_id[return_line.product_id] = round(
                    prior_returned_quantities_by_product_id.get(return_line.product_id, 0.0) + return_line.quantity,
                    2,
                )

        sale_lines_by_product_id = {
            line.product_id: {
                "product_id": line.product_id,
                "product_name": products[line.product_id].name,
                "sku_code": products[line.product_id].sku_code,
                "hsn_sac_code": products[line.product_id].hsn_sac_code,
                "quantity": line.quantity,
                "unit_price": line.unit_price,
                "gst_rate": line.gst_rate,
            }
            for line in sale_bundle.lines
            if line.product_id in products
        }

        try:
            draft = build_sale_return_draft(
                branch_gstin=branch.gstin,
                sale_customer_name=sale_bundle.sale.customer_name,
                sale_customer_gstin=sale_bundle.sale.customer_gstin,
                sale_lines_by_product_id=sale_lines_by_product_id,
                prior_returned_quantities_by_product_id=prior_returned_quantities_by_product_id,
                requested_lines=lines,
            )
            ensure_refund_amount_allowed(
                requested_refund_amount=refund_amount,
                credit_note_total=draft.grand_total,
                remaining_refundable_amount=sum(payment.amount for payment in sale_bundle.payments) - sum(record.refund_amount for record in existing_returns),
            )
        except ValueError as error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

        sequence_number = await self._billing_repo.next_branch_credit_note_sequence(tenant_id=tenant_id, branch_id=branch_id)
        persisted = await self._billing_repo.create_sale_return(
            tenant_id=tenant_id,
            branch_id=branch_id,
            sale_id=sale_id,
            status="REFUND_APPROVED" if can_approve_refund else "REFUND_PENDING_APPROVAL",
            refund_amount=refund_amount,
            refund_method=refund_method,
            issued_on=utc_now().date(),
            credit_note_number=credit_note_number(branch_code=branch.code, sequence_number=sequence_number),
            subtotal=draft.subtotal,
            cgst_total=draft.cgst_total,
            sgst_total=draft.sgst_total,
            igst_total=draft.igst_total,
            grand_total=draft.grand_total,
            lines=[
                {
                    "product_id": line.product_id,
                    "quantity": line.quantity,
                    "unit_price": line.unit_price,
                    "gst_rate": line.gst_rate,
                    "line_subtotal": line.line_subtotal,
                    "tax_total": line.tax_total,
                    "line_total": line.line_total,
                }
                for line in draft.lines
            ],
            tax_lines=[
                {
                    "tax_type": line.tax_type,
                    "tax_rate": line.tax_rate,
                    "taxable_amount": line.taxable_amount,
                    "tax_amount": line.tax_amount,
                }
                for line in draft.tax_lines
            ],
        )
        await self._inventory_repo.create_inventory_ledger_entries(
            entries=[
                {
                    "tenant_id": tenant_id,
                    "branch_id": branch_id,
                    "product_id": line.product_id,
                    "entry_type": "CUSTOMER_RETURN",
                    "quantity": abs(line.quantity),
                    "reference_type": "sale_return",
                    "reference_id": persisted.sale_return.id,
                }
                for line in draft.lines
            ]
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="sale_return.created",
            entity_type="sale_return",
            entity_id=persisted.sale_return.id,
            payload={
                "sale_id": sale_id,
                "credit_note_number": persisted.credit_note.credit_note_number,
                "status": persisted.sale_return.status,
            },
        )
        if can_approve_refund:
            await self._audit_repo.record(
                tenant_id=tenant_id,
                branch_id=branch_id,
                actor_user_id=actor_user_id,
                action="sale_return.refund_approved",
                entity_type="sale_return",
                entity_id=persisted.sale_return.id,
                payload={"refund_amount": persisted.sale_return.refund_amount},
            )
        await self._session.commit()
        return self._serialize_sale_return_bundle(
            sale_return=persisted.sale_return,
            credit_note=persisted.credit_note,
            sale_return_lines=persisted.lines,
            credit_note_tax_lines=persisted.tax_lines,
            products_by_id=products,
        )

    async def create_exchange(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        sale_id: str,
        actor_user_id: str,
        settlement_method: str,
        return_lines: list[dict[str, float | str]],
        replacement_lines: list[dict[str, float | str]],
        can_approve_refund: bool,
    ) -> dict[str, object]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
        if branch.gstin is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Branch GSTIN is required for exchange")

        sale_bundle = await self._billing_repo.get_sale_bundle(tenant_id=tenant_id, branch_id=branch_id, sale_id=sale_id)
        if sale_bundle is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found")

        products = {
            product.id: product
            for product in await self._catalog_repo.list_products(tenant_id=tenant_id)
        }
        branch_catalog_items = await self._catalog_repo.list_branch_catalog_items(tenant_id=tenant_id, branch_id=branch_id)
        branch_catalog_by_product_id: dict[str, dict[str, object]] = {}
        for item in branch_catalog_items:
            product = products.get(item.product_id)
            if product is None:
                continue
            branch_catalog_by_product_id[item.product_id] = {
                "availability_status": item.availability_status,
                "effective_selling_price": item.selling_price_override if item.selling_price_override is not None else product.selling_price,
            }

        existing_returns = await self._billing_repo.list_sale_returns_for_sale(
            tenant_id=tenant_id,
            branch_id=branch_id,
            sale_id=sale_id,
        )
        return_lines_by_return_id = await self._billing_repo.list_sale_return_lines_for_returns(
            sale_return_ids=[record.id for record in existing_returns]
        )
        prior_returned_quantities_by_product_id: dict[str, float] = {}
        for persisted_return_lines in return_lines_by_return_id.values():
            for return_line in persisted_return_lines:
                prior_returned_quantities_by_product_id[return_line.product_id] = round(
                    prior_returned_quantities_by_product_id.get(return_line.product_id, 0.0) + return_line.quantity,
                    2,
                )

        sale_lines_by_product_id = {
            line.product_id: {
                "product_id": line.product_id,
                "product_name": products[line.product_id].name,
                "sku_code": products[line.product_id].sku_code,
                "hsn_sac_code": products[line.product_id].hsn_sac_code,
                "quantity": line.quantity,
                "unit_price": line.unit_price,
                "gst_rate": line.gst_rate,
            }
            for line in sale_bundle.lines
            if line.product_id in products
        }

        try:
            return_draft = build_sale_return_draft(
                branch_gstin=branch.gstin,
                sale_customer_name=sale_bundle.sale.customer_name,
                sale_customer_gstin=sale_bundle.sale.customer_gstin,
                sale_lines_by_product_id=sale_lines_by_product_id,
                prior_returned_quantities_by_product_id=prior_returned_quantities_by_product_id,
                requested_lines=return_lines,
            )
            replacement_draft = build_sale_draft(
                line_inputs=replacement_lines,
                branch_gstin=branch.gstin,
                customer_name=sale_bundle.sale.customer_name,
                customer_gstin=sale_bundle.sale.customer_gstin,
                products_by_id=products,
                branch_catalog_items_by_product_id=branch_catalog_by_product_id,
            )
        except ValueError as error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

        returned_quantities_by_product_id = {line.product_id: line.quantity for line in return_draft.lines}
        for line in replacement_draft.lines:
            available_quantity = await self._inventory_repo.stock_on_hand(
                tenant_id=tenant_id,
                branch_id=branch_id,
                product_id=line.product_id,
            )
            try:
                ensure_sale_stock_available(
                    requested_quantity=line.quantity,
                    available_quantity=available_quantity + returned_quantities_by_product_id.get(line.product_id, 0.0),
                )
            except ValueError as error:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

        settlement = build_exchange_settlement(
            credit_note_total=return_draft.grand_total,
            replacement_total=replacement_draft.grand_total,
            settlement_method=settlement_method,
            can_approve_refund=can_approve_refund,
        )
        ensure_refund_amount_allowed(
            requested_refund_amount=settlement.refund_amount,
            credit_note_total=return_draft.grand_total,
            remaining_refundable_amount=sum(payment.amount for payment in sale_bundle.payments) - sum(record.refund_amount for record in existing_returns),
        )

        credit_note_sequence = await self._billing_repo.next_branch_credit_note_sequence(tenant_id=tenant_id, branch_id=branch_id)
        persisted_return = await self._billing_repo.create_sale_return(
            tenant_id=tenant_id,
            branch_id=branch_id,
            sale_id=sale_id,
            status=settlement.sale_return_status,
            refund_amount=settlement.refund_amount,
            refund_method=settlement.refund_method,
            issued_on=utc_now().date(),
            credit_note_number=credit_note_number(branch_code=branch.code, sequence_number=credit_note_sequence),
            subtotal=return_draft.subtotal,
            cgst_total=return_draft.cgst_total,
            sgst_total=return_draft.sgst_total,
            igst_total=return_draft.igst_total,
            grand_total=return_draft.grand_total,
            lines=[
                {
                    "product_id": line.product_id,
                    "quantity": line.quantity,
                    "unit_price": line.unit_price,
                    "gst_rate": line.gst_rate,
                    "line_subtotal": line.line_subtotal,
                    "tax_total": line.tax_total,
                    "line_total": line.line_total,
                }
                for line in return_draft.lines
            ],
            tax_lines=[
                {
                    "tax_type": line.tax_type,
                    "tax_rate": line.tax_rate,
                    "taxable_amount": line.taxable_amount,
                    "tax_amount": line.tax_amount,
                }
                for line in return_draft.tax_lines
            ],
        )
        await self._inventory_repo.create_inventory_ledger_entries(
            entries=[
                {
                    "tenant_id": tenant_id,
                    "branch_id": branch_id,
                    "product_id": line.product_id,
                    "entry_type": "CUSTOMER_RETURN",
                    "quantity": abs(line.quantity),
                    "reference_type": "sale_return",
                    "reference_id": persisted_return.sale_return.id,
                }
                for line in return_draft.lines
            ]
        )

        sale_sequence = await self._billing_repo.next_branch_sale_sequence(tenant_id=tenant_id, branch_id=branch_id)
        persisted_sale = await self._billing_repo.create_sale(
            tenant_id=tenant_id,
            branch_id=branch_id,
            customer_name=replacement_draft.customer_name,
            customer_gstin=replacement_draft.customer_gstin,
            invoice_kind=replacement_draft.invoice_kind,
            irn_status=replacement_draft.irn_status,
            issued_on=utc_now().date(),
            invoice_number=sale_invoice_number(branch_code=branch.code, sequence_number=sale_sequence),
            subtotal=replacement_draft.subtotal,
            tax_total=replacement_draft.tax_total,
            cgst_total=replacement_draft.cgst_total,
            sgst_total=replacement_draft.sgst_total,
            igst_total=replacement_draft.igst_total,
            grand_total=replacement_draft.grand_total,
            payment_method=None,
            payments=[
                {"payment_method": allocation.payment_method, "amount": allocation.amount}
                for allocation in settlement.payment_allocations
            ],
            lines=[
                {
                    "product_id": line.product_id,
                    "quantity": line.quantity,
                    "unit_price": line.unit_price,
                    "gst_rate": line.gst_rate,
                    "line_subtotal": line.line_subtotal,
                    "tax_total": line.tax_total,
                    "line_total": line.line_total,
                }
                for line in replacement_draft.lines
            ],
            tax_lines=[
                {
                    "tax_type": line.tax_type,
                    "tax_rate": line.tax_rate,
                    "taxable_amount": line.taxable_amount,
                    "tax_amount": line.tax_amount,
                }
                for line in replacement_draft.tax_lines
            ],
        )
        await self._inventory_repo.create_inventory_ledger_entries(
            entries=[
                {
                    "tenant_id": tenant_id,
                    "branch_id": branch_id,
                    "product_id": line.product_id,
                    "entry_type": "SALE",
                    "quantity": -abs(line.quantity),
                    "reference_type": "sale",
                    "reference_id": persisted_sale.sale.id,
                }
                for line in replacement_draft.lines
            ]
        )
        exchange_order = await self._billing_repo.create_exchange_order(
            tenant_id=tenant_id,
            branch_id=branch_id,
            original_sale_id=sale_id,
            replacement_sale_id=persisted_sale.sale.id,
            sale_return_id=persisted_return.sale_return.id,
            status=settlement.exchange_status,
            balance_direction=settlement.balance_direction,
            balance_amount=settlement.balance_amount,
            settlement_method=settlement_method,
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="exchange.created",
            entity_type="exchange_order",
            entity_id=exchange_order.id,
            payload={
                "original_sale_id": sale_id,
                "replacement_sale_id": persisted_sale.sale.id,
                "sale_return_id": persisted_return.sale_return.id,
                "balance_direction": settlement.balance_direction,
                "balance_amount": settlement.balance_amount,
            },
        )
        if settlement.exchange_status == "COMPLETED" and settlement.sale_return_status == "REFUND_APPROVED":
            await self._audit_repo.record(
                tenant_id=tenant_id,
                branch_id=branch_id,
                actor_user_id=actor_user_id,
                action="sale_return.refund_approved",
                entity_type="sale_return",
                entity_id=persisted_return.sale_return.id,
                payload={"note": "Approved during exchange"},
            )
        await self._session.commit()
        return {
            "id": exchange_order.id,
            "tenant_id": exchange_order.tenant_id,
            "branch_id": exchange_order.branch_id,
            "original_sale_id": exchange_order.original_sale_id,
            "replacement_sale_id": exchange_order.replacement_sale_id,
            "sale_return_id": exchange_order.sale_return_id,
            "status": exchange_order.status,
            "balance_direction": exchange_order.balance_direction,
            "balance_amount": exchange_order.balance_amount,
            "settlement_method": exchange_order.settlement_method,
            "payment_allocations": [
                {"payment_method": allocation.payment_method, "amount": allocation.amount}
                for allocation in settlement.payment_allocations
            ],
            "sale_return": self._serialize_sale_return_bundle(
                sale_return=persisted_return.sale_return,
                credit_note=persisted_return.credit_note,
                sale_return_lines=persisted_return.lines,
                credit_note_tax_lines=persisted_return.tax_lines,
                products_by_id=products,
            ),
            "replacement_sale": self._serialize_sale_bundle(
                sale=persisted_sale.sale,
                invoice=persisted_sale.invoice,
                payments=persisted_sale.payments,
                sale_lines=persisted_sale.lines,
                tax_lines=persisted_sale.tax_lines,
                products_by_id=products,
            ),
        }

    async def list_sale_returns(self, *, tenant_id: str, branch_id: str) -> list[dict[str, object]]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
        records = await self._billing_repo.list_branch_sale_returns(tenant_id=tenant_id, branch_id=branch_id)
        return [
            {
                "sale_return_id": sale_return.id,
                "sale_id": sale.id,
                "invoice_number": invoice.invoice_number,
                "customer_name": sale.customer_name,
                "status": sale_return.status,
                "refund_amount": sale_return.refund_amount,
                "refund_method": sale_return.refund_method,
                "credit_note_number": credit_note.credit_note_number,
                "credit_note_total": credit_note.grand_total,
                "issued_on": credit_note.issued_on,
            }
            for sale_return, credit_note, sale, invoice in records
        ]

    async def approve_sale_return_refund(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        sale_return_id: str,
        actor_user_id: str,
        note: str | None,
    ) -> dict[str, object]:
        sale_return = await self._billing_repo.get_sale_return(
            tenant_id=tenant_id,
            branch_id=branch_id,
            sale_return_id=sale_return_id,
        )
        if sale_return is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale return not found")
        sale_return.status = "REFUND_APPROVED"
        credit_note = await self._billing_repo.get_credit_note_for_sale_return(sale_return_id=sale_return.id)
        if credit_note is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credit note not found")
        return_lines = (await self._billing_repo.list_sale_return_lines_for_returns(sale_return_ids=[sale_return.id])).get(sale_return.id, [])
        credit_note_tax_lines = (
            await self._billing_repo.list_credit_note_tax_lines_for_credit_notes(credit_note_ids=[credit_note.id])
        ).get(credit_note.id, [])
        products = {
            product.id: product
            for product in await self._catalog_repo.list_products(tenant_id=tenant_id)
        }
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="sale_return.refund_approved",
            entity_type="sale_return",
            entity_id=sale_return.id,
            payload={"note": note} if note else {},
        )
        await self._session.commit()
        return self._serialize_sale_return_bundle(
            sale_return=sale_return,
            credit_note=credit_note,
            sale_return_lines=return_lines,
            credit_note_tax_lines=credit_note_tax_lines,
            products_by_id=products,
        )

    def _serialize_sale_bundle(
        self,
        *,
        sale,
        invoice,
        payments,
        sale_lines,
        tax_lines,
        products_by_id,
    ) -> dict[str, object]:
        return {
            "id": sale.id,
            "tenant_id": sale.tenant_id,
            "branch_id": sale.branch_id,
            "customer_name": sale.customer_name,
            "customer_gstin": sale.customer_gstin,
            "invoice_kind": sale.invoice_kind,
            "irn_status": sale.irn_status,
            "invoice_number": invoice.invoice_number,
            "issued_on": invoice.issued_on,
            "subtotal": sale.subtotal,
            "cgst_total": invoice.cgst_total,
            "sgst_total": invoice.sgst_total,
            "igst_total": invoice.igst_total,
            "grand_total": invoice.grand_total,
            "payment": self._payment_summary(payments),
            "lines": [
                {
                    "product_id": line.product_id,
                    "product_name": products_by_id[line.product_id].name,
                    "sku_code": products_by_id[line.product_id].sku_code,
                    "hsn_sac_code": products_by_id[line.product_id].hsn_sac_code,
                    "quantity": line.quantity,
                    "unit_price": line.unit_price,
                    "gst_rate": line.gst_rate,
                    "line_subtotal": line.line_subtotal,
                    "tax_total": line.tax_total,
                    "line_total": line.line_total,
                }
                for line in sale_lines
            ],
            "tax_lines": [
                {
                    "tax_type": line.tax_type,
                    "tax_rate": line.tax_rate,
                    "taxable_amount": line.taxable_amount,
                    "tax_amount": line.tax_amount,
                }
                for line in tax_lines
            ],
        }

    def _payment_summary(self, payments) -> dict[str, object]:
        if len(payments) == 1:
            return {
                "payment_method": payments[0].payment_method,
                "amount": payments[0].amount,
            }
        return {
            "payment_method": "MIXED",
            "amount": round(sum(payment.amount for payment in payments), 2),
        }

    def _serialize_sale_return_bundle(
        self,
        *,
        sale_return,
        credit_note,
        sale_return_lines,
        credit_note_tax_lines,
        products_by_id,
    ) -> dict[str, object]:
        return {
            "id": sale_return.id,
            "tenant_id": sale_return.tenant_id,
            "branch_id": sale_return.branch_id,
            "sale_id": sale_return.sale_id,
            "status": sale_return.status,
            "refund_amount": sale_return.refund_amount,
            "refund_method": sale_return.refund_method,
            "lines": [
                {
                    "product_id": line.product_id,
                    "product_name": products_by_id[line.product_id].name,
                    "sku_code": products_by_id[line.product_id].sku_code,
                    "hsn_sac_code": products_by_id[line.product_id].hsn_sac_code,
                    "quantity": line.quantity,
                    "unit_price": line.unit_price,
                    "gst_rate": line.gst_rate,
                    "line_subtotal": line.line_subtotal,
                    "tax_total": line.tax_total,
                    "line_total": line.line_total,
                }
                for line in sale_return_lines
            ],
            "credit_note": {
                "id": credit_note.id,
                "credit_note_number": credit_note.credit_note_number,
                "issued_on": credit_note.issued_on,
                "subtotal": credit_note.subtotal,
                "cgst_total": credit_note.cgst_total,
                "sgst_total": credit_note.sgst_total,
                "igst_total": credit_note.igst_total,
                "grand_total": credit_note.grand_total,
                "tax_lines": [
                    {
                        "tax_type": line.tax_type,
                        "tax_rate": line.tax_rate,
                        "taxable_amount": line.taxable_amount,
                        "tax_amount": line.tax_amount,
                    }
                    for line in credit_note_tax_lines
                ],
            },
        }
