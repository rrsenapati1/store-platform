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
        handoff_surface: str | None,
        provider_payment_mode: str | None,
        customer_name: str,
        customer_gstin: str | None,
        lines: list[dict[str, object]],
    ) -> dict[str, object]:
        (
            resolved_handoff_surface,
            resolved_provider_payment_mode,
        ) = self._resolve_checkout_configuration(
            payment_method=payment_method,
            handoff_surface=handoff_surface,
            provider_payment_mode=provider_payment_mode,
        )
        draft, cart_snapshot = await self._build_checkout_sale_draft(
            tenant_id=tenant_id,
            branch_id=branch_id,
            customer_name=customer_name,
            customer_gstin=customer_gstin,
            lines=lines,
        )
        record = await self._create_payment_session_record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            provider_name=provider_name,
            payment_method=payment_method,
            handoff_surface=resolved_handoff_surface,
            provider_payment_mode=resolved_provider_payment_mode,
            customer_name=customer_name,
            customer_gstin=customer_gstin,
            lines=lines,
            draft=draft,
            cart_snapshot=cart_snapshot,
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="checkout_payment_session.created",
            entity_type="checkout_payment_session",
            entity_id=record.id,
            payload={
                "provider_name": provider_name,
                "payment_method": payment_method,
                "handoff_surface": resolved_handoff_surface,
                "provider_payment_mode": resolved_provider_payment_mode,
                "order_amount": record.order_amount,
            },
        )
        await self._session.commit()
        return self._serialize_checkout_payment_session(record, sale=None)

    async def list_checkout_payment_sessions(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        limit: int = 10,
    ) -> list[dict[str, object]]:
        records = await self._billing_repo.list_checkout_payment_sessions(
            tenant_id=tenant_id,
            branch_id=branch_id,
            limit=limit,
        )
        serialized_records: list[dict[str, object]] = []
        for record in records:
            serialized_records.append(
                self._serialize_checkout_payment_session(
                    record,
                    sale=await self._load_sale_for_record(record),
                )
            )
        return serialized_records

    async def get_checkout_payment_session(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        checkout_payment_session_id: str,
    ) -> dict[str, object]:
        record = await self._require_checkout_payment_session(
            tenant_id=tenant_id,
            branch_id=branch_id,
            checkout_payment_session_id=checkout_payment_session_id,
        )
        sale = await self._load_sale_for_record(record)
        return self._serialize_checkout_payment_session(record, sale=sale)

    async def refresh_checkout_payment_session(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        checkout_payment_session_id: str,
        actor_user_id: str,
    ) -> dict[str, object]:
        record = await self._require_checkout_payment_session(
            tenant_id=tenant_id,
            branch_id=branch_id,
            checkout_payment_session_id=checkout_payment_session_id,
        )
        provider = build_checkout_payment_provider(record.provider_name, self._settings)
        payments = await provider.fetch_order_payments(provider_order_id=record.provider_order_id)
        normalized = provider.normalize_polled_payments(
            provider_order_id=record.provider_order_id,
            payload=payments,
        )
        sale = await self._apply_provider_event(record, normalized, actor_user_id=actor_user_id)
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="checkout_payment_session.refreshed",
            entity_type="checkout_payment_session",
            entity_id=record.id,
            payload={"provider_status": record.provider_status, "lifecycle_status": record.lifecycle_status},
        )
        await self._session.commit()
        return self._serialize_checkout_payment_session(record, sale=sale or await self._load_sale_for_record(record))

    async def finalize_checkout_payment_session(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        checkout_payment_session_id: str,
        actor_user_id: str,
    ) -> dict[str, object]:
        record = await self._require_checkout_payment_session(
            tenant_id=tenant_id,
            branch_id=branch_id,
            checkout_payment_session_id=checkout_payment_session_id,
        )
        if record.lifecycle_status not in {"CONFIRMED", "FINALIZED"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only confirmed checkout payment sessions can be finalized",
            )
        sale = await self._attempt_finalize_sale(record)
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="checkout_payment_session.finalize_requested",
            entity_type="checkout_payment_session",
            entity_id=record.id,
            payload={"lifecycle_status": record.lifecycle_status, "sale_id": record.finalized_sale_id},
        )
        await self._session.commit()
        return self._serialize_checkout_payment_session(record, sale=sale or await self._load_sale_for_record(record))

    async def retry_checkout_payment_session(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        checkout_payment_session_id: str,
        actor_user_id: str,
    ) -> dict[str, object]:
        record = await self._require_checkout_payment_session(
            tenant_id=tenant_id,
            branch_id=branch_id,
            checkout_payment_session_id=checkout_payment_session_id,
        )
        if self._recovery_state_for_record(record) != "RETRYABLE":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only failed, expired, or canceled checkout payment sessions can be retried",
            )
        lines = list(record.cart_snapshot.get("lines", []))
        next_session = await self.create_checkout_payment_session(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            provider_name=record.provider_name,
            payment_method=record.payment_method,
            handoff_surface=record.handoff_surface,
            provider_payment_mode=record.provider_payment_mode,
            customer_name=record.customer_name,
            customer_gstin=record.customer_gstin,
            lines=lines,
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="checkout_payment_session.retried",
            entity_type="checkout_payment_session",
            entity_id=record.id,
            payload={"replacement_checkout_payment_session_id": next_session["id"]},
        )
        await self._session.commit()
        return next_session

    async def cancel_checkout_payment_session(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        checkout_payment_session_id: str,
        actor_user_id: str,
    ) -> dict[str, object]:
        record = await self._require_checkout_payment_session(
            tenant_id=tenant_id,
            branch_id=branch_id,
            checkout_payment_session_id=checkout_payment_session_id,
        )
        if record.finalized_sale_id is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Finalized checkout payment sessions cannot be canceled")
        record.lifecycle_status = "CANCELED"
        record.provider_status = "CANCELED"
        record.canceled_at = utc_now()
        record.last_reconciled_at = utc_now()
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

        await self._apply_provider_event(record, normalized, actor_user_id=record.actor_user_id)
        await self._session.commit()
        return {"status": "ok", "checkout_payment_session_id": record.id, "lifecycle_status": record.lifecycle_status}

    async def _build_checkout_sale_draft(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        customer_name: str,
        customer_gstin: str | None,
        lines: list[dict[str, object]],
    ):
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
        return draft, cart_snapshot

    async def _create_payment_session_record(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        actor_user_id: str,
        provider_name: str,
        payment_method: str,
        handoff_surface: str,
        provider_payment_mode: str,
        customer_name: str,
        customer_gstin: str | None,
        lines: list[dict[str, object]],
        draft,
        cart_snapshot: dict[str, object],
    ):
        cart_summary_hash = hashlib.sha256(json.dumps(cart_snapshot, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        checkout_payment_session_id = new_id()
        provider = build_checkout_payment_provider(provider_name, self._settings)
        provider_result = await provider.create_checkout_payment(
            checkout_payment_session_id=checkout_payment_session_id,
            handoff_surface=handoff_surface,
            provider_payment_mode=provider_payment_mode,
            order_amount=draft.grand_total,
            currency_code="INR",
            customer_name=customer_name,
            customer_gstin=customer_gstin,
        )
        return await self._billing_repo.create_checkout_payment_session(
            session_id=checkout_payment_session_id,
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            provider_name=provider_name,
            provider_order_id=provider_result.provider_order_id,
            provider_payment_session_id=provider_result.provider_payment_session_id,
            payment_method=payment_method,
            handoff_surface=handoff_surface,
            provider_payment_mode=provider_payment_mode,
            lifecycle_status="ACTION_READY",
            provider_status=provider_result.provider_status,
            order_amount=draft.grand_total,
            currency_code="INR",
            cart_summary_hash=cart_summary_hash,
            cart_snapshot=cart_snapshot,
            customer_name=customer_name,
            customer_gstin=customer_gstin,
            action_payload=provider_result.action_payload,
            action_expires_at=provider_result.action_expires_at,
            qr_payload=provider_result.qr_payload or {},
            qr_expires_at=provider_result.qr_expires_at,
            provider_response_payload=provider_result.provider_response_payload,
        )

    async def _apply_provider_event(self, record, normalized_event, *, actor_user_id: str | None):
        record.provider_payment_id = normalized_event.provider_payment_id
        record.provider_status = normalized_event.provider_status
        record.provider_response_payload = normalized_event.payload
        record.last_reconciled_at = utc_now()

        if normalized_event.lifecycle_status == "CONFIRMED":
            if record.confirmed_at is None:
                record.confirmed_at = utc_now()
            record.lifecycle_status = "CONFIRMED"
            return await self._attempt_finalize_sale(record)

        if normalized_event.lifecycle_status == "FAILED":
            record.lifecycle_status = "FAILED"
            record.failed_at = utc_now()
            record.last_error_message = f"Cashfree reported {record.provider_status}"
            return None

        if normalized_event.lifecycle_status == "EXPIRED":
            record.lifecycle_status = "EXPIRED"
            record.expired_at = utc_now()
            record.last_error_message = f"Cashfree reported {record.provider_status}"
            return None

        if record.lifecycle_status == "ACTION_READY":
            record.lifecycle_status = "PENDING_CUSTOMER_PAYMENT"
        else:
            record.lifecycle_status = normalized_event.lifecycle_status
        record.last_error_message = None
        return None

    async def _attempt_finalize_sale(self, record):
        if record.finalized_sale_id:
            record.lifecycle_status = "FINALIZED"
            record.last_error_message = None
            return await self._load_sale_for_record(record)

        try:
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
        except HTTPException as error:
            record.lifecycle_status = "CONFIRMED"
            detail = error.detail if isinstance(error.detail, str) else "Unable to finalize confirmed checkout payment session"
            record.last_error_message = detail
            return None
        except Exception as error:  # pragma: no cover - defensive guard for provider reconciliation
            record.lifecycle_status = "CONFIRMED"
            record.last_error_message = str(error)
            return None

        record.finalized_sale_id = str(sale["id"])
        record.finalized_at = utc_now()
        record.lifecycle_status = "FINALIZED"
        record.last_error_message = None
        return sale

    async def _require_checkout_payment_session(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        checkout_payment_session_id: str,
    ):
        record = await self._billing_repo.get_checkout_payment_session(
            tenant_id=tenant_id,
            branch_id=branch_id,
            checkout_payment_session_id=checkout_payment_session_id,
        )
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Checkout payment session not found")
        return record

    async def _load_sale_for_record(self, record):
        if not record.finalized_sale_id:
            return None
        return await self._billing_service.get_sale(
            tenant_id=record.tenant_id,
            branch_id=record.branch_id,
            sale_id=record.finalized_sale_id,
        )

    def _resolve_checkout_configuration(
        self,
        *,
        payment_method: str,
        handoff_surface: str | None,
        provider_payment_mode: str | None,
    ) -> tuple[str, str]:
        normalized_payment_method = payment_method.strip().upper()
        inferred: dict[str, tuple[str, str]] = {
            "CASHFREE_UPI_QR": ("BRANDED_UPI_QR", "cashfree_upi"),
            "CASHFREE_HOSTED_TERMINAL": ("HOSTED_TERMINAL", "cashfree_checkout"),
            "CASHFREE_HOSTED_PHONE": ("HOSTED_PHONE", "cashfree_checkout"),
        }
        if normalized_payment_method not in inferred:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported checkout payment method: {payment_method}")
        default_handoff_surface, default_provider_payment_mode = inferred[normalized_payment_method]
        resolved_handoff_surface = (handoff_surface or default_handoff_surface).strip().upper()
        resolved_provider_payment_mode = (provider_payment_mode or default_provider_payment_mode).strip()
        return resolved_handoff_surface, resolved_provider_payment_mode

    @staticmethod
    def _recovery_state_for_record(record) -> str:
        if record.finalized_sale_id or record.lifecycle_status == "FINALIZED":
            return "CLOSED"
        if record.lifecycle_status == "CONFIRMED":
            return "FINALIZE_REQUIRED"
        if record.lifecycle_status in {"FAILED", "EXPIRED", "CANCELED"}:
            return "RETRYABLE"
        return "ACTIVE"

    def _serialize_checkout_payment_session(self, record, *, sale: dict[str, object] | None) -> dict[str, object]:
        qr_payload = record.qr_payload or None
        return {
            "id": record.id,
            "tenant_id": record.tenant_id,
            "branch_id": record.branch_id,
            "provider_name": record.provider_name,
            "provider_order_id": record.provider_order_id,
            "provider_payment_session_id": record.provider_payment_session_id,
            "provider_payment_id": record.provider_payment_id,
            "payment_method": record.payment_method,
            "handoff_surface": record.handoff_surface,
            "provider_payment_mode": record.provider_payment_mode,
            "lifecycle_status": record.lifecycle_status,
            "provider_status": record.provider_status,
            "order_amount": record.order_amount,
            "currency_code": record.currency_code,
            "action_payload": record.action_payload,
            "action_expires_at": record.action_expires_at,
            "qr_payload": qr_payload,
            "qr_expires_at": record.qr_expires_at,
            "last_error_message": record.last_error_message,
            "last_reconciled_at": record.last_reconciled_at,
            "recovery_state": self._recovery_state_for_record(record),
            "sale": sale,
        }
