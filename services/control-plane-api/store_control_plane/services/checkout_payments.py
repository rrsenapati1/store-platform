from __future__ import annotations

import hashlib
import json

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import Settings
from ..repositories import AuditRepository, BillingRepository, CatalogRepository, InventoryRepository, TenantRepository
from ..utils import new_id, utc_now
from .billing import BillingService
from .billing_policy import build_sale_draft, ensure_sale_stock_available
from .checkout_payment_providers import build_checkout_payment_provider


class CheckoutPaymentsService:
    def __init__(self, session: AsyncSession, settings: Settings):
        self._session = session
        self._settings = settings
        self._tenant_repo = TenantRepository(session)
        self._catalog_repo = CatalogRepository(session)
        self._inventory_repo = InventoryRepository(session)
        self._billing_repo = BillingRepository(session)
        self._audit_repo = AuditRepository(session)
        self._billing_service = BillingService(session)

    async def create_checkout_payment_session(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        actor_user_id: str,
        provider_name: str,
        payment_method: str,
        customer_name: str,
        customer_gstin: str | None,
        lines: list[dict[str, object]],
    ) -> dict[str, object]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
        if branch.gstin is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Branch GSTIN is required for billing")

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

        cart_snapshot = {
            "customer_name": draft.customer_name,
            "customer_gstin": draft.customer_gstin,
            "lines": [{"product_id": line.product_id, "quantity": line.quantity} for line in draft.lines],
            "totals": {
                "subtotal": draft.subtotal,
                "cgst_total": draft.cgst_total,
                "sgst_total": draft.sgst_total,
                "igst_total": draft.igst_total,
                "grand_total": draft.grand_total,
            },
        }
        cart_summary_hash = hashlib.sha256(json.dumps(cart_snapshot, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        checkout_payment_session_id = new_id()
        provider = build_checkout_payment_provider(provider_name, self._settings)
        provider_result = await provider.create_checkout_payment(
            checkout_payment_session_id=checkout_payment_session_id,
            order_amount=draft.grand_total,
            currency_code="INR",
            customer_name=customer_name,
            customer_gstin=customer_gstin,
        )
        record = await self._billing_repo.create_checkout_payment_session(
            session_id=checkout_payment_session_id,
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            provider_name=provider_name,
            provider_order_id=provider_result.provider_order_id,
            provider_payment_session_id=provider_result.provider_payment_session_id,
            payment_method=payment_method,
            lifecycle_status="QR_READY",
            provider_status=provider_result.provider_status,
            order_amount=draft.grand_total,
            currency_code="INR",
            cart_summary_hash=cart_summary_hash,
            cart_snapshot=cart_snapshot,
            customer_name=customer_name,
            customer_gstin=customer_gstin,
            qr_payload=provider_result.qr_payload,
            qr_expires_at=provider_result.qr_expires_at,
            provider_response_payload=provider_result.provider_response_payload,
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="checkout_payment_session.created",
            entity_type="checkout_payment_session",
            entity_id=record.id,
            payload={"provider_name": provider_name, "payment_method": payment_method, "order_amount": record.order_amount},
        )
        await self._session.commit()
        return self._serialize_checkout_payment_session(record, sale=None)

    async def get_checkout_payment_session(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        checkout_payment_session_id: str,
    ) -> dict[str, object]:
        record = await self._billing_repo.get_checkout_payment_session(
            tenant_id=tenant_id,
            branch_id=branch_id,
            checkout_payment_session_id=checkout_payment_session_id,
        )
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Checkout payment session not found")
        sale = None
        if record.finalized_sale_id:
            sale = await self._billing_service.get_sale(tenant_id=tenant_id, branch_id=branch_id, sale_id=record.finalized_sale_id)
        return self._serialize_checkout_payment_session(record, sale=sale)

    async def cancel_checkout_payment_session(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        checkout_payment_session_id: str,
        actor_user_id: str,
    ) -> dict[str, object]:
        record = await self._billing_repo.get_checkout_payment_session(
            tenant_id=tenant_id,
            branch_id=branch_id,
            checkout_payment_session_id=checkout_payment_session_id,
        )
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Checkout payment session not found")
        if record.finalized_sale_id is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Finalized checkout payment sessions cannot be canceled")
        record.lifecycle_status = "CANCELED"
        record.provider_status = "CANCELED"
        record.canceled_at = utc_now()
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="checkout_payment_session.canceled",
            entity_type="checkout_payment_session",
            entity_id=record.id,
            payload={"provider_name": record.provider_name},
        )
        await self._session.commit()
        return self._serialize_checkout_payment_session(record, sale=None)

    async def handle_cashfree_webhook(
        self,
        *,
        raw_body: bytes,
        signature: str | None,
        timestamp: str | None,
    ) -> dict[str, object]:
        provider = build_checkout_payment_provider("cashfree", self._settings)
        if not provider.verify_webhook_signature(
            secret=self._settings.cashfree_payment_webhook_secret,
            raw_body=raw_body,
            signature=signature,
            timestamp=timestamp,
        ):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Cashfree payment webhook signature")

        payload = json.loads(raw_body.decode("utf-8"))
        normalized = provider.normalize_webhook_payload(payload)
        if not normalized.provider_order_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cashfree webhook missing provider order id")
        record = await self._billing_repo.get_checkout_payment_session_by_provider_order(
            provider_name="cashfree",
            provider_order_id=normalized.provider_order_id,
        )
        if record is None:
            return {"status": "ignored"}

        record.provider_payment_id = normalized.provider_payment_id
        record.provider_status = normalized.provider_status
        record.provider_response_payload = normalized.payload
        record.last_error_message = None

        if normalized.lifecycle_status == "CONFIRMED":
            if record.confirmed_at is None:
                record.confirmed_at = utc_now()
            if record.finalized_sale_id is None:
                sale = await self._billing_service.create_sale(
                    tenant_id=record.tenant_id,
                    branch_id=record.branch_id,
                    actor_user_id=record.actor_user_id,
                    customer_name=record.customer_name,
                    customer_gstin=record.customer_gstin,
                    payment_method=record.payment_method,
                    lines=list(record.cart_snapshot.get("lines", [])),
                    auto_commit=False,
                )
                record.finalized_sale_id = str(sale["id"])
                record.finalized_at = utc_now()
            record.lifecycle_status = "FINALIZED" if record.finalized_sale_id else "CONFIRMED"
        elif normalized.lifecycle_status == "FAILED":
            record.lifecycle_status = "FAILED"
            record.failed_at = utc_now()
        elif normalized.lifecycle_status == "EXPIRED":
            record.lifecycle_status = "EXPIRED"
            record.expired_at = utc_now()

        await self._session.commit()
        return {"status": "ok", "checkout_payment_session_id": record.id, "lifecycle_status": record.lifecycle_status}

    @staticmethod
    def _serialize_checkout_payment_session(record, *, sale: dict[str, object] | None) -> dict[str, object]:
        return {
            "id": record.id,
            "tenant_id": record.tenant_id,
            "branch_id": record.branch_id,
            "provider_name": record.provider_name,
            "provider_order_id": record.provider_order_id,
            "provider_payment_session_id": record.provider_payment_session_id,
            "provider_payment_id": record.provider_payment_id,
            "payment_method": record.payment_method,
            "lifecycle_status": record.lifecycle_status,
            "provider_status": record.provider_status,
            "order_amount": record.order_amount,
            "currency_code": record.currency_code,
            "qr_payload": record.qr_payload,
            "qr_expires_at": record.qr_expires_at,
            "sale": sale,
        }
