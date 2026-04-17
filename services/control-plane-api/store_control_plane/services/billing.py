from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories import AuditRepository, BillingRepository, CatalogRepository, InventoryRepository, TenantRepository
from ..utils import utc_now
from .billing_policy import build_sale_draft, ensure_sale_stock_available, sale_invoice_number
from .checkout_pricing import CheckoutPricingService
from .customer_profiles import CustomerProfileService
from .gift_cards import GiftCardService
from .exchange_policy import build_exchange_settlement
from .loyalty import LoyaltyService
from .promotions import PromotionService
from .returns_policy import build_sale_return_draft, credit_note_number, ensure_refund_amount_allowed
from .store_credit import StoreCreditService
from .workforce import WorkforceService


class BillingService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._tenant_repo = TenantRepository(session)
        self._catalog_repo = CatalogRepository(session)
        self._inventory_repo = InventoryRepository(session)
        self._billing_repo = BillingRepository(session)
        self._audit_repo = AuditRepository(session)
        self._checkout_pricing_service = CheckoutPricingService(session)
        self._customer_profile_service = CustomerProfileService(session)
        self._loyalty_service = LoyaltyService(session)
        self._promotion_service = PromotionService(session)
        self._gift_card_service = GiftCardService(session)
        self._store_credit_service = StoreCreditService(session)
        self._workforce_service = WorkforceService(session)

    async def create_sale(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        actor_user_id: str | None,
        customer_profile_id: str | None,
        customer_name: str,
        customer_gstin: str | None,
        payment_method: str,
        promotion_code: str | None = None,
        customer_voucher_id: str | None = None,
        gift_card_code: str | None = None,
        gift_card_amount: float = 0.0,
        pricing_snapshot: dict[str, object] | None = None,
        store_credit_amount: float = 0.0,
        loyalty_points_to_redeem: int = 0,
        lines: list[dict[str, float | str]],
        cashier_session_id: str | None = None,
        auto_commit: bool = True,
    ) -> dict[str, object]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
        if cashier_session_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cashier session is required")
        cashier_session = await self._workforce_service.require_open_cashier_session(
            tenant_id=tenant_id,
            branch_id=branch_id,
            cashier_session_id=cashier_session_id,
            actor_user_id=actor_user_id,
        )

        preview = pricing_snapshot
        if preview is None:
            preview = await self._checkout_pricing_service.build_preview(
                tenant_id=tenant_id,
                branch_id=branch_id,
                customer_profile_id=customer_profile_id,
                customer_name=customer_name,
                customer_gstin=customer_gstin,
                promotion_code=promotion_code,
                customer_voucher_id=customer_voucher_id,
                gift_card_code=gift_card_code,
                gift_card_amount=gift_card_amount,
                loyalty_points_to_redeem=loyalty_points_to_redeem,
                store_credit_amount=store_credit_amount,
                lines=lines,
                validate_stock=True,
            )

        preview_summary = dict(preview["summary"])
        preview_lines = list(preview["lines"])
        preview_tax_lines = list(preview["tax_lines"])
        automatic_campaign = preview.get("automatic_campaign")
        promotion_code_campaign = preview.get("promotion_code_campaign")
        customer_voucher = preview.get("customer_voucher")
        gift_card = preview.get("gift_card")
        loyalty_points_redeemed = int(preview.get("loyalty_points_to_redeem", 0))
        loyalty_points_earned = int(preview.get("loyalty_points_earned", 0))
        loyalty_discount_amount = round(float(preview_summary.get("loyalty_discount_total", 0.0)), 2)
        gift_card_amount = round(float(preview_summary.get("gift_card_amount", 0.0)), 2)
        store_credit_amount = round(float(preview_summary.get("store_credit_amount", 0.0)), 2)
        net_sale_total = round(float(preview_summary.get("grand_total", 0.0)), 2)
        payment_rows: list[dict[str, float | str]] = []
        remaining_payment_amount = net_sale_total
        if store_credit_amount > 0:
            payment_rows.append({"payment_method": "STORE_CREDIT", "amount": store_credit_amount})
            remaining_payment_amount = round(remaining_payment_amount - store_credit_amount, 2)
        if gift_card_amount > 0:
            payment_rows.append({"payment_method": "GIFT_CARD", "amount": gift_card_amount})
            remaining_payment_amount = round(remaining_payment_amount - gift_card_amount, 2)
        if remaining_payment_amount > 0:
            payment_rows.append({"payment_method": payment_method, "amount": remaining_payment_amount})

        sequence_number = await self._billing_repo.next_branch_sale_sequence(tenant_id=tenant_id, branch_id=branch_id)
        persisted = await self._billing_repo.create_sale(
            tenant_id=tenant_id,
            branch_id=branch_id,
            cashier_session_id=cashier_session.id,
            customer_profile_id=customer_profile_id,
            customer_name=str(preview["customer_name"]),
            customer_gstin=preview.get("customer_gstin"),
            automatic_campaign_name=automatic_campaign["name"] if automatic_campaign is not None else None,
            automatic_discount_total=round(float(preview_summary.get("automatic_discount_total", 0.0)), 2),
            promotion_campaign_id=promotion_code_campaign["id"] if promotion_code_campaign is not None else None,
            promotion_code_id=promotion_code_campaign["code_id"] if promotion_code_campaign is not None else None,
            customer_voucher_id=customer_voucher["id"] if customer_voucher is not None else None,
            gift_card_id=gift_card["id"] if gift_card is not None else None,
            customer_voucher_name=customer_voucher["voucher_name"] if customer_voucher is not None else None,
            gift_card_code=gift_card["gift_card_code"] if gift_card is not None else None,
            gift_card_amount=gift_card_amount,
            promotion_code=promotion_code_campaign["code"] if promotion_code_campaign is not None else None,
            promotion_discount_amount=round(float(preview_summary.get("promotion_code_discount_total", 0.0)), 2),
            customer_voucher_discount_total=round(
                float(preview_summary.get("customer_voucher_discount_total", 0.0)),
                2,
            ),
            promotion_code_discount_total=round(float(preview_summary.get("promotion_code_discount_total", 0.0)), 2),
            invoice_kind=str(preview["invoice_kind"]),
            irn_status=str(preview["irn_status"]),
            issued_on=utc_now().date(),
            mrp_total=round(float(preview_summary.get("mrp_total", 0.0)), 2),
            selling_price_subtotal=round(float(preview_summary.get("selling_price_subtotal", 0.0)), 2),
            total_discount=round(float(preview_summary.get("total_discount", 0.0)), 2),
            invoice_total=round(float(preview_summary.get("invoice_total", 0.0)), 2),
            invoice_number=sale_invoice_number(branch_code=branch.code, sequence_number=sequence_number),
            subtotal=round(float(preview_summary.get("selling_price_subtotal", 0.0)), 2),
            tax_total=round(float(preview_summary.get("tax_total", 0.0)), 2),
            cgst_total=round(
                sum(float(line["tax_amount"]) for line in preview_tax_lines if line["tax_type"] == "CGST"),
                2,
            ),
            sgst_total=round(
                sum(float(line["tax_amount"]) for line in preview_tax_lines if line["tax_type"] == "SGST"),
                2,
            ),
            igst_total=round(
                sum(float(line["tax_amount"]) for line in preview_tax_lines if line["tax_type"] == "IGST"),
                2,
            ),
            grand_total=net_sale_total,
            loyalty_points_redeemed=loyalty_points_redeemed,
            loyalty_discount_amount=loyalty_discount_amount,
            loyalty_points_earned=loyalty_points_earned,
            payment_method=payment_method,
            payments=payment_rows or None,
            lines=preview_lines,
            tax_lines=preview_tax_lines,
        )
        if promotion_code_campaign is not None:
            await self._promotion_service.mark_code_redeemed(
                tenant_id=tenant_id,
                promotion_code_id=str(promotion_code_campaign["code_id"]),
            )
        if customer_voucher is not None:
            await self._promotion_service.mark_customer_voucher_redeemed(
                tenant_id=tenant_id,
                voucher_id=str(customer_voucher["id"]),
                sale_id=persisted.sale.id,
            )
        if gift_card is not None and gift_card_amount > 0:
            await self._gift_card_service.redeem_gift_card(
                tenant_id=tenant_id,
                gift_card_id=str(gift_card["id"]),
                amount=gift_card_amount,
                branch_id=branch_id,
                source_reference_id=persisted.sale.id,
                note=f"Sale {persisted.invoice.invoice_number}",
            )
        if store_credit_amount > 0:
            await self._store_credit_service.redeem_customer_store_credit(
                tenant_id=tenant_id,
                customer_profile_id=customer_profile_id,
                amount=store_credit_amount,
                branch_id=branch_id,
                source_reference_id=persisted.sale.id,
                note=f"Sale {persisted.invoice.invoice_number}",
            )
        if loyalty_points_redeemed > 0:
            await self._loyalty_service.redeem_customer_loyalty(
                tenant_id=tenant_id,
                customer_profile_id=customer_profile_id,
                points_to_redeem=loyalty_points_redeemed,
                branch_id=branch_id,
                source_reference_id=persisted.sale.id,
                note=f"Sale {persisted.invoice.invoice_number}",
            )
        if customer_profile_id is not None and loyalty_points_earned > 0:
            await self._loyalty_service.earn_customer_loyalty(
                tenant_id=tenant_id,
                customer_profile_id=customer_profile_id,
                eligible_sale_amount=net_sale_total,
                branch_id=branch_id,
                source_reference_id=persisted.sale.id,
                note=f"Sale {persisted.invoice.invoice_number}",
            )
        await self._inventory_repo.create_inventory_ledger_entries(
            entries=[
                {
                    "tenant_id": tenant_id,
                    "branch_id": branch_id,
                    "product_id": str(line["product_id"]),
                    "entry_type": "SALE",
                    "quantity": -abs(float(line["quantity"])),
                    "reference_type": "sale",
                    "reference_id": persisted.sale.id,
                }
                for line in preview_lines
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
        await self._workforce_service.touch_cashier_session_activity(cashier_session=cashier_session)
        if auto_commit:
            await self._session.commit()
        products = {
            product.id: product
            for product in await self._catalog_repo.list_products(tenant_id=tenant_id)
        }
        return self._serialize_sale_bundle(
            sale=persisted.sale,
            invoice=persisted.invoice,
            payments=persisted.payments,
            sale_lines=persisted.lines,
            tax_lines=persisted.tax_lines,
            products_by_id=products,
        )

    async def get_sale(self, *, tenant_id: str, branch_id: str, sale_id: str) -> dict[str, object]:
        sale_bundle = await self._billing_repo.get_sale_bundle(tenant_id=tenant_id, branch_id=branch_id, sale_id=sale_id)
        if sale_bundle is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found")
        products = {
            product.id: product
            for product in await self._catalog_repo.list_products(tenant_id=tenant_id)
        }
        return self._serialize_sale_bundle(
            sale=sale_bundle.sale,
            invoice=sale_bundle.invoice,
            payments=sale_bundle.payments,
            sale_lines=sale_bundle.lines,
            tax_lines=sale_bundle.tax_lines,
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
                "cashier_session_id": sale.cashier_session_id,
                "customer_profile_id": sale.customer_profile_id,
                "invoice_number": invoice.invoice_number,
                "customer_name": sale.customer_name,
                "invoice_kind": sale.invoice_kind,
                "irn_status": sale.irn_status,
                "payment_method": self._payment_summary(payments)["payment_method"],
                "automatic_campaign_name": sale.automatic_campaign_name,
                "automatic_discount_total": sale.automatic_discount_total,
                "promotion_code_discount_total": sale.promotion_code_discount_total,
                "total_discount": sale.total_discount,
                "invoice_total": sale.invoice_total,
                "grand_total": sale.grand_total,
                "promotion_campaign_id": sale.promotion_campaign_id,
                "promotion_code_id": sale.promotion_code_id,
                "promotion_code": sale.promotion_code,
                "promotion_discount_amount": sale.promotion_discount_amount,
                "gift_card_id": sale.gift_card_id,
                "gift_card_code": sale.gift_card_code,
                "gift_card_amount": sale.gift_card_amount
                if sale.gift_card_amount > 0
                else round(sum(payment.amount for payment in payments if payment.payment_method == "GIFT_CARD"), 2),
                "store_credit_amount": round(
                    sum(payment.amount for payment in payments if payment.payment_method == "STORE_CREDIT"),
                    2,
                ),
                "loyalty_points_redeemed": sale.loyalty_points_redeemed,
                "loyalty_discount_amount": sale.loyalty_discount_amount,
                "loyalty_points_earned": sale.loyalty_points_earned,
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
        cashier_session_id: str | None,
        refund_amount: float,
        refund_method: str,
        lines: list[dict[str, float | str]],
        can_approve_refund: bool,
    ) -> dict[str, object]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
        if cashier_session_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cashier session is required")
        cashier_session = await self._workforce_service.require_open_cashier_session(
            tenant_id=tenant_id,
            branch_id=branch_id,
            cashier_session_id=cashier_session_id,
            actor_user_id=actor_user_id,
        )

        sale_bundle = await self._billing_repo.get_sale_bundle(tenant_id=tenant_id, branch_id=branch_id, sale_id=sale_id)
        if sale_bundle is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found")
        if refund_method == "STORE_CREDIT" and sale_bundle.sale.customer_profile_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer profile is required for store credit refunds",
            )

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
            cashier_session_id=cashier_session.id,
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
        await self._workforce_service.touch_cashier_session_activity(cashier_session=cashier_session)
        if can_approve_refund:
            if persisted.sale_return.refund_method == "STORE_CREDIT" and persisted.sale_return.refund_amount > 0:
                await self._store_credit_service.issue_customer_store_credit(
                    tenant_id=tenant_id,
                    customer_profile_id=sale_bundle.sale.customer_profile_id,
                    amount=persisted.sale_return.refund_amount,
                    note=f"Sale return {persisted.credit_note.credit_note_number}",
                    branch_id=branch_id,
                    source_type="RETURN_REFUND",
                    source_reference_id=persisted.sale_return.id,
                )
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
            customer_profile_id=sale_bundle.sale.customer_profile_id,
            customer_name=replacement_draft.customer_name,
            customer_gstin=replacement_draft.customer_gstin,
            promotion_campaign_id=None,
            promotion_code_id=None,
            customer_voucher_id=None,
            gift_card_id=None,
            customer_voucher_name=None,
            gift_card_code=None,
            gift_card_amount=0.0,
            promotion_code=None,
            promotion_discount_amount=0.0,
            customer_voucher_discount_total=0.0,
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
            loyalty_points_redeemed=0,
            loyalty_discount_amount=0.0,
            loyalty_points_earned=0,
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
                "cashier_session_id": sale_return.cashier_session_id,
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
        already_approved = sale_return.status == "REFUND_APPROVED"
        sale_return.status = "REFUND_APPROVED"
        credit_note = await self._billing_repo.get_credit_note_for_sale_return(sale_return_id=sale_return.id)
        if credit_note is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credit note not found")
        sale_bundle = await self._billing_repo.get_sale_bundle(
            tenant_id=tenant_id,
            branch_id=branch_id,
            sale_id=sale_return.sale_id,
        )
        if sale_bundle is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found")
        if sale_return.refund_method == "STORE_CREDIT":
            if sale_bundle.sale.customer_profile_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Customer profile is required for store credit refunds",
                )
            if not already_approved and sale_return.refund_amount > 0:
                await self._store_credit_service.issue_customer_store_credit(
                    tenant_id=tenant_id,
                    customer_profile_id=sale_bundle.sale.customer_profile_id,
                    amount=sale_return.refund_amount,
                    note=f"Sale return {credit_note.credit_note_number}",
                    branch_id=branch_id,
                    source_type="RETURN_REFUND",
                    source_reference_id=sale_return.id,
                )
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
            "sale_id": sale.id,
            "tenant_id": sale.tenant_id,
            "branch_id": sale.branch_id,
            "cashier_session_id": sale.cashier_session_id,
            "customer_profile_id": sale.customer_profile_id,
            "customer_name": sale.customer_name,
            "customer_gstin": sale.customer_gstin,
            "invoice_kind": sale.invoice_kind,
            "irn_status": sale.irn_status,
            "invoice_number": invoice.invoice_number,
            "issued_on": invoice.issued_on,
            "mrp_total": sale.mrp_total,
            "selling_price_subtotal": sale.selling_price_subtotal,
            "subtotal": sale.subtotal,
            "cgst_total": invoice.cgst_total,
            "sgst_total": invoice.sgst_total,
            "igst_total": invoice.igst_total,
            "automatic_campaign_name": sale.automatic_campaign_name,
            "automatic_discount_total": sale.automatic_discount_total,
            "promotion_code_discount_total": sale.promotion_code_discount_total,
            "total_discount": sale.total_discount,
            "invoice_total": sale.invoice_total,
            "grand_total": sale.grand_total,
            "promotion_campaign_id": sale.promotion_campaign_id,
            "promotion_code_id": sale.promotion_code_id,
            "customer_voucher_id": sale.customer_voucher_id,
            "gift_card_id": sale.gift_card_id,
            "customer_voucher_name": sale.customer_voucher_name,
            "gift_card_code": sale.gift_card_code,
            "promotion_code": sale.promotion_code,
            "promotion_discount_amount": sale.promotion_discount_amount,
            "customer_voucher_discount_total": sale.customer_voucher_discount_total,
            "gift_card_amount": sale.gift_card_amount
            if sale.gift_card_amount > 0
            else round(sum(payment.amount for payment in payments if payment.payment_method == "GIFT_CARD"), 2),
            "store_credit_amount": round(
                sum(payment.amount for payment in payments if payment.payment_method == "STORE_CREDIT"),
                2,
            ),
            "loyalty_points_redeemed": sale.loyalty_points_redeemed,
            "loyalty_discount_amount": sale.loyalty_discount_amount,
            "loyalty_points_earned": sale.loyalty_points_earned,
            "payment": self._payment_summary(payments),
            "lines": [
                {
                    "product_id": line.product_id,
                    "product_name": products_by_id[line.product_id].name,
                    "sku_code": products_by_id[line.product_id].sku_code,
                    "hsn_sac_code": products_by_id[line.product_id].hsn_sac_code,
                    "quantity": line.quantity,
                    "mrp": line.mrp,
                    "unit_selling_price": line.unit_selling_price,
                    "unit_price": line.unit_price,
                    "gst_rate": line.gst_rate,
                    "automatic_discount_amount": line.automatic_discount_amount,
                    "promotion_code_discount_amount": line.promotion_code_discount_amount,
                    "customer_voucher_discount_amount": (
                        line.customer_voucher_discount_amount if line.customer_voucher_discount_amount > 0 else None
                    ),
                    "promotion_discount_source": line.promotion_discount_source,
                    "taxable_amount": line.taxable_amount,
                    "tax_amount": line.tax_amount,
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

    async def _resolve_promotion_application(
        self,
        *,
        tenant_id: str,
        sale_total: float,
        promotion_code: str | None,
        promotion_snapshot: dict[str, object] | None,
    ) -> dict[str, object]:
        if promotion_code and promotion_snapshot:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Promotion code and promotion snapshot cannot both be supplied",
            )
        if promotion_snapshot is not None:
            discount_amount = round(float(promotion_snapshot.get("promotion_discount_amount", 0.0) or 0.0), 2)
            if discount_amount < 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Promotion discount amount must be non-negative")
            if discount_amount > round(float(sale_total), 2):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Promotion discount amount cannot exceed sale total")
            return {
                "promotion_campaign_id": promotion_snapshot.get("promotion_campaign_id"),
                "promotion_code_id": promotion_snapshot.get("promotion_code_id"),
                "promotion_code": promotion_snapshot.get("promotion_code"),
                "promotion_discount_amount": discount_amount,
            }
        if not promotion_code:
            return {
                "promotion_campaign_id": None,
                "promotion_code_id": None,
                "promotion_code": None,
                "promotion_discount_amount": 0.0,
            }
        validated = await self._promotion_service.validate_promotion_code(
            tenant_id=tenant_id,
            promotion_code=promotion_code,
            sale_total=sale_total,
        )
        return {
            "promotion_campaign_id": validated["campaign"].id,
            "promotion_code_id": validated["code"].id,
            "promotion_code": validated["code"].code,
            "promotion_discount_amount": round(float(validated["discount_amount"]), 2),
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
            "cashier_session_id": sale_return.cashier_session_id,
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
