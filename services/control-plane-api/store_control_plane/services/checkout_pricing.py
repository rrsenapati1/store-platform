from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories import CatalogRepository, InventoryRepository, TenantRepository
from .billing_policy import build_sale_draft, ensure_sale_stock_available
from .customer_profiles import CustomerProfileService
from .loyalty import LoyaltyService
from .promotions import PromotionService
from .purchase_policy import money
from .store_credit import StoreCreditService


@dataclass(slots=True)
class _AutomaticCampaignEvaluation:
    campaign: object
    scope_label: str
    discount_total: float
    line_allocations: list[float]


class CheckoutPricingService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._tenant_repo = TenantRepository(session)
        self._catalog_repo = CatalogRepository(session)
        self._inventory_repo = InventoryRepository(session)
        self._customer_profile_service = CustomerProfileService(session)
        self._promotion_service = PromotionService(session)
        self._loyalty_service = LoyaltyService(session)
        self._store_credit_service = StoreCreditService(session)

    async def build_preview(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        customer_profile_id: str | None,
        customer_name: str,
        customer_gstin: str | None,
        promotion_code: str | None,
        customer_voucher_id: str | None,
        loyalty_points_to_redeem: int,
        store_credit_amount: float,
        lines: list[dict[str, object]],
        validate_stock: bool = True,
    ) -> dict[str, object]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
        if branch.gstin is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Branch GSTIN is required for billing")

        resolved_customer_name = customer_name
        resolved_customer_gstin = customer_gstin
        if customer_profile_id is not None:
            profile = await self._customer_profile_service.require_active_profile(
                tenant_id=tenant_id,
                customer_profile_id=customer_profile_id,
            )
            resolved_customer_name = profile.full_name
            resolved_customer_gstin = profile.gstin

        products = {product.id: product for product in await self._catalog_repo.list_products(tenant_id=tenant_id)}
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
                customer_name=resolved_customer_name,
                customer_gstin=resolved_customer_gstin,
                products_by_id=products,
                branch_catalog_items_by_product_id=branch_catalog_by_product_id,
            )
        except ValueError as error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

        if validate_stock:
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

        automatic_evaluation = await self._select_best_automatic_campaign(
            tenant_id=tenant_id,
            draft=draft,
            products=products,
        )
        automatic_line_discounts = automatic_evaluation.line_allocations if automatic_evaluation is not None else [0.0] * len(draft.lines)
        automatic_discount_total = money(sum(automatic_line_discounts))

        post_automatic_line_subtotals = [
            money(line.line_subtotal - automatic_line_discounts[index])
            for index, line in enumerate(draft.lines)
        ]
        post_automatic_subtotal = money(sum(post_automatic_line_subtotals))

        promotion_code_campaign = None
        promotion_code_discount_total = 0.0
        promotion_code_line_discounts = [0.0] * len(draft.lines)
        customer_voucher = None
        customer_voucher_discount_total = 0.0
        customer_voucher_line_discounts = [0.0] * len(draft.lines)
        if promotion_code and customer_voucher_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Shared promotion codes and customer vouchers cannot be combined",
            )
        if promotion_code:
            validated = await self._promotion_service.validate_promotion_code(
                tenant_id=tenant_id,
                promotion_code=promotion_code,
                sale_total=post_automatic_subtotal,
            )
            promotion_code_campaign = {
                **self._promotion_service.serialize_campaign_snapshot(validated["campaign"]),
                "code_id": validated["code"].id,
                "code": validated["code"].code,
            }
            promotion_code_discount_total = money(float(validated["discount_amount"]))
            promotion_code_line_discounts = self._allocate_discount(
                total_discount=promotion_code_discount_total,
                weights=post_automatic_line_subtotals,
            )
        elif customer_voucher_id:
            if customer_profile_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Customer profile is required for customer vouchers",
                )
            validated = await self._promotion_service.validate_customer_voucher(
                tenant_id=tenant_id,
                customer_profile_id=customer_profile_id,
                voucher_id=customer_voucher_id,
                sale_total=post_automatic_subtotal,
            )
            customer_voucher = self._promotion_service.serialize_customer_voucher_snapshot(validated["voucher"])
            customer_voucher_discount_total = money(float(validated["discount_amount"]))
            customer_voucher_line_discounts = self._allocate_discount(
                total_discount=customer_voucher_discount_total,
                weights=post_automatic_line_subtotals,
            )

        is_inter_state = any(tax_line.tax_type == "IGST" for tax_line in draft.tax_lines)
        preview_lines: list[dict[str, object]] = []
        tax_groups: dict[tuple[str, float], dict[str, float]] = {}
        mrp_total = 0.0
        selling_price_subtotal = 0.0
        tax_total = 0.0
        invoice_total = 0.0

        for index, line in enumerate(draft.lines):
            product = products[line.product_id]
            automatic_discount_amount = money(automatic_line_discounts[index])
            promotion_code_discount_amount = money(promotion_code_line_discounts[index])
            customer_voucher_discount_amount = money(customer_voucher_line_discounts[index])
            taxable_amount = money(
                line.line_subtotal
                - automatic_discount_amount
                - promotion_code_discount_amount
                - customer_voucher_discount_amount
            )
            tax_amount = money(taxable_amount * line.gst_rate / 100)
            line_total = money(taxable_amount + tax_amount)
            mrp = money(float(product.mrp) * line.quantity)
            mrp_total = money(mrp_total + mrp)
            selling_price_subtotal = money(selling_price_subtotal + line.line_subtotal)
            tax_total = money(tax_total + tax_amount)
            invoice_total = money(invoice_total + line_total)

            source_segments: list[str] = []
            if automatic_discount_amount > 0:
                source_segments.append(automatic_evaluation.scope_label if automatic_evaluation is not None else "AUTOMATIC")
            if promotion_code_discount_amount > 0:
                source_segments.append("CODE")
            if customer_voucher_discount_amount > 0:
                source_segments.append("ASSIGNED_VOUCHER")
            promotion_discount_source = "+".join(source_segments) if source_segments else None

            preview_lines.append(
                {
                    "product_id": line.product_id,
                    "product_name": line.product_name,
                    "sku_code": line.sku_code,
                    "hsn_sac_code": line.hsn_sac_code,
                    "quantity": line.quantity,
                    "mrp": mrp,
                    "unit_selling_price": line.unit_price,
                    "unit_price": line.unit_price,
                    "gst_rate": line.gst_rate,
                    "automatic_discount_amount": automatic_discount_amount,
                    "promotion_code_discount_amount": promotion_code_discount_amount,
                    "customer_voucher_discount_amount": (
                        customer_voucher_discount_amount if customer_voucher_discount_amount > 0 else None
                    ),
                    "promotion_discount_source": promotion_discount_source,
                    "taxable_amount": taxable_amount,
                    "tax_amount": tax_amount,
                    "line_subtotal": line.line_subtotal,
                    "tax_total": tax_amount,
                    "line_total": line_total,
                }
            )

            self._accumulate_tax_group(
                tax_groups=tax_groups,
                is_inter_state=is_inter_state,
                gst_rate=line.gst_rate,
                taxable_amount=taxable_amount,
                tax_amount=tax_amount,
            )

        tax_lines = [
            {
                "tax_type": tax_type,
                "tax_rate": tax_rate,
                "taxable_amount": money(group["taxable_amount"]),
                "tax_amount": money(group["tax_amount"]),
            }
            for (tax_type, tax_rate), group in sorted(tax_groups.items(), key=lambda item: (item[0][0], item[0][1]))
        ]

        loyalty_points_to_redeem = int(loyalty_points_to_redeem or 0)
        loyalty_points_redeemed = 0
        loyalty_discount_total = 0.0
        if loyalty_points_to_redeem > 0:
            if customer_profile_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Customer profile is required for loyalty redemption",
                )
            loyalty_redemption = await self._loyalty_service.calculate_sale_redemption(
                tenant_id=tenant_id,
                customer_profile_id=customer_profile_id,
                points_to_redeem=loyalty_points_to_redeem,
                sale_total=invoice_total,
            )
            loyalty_points_redeemed = int(loyalty_redemption["points_to_redeem"])
            loyalty_discount_total = money(float(loyalty_redemption["discount_amount"]))

        grand_total = money(invoice_total - loyalty_discount_total)
        store_credit_amount = money(float(store_credit_amount or 0.0))
        if store_credit_amount > 0:
            if customer_profile_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Customer profile is required for store credit redemption",
                )
            if store_credit_amount > grand_total:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Store credit redemption cannot exceed sale total",
                )
            credit_summary = await self._store_credit_service.get_customer_store_credit(
                tenant_id=tenant_id,
                customer_profile_id=customer_profile_id,
            )
            if store_credit_amount > float(credit_summary["available_balance"]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Customer store credit balance is insufficient",
                )

        loyalty_points_earned = 0
        if customer_profile_id is not None:
            loyalty_points_earned = await self._loyalty_service.calculate_sale_earn_points(
                tenant_id=tenant_id,
                eligible_sale_amount=grand_total,
            )

        automatic_campaign = None
        if automatic_evaluation is not None:
            automatic_campaign = self._promotion_service.serialize_campaign_snapshot(automatic_evaluation.campaign)

        return {
            "customer_profile_id": customer_profile_id,
            "customer_name": draft.customer_name,
            "customer_gstin": draft.customer_gstin,
            "promotion_code": promotion_code_campaign["code"] if promotion_code_campaign is not None else None,
            "invoice_kind": draft.invoice_kind,
            "irn_status": draft.irn_status,
            "automatic_campaign": automatic_campaign,
            "promotion_code_campaign": promotion_code_campaign,
            "customer_voucher": customer_voucher,
            "summary": {
                "mrp_total": mrp_total,
                "selling_price_subtotal": selling_price_subtotal,
                "automatic_discount_total": automatic_discount_total,
                "promotion_code_discount_total": promotion_code_discount_total,
                "customer_voucher_discount_total": customer_voucher_discount_total,
                "loyalty_discount_total": loyalty_discount_total,
                "total_discount": money(
                    automatic_discount_total
                    + promotion_code_discount_total
                    + customer_voucher_discount_total
                    + loyalty_discount_total
                ),
                "tax_total": tax_total,
                "invoice_total": invoice_total,
                "grand_total": grand_total,
                "store_credit_amount": store_credit_amount,
                "final_payable_amount": money(grand_total - store_credit_amount),
            },
            "lines": preview_lines,
            "tax_lines": tax_lines,
            "loyalty_points_to_redeem": loyalty_points_redeemed,
            "loyalty_points_earned": loyalty_points_earned,
        }

    async def describe_scan_automatic_discount_hint(
        self,
        *,
        tenant_id: str,
        product_id: str,
        category_code: str | None,
        unit_selling_price: float,
    ) -> dict[str, object] | None:
        campaigns = await self._promotion_service.list_active_automatic_campaigns(tenant_id=tenant_id)
        best_campaign = None
        best_discount = 0.0
        for campaign in campaigns:
            if campaign.scope != "ITEM_CATEGORY":
                continue
            if not self._campaign_targets_product(
                campaign=campaign,
                product_id=product_id,
                category_code=category_code,
            ):
                continue
            if campaign.minimum_order_amount is not None and money(unit_selling_price) < money(float(campaign.minimum_order_amount)):
                continue
            discount_amount = self._discount_amount_for_total(
                discount_type=campaign.discount_type,
                discount_value=float(campaign.discount_value),
                maximum_discount_amount=campaign.maximum_discount_amount,
                base_total=money(unit_selling_price),
            )
            if discount_amount > best_discount:
                best_campaign = campaign
                best_discount = discount_amount
        if best_campaign is None:
            return None
        return {
            "campaign_name": best_campaign.name,
            "discount_type": best_campaign.discount_type,
            "discount_value": float(best_campaign.discount_value),
            "scope": best_campaign.scope,
        }

    async def _select_best_automatic_campaign(self, *, tenant_id: str, draft, products: dict[str, object]) -> _AutomaticCampaignEvaluation | None:
        campaigns = await self._promotion_service.list_active_automatic_campaigns(tenant_id=tenant_id)
        best_evaluation: _AutomaticCampaignEvaluation | None = None
        best_discount = 0.0
        for campaign in campaigns:
            evaluation = self._evaluate_automatic_campaign(
                campaign=campaign,
                draft=draft,
                products=products,
            )
            if evaluation is None:
                continue
            if evaluation.discount_total > best_discount:
                best_evaluation = evaluation
                best_discount = evaluation.discount_total
        return best_evaluation

    def _evaluate_automatic_campaign(self, *, campaign, draft, products: dict[str, object]) -> _AutomaticCampaignEvaluation | None:
        cart_subtotal = money(sum(line.line_subtotal for line in draft.lines))
        if campaign.minimum_order_amount is not None and cart_subtotal < money(float(campaign.minimum_order_amount)):
            return None

        eligible_indexes: list[int] = []
        scope_label = "AUTOMATIC_CART"
        for index, line in enumerate(draft.lines):
            if campaign.scope == "CART":
                eligible_indexes.append(index)
                continue
            product = products[line.product_id]
            if self._campaign_targets_product(
                campaign=campaign,
                product_id=line.product_id,
                category_code=product.category_code,
            ):
                eligible_indexes.append(index)
        if not eligible_indexes:
            return None
        if campaign.scope == "ITEM_CATEGORY":
            scope_label = "AUTOMATIC_ITEM_CATEGORY"

        weights = [draft.lines[index].line_subtotal for index in eligible_indexes]
        eligible_subtotal = money(sum(weights))
        discount_total = self._discount_amount_for_total(
            discount_type=campaign.discount_type,
            discount_value=float(campaign.discount_value),
            maximum_discount_amount=campaign.maximum_discount_amount,
            base_total=eligible_subtotal,
        )
        if discount_total <= 0:
            return None

        allocations = [0.0] * len(draft.lines)
        eligible_allocations = self._allocate_discount(total_discount=discount_total, weights=weights)
        for index, allocation in zip(eligible_indexes, eligible_allocations, strict=False):
            allocations[index] = allocation
        return _AutomaticCampaignEvaluation(
            campaign=campaign,
            scope_label=scope_label,
            discount_total=money(sum(allocations)),
            line_allocations=allocations,
        )

    @staticmethod
    def _campaign_targets_product(*, campaign, product_id: str, category_code: str | None) -> bool:
        target_product_ids = list(campaign.target_product_ids or [])
        target_category_codes = [code.upper() for code in list(campaign.target_category_codes or [])]
        normalized_category_code = category_code.upper() if category_code else None
        return product_id in target_product_ids or (
            normalized_category_code is not None and normalized_category_code in target_category_codes
        )

    @staticmethod
    def _discount_amount_for_total(
        *,
        discount_type: str,
        discount_value: float,
        maximum_discount_amount: float | None,
        base_total: float,
    ) -> float:
        if base_total <= 0:
            return 0.0
        if discount_type == "FLAT_AMOUNT":
            discount_amount = discount_value
        else:
            discount_amount = money(base_total * discount_value / 100.0)
            if maximum_discount_amount is not None:
                discount_amount = min(discount_amount, money(float(maximum_discount_amount)))
        return min(money(discount_amount), money(base_total))

    @staticmethod
    def _allocate_discount(*, total_discount: float, weights: list[float]) -> list[float]:
        total_discount = money(total_discount)
        if total_discount <= 0 or not weights:
            return [0.0] * len(weights)
        positive_indexes = [index for index, weight in enumerate(weights) if money(weight) > 0]
        if not positive_indexes:
            return [0.0] * len(weights)

        allocations = [0.0] * len(weights)
        total_weight = money(sum(money(weights[index]) for index in positive_indexes))
        remaining_discount = total_discount
        remaining_weight = total_weight
        for position, index in enumerate(positive_indexes):
            weight = money(weights[index])
            if position == len(positive_indexes) - 1 or remaining_weight <= 0:
                allocation = remaining_discount
            else:
                allocation = money(total_discount * weight / total_weight)
                allocation = min(allocation, weight, remaining_discount)
            allocations[index] = money(allocation)
            remaining_discount = money(remaining_discount - allocations[index])
            remaining_weight = money(remaining_weight - weight)
        return allocations

    @staticmethod
    def _accumulate_tax_group(
        *,
        tax_groups: dict[tuple[str, float], dict[str, float]],
        is_inter_state: bool,
        gst_rate: float,
        taxable_amount: float,
        tax_amount: float,
    ) -> None:
        if is_inter_state:
            key = ("IGST", gst_rate)
            group = tax_groups.setdefault(key, {"taxable_amount": 0.0, "tax_amount": 0.0})
            group["taxable_amount"] = money(group["taxable_amount"] + taxable_amount)
            group["tax_amount"] = money(group["tax_amount"] + tax_amount)
            return

        split_rate = money(gst_rate / 2)
        cgst_amount = money(tax_amount / 2)
        sgst_amount = money(tax_amount - cgst_amount)
        for tax_type, amount in (("CGST", cgst_amount), ("SGST", sgst_amount)):
            key = (tax_type, split_rate)
            group = tax_groups.setdefault(key, {"taxable_amount": 0.0, "tax_amount": 0.0})
            group["taxable_amount"] = money(group["taxable_amount"] + taxable_amount)
            group["tax_amount"] = money(group["tax_amount"] + amount)
