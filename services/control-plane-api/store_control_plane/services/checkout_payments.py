from __future__ import annotations

import hashlib
import json

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import Settings
from ..repositories import AuditRepository, BillingRepository, CatalogRepository, InventoryRepository, TenantRepository
from ..utils import new_id, utc_now
from .billing import BillingService
from .checkout_pricing import CheckoutPricingService
from .checkout_payment_providers import build_checkout_payment_provider
from .customer_profiles import CustomerProfileService
from .loyalty import LoyaltyService
from .promotions import PromotionService


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
        self._checkout_pricing_service = CheckoutPricingService(session)
        self._customer_profile_service = CustomerProfileService(session)
        self._loyalty_service = LoyaltyService(session)
        self._promotion_service = PromotionService(session)

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
        customer_profile_id: str | None,
        customer_name: str,
        customer_gstin: str | None,
        promotion_code: str | None,
        loyalty_points_to_redeem: int,
        store_credit_amount: float,
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
        pricing_preview = await self._build_checkout_pricing_preview(
            tenant_id=tenant_id,
            branch_id=branch_id,
            customer_profile_id=customer_profile_id,
            customer_name=customer_name,
            customer_gstin=customer_gstin,
            promotion_code=promotion_code,
            loyalty_points_to_redeem=loyalty_points_to_redeem,
            store_credit_amount=store_credit_amount,
            lines=lines,
        )
        record = await self._create_payment_session_record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            customer_profile_id=customer_profile_id,
            provider_name=provider_name,
            payment_method=payment_method,
            handoff_surface=resolved_handoff_surface,
            provider_payment_mode=resolved_provider_payment_mode,
            customer_name=str(pricing_preview["customer_name"]),
            customer_gstin=pricing_preview.get("customer_gstin"),
            lines=lines,
            pricing_preview=pricing_preview,
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
                "automatic_discount_total": pricing_preview["summary"]["automatic_discount_total"],
                "promotion_code_discount_total": pricing_preview["summary"]["promotion_code_discount_total"],
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
        lines = list(record.cart_snapshot.get("requested_lines", []))
        next_session = await self.create_checkout_payment_session(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            provider_name=record.provider_name,
            payment_method=record.payment_method,
            handoff_surface=record.handoff_surface,
            provider_payment_mode=record.provider_payment_mode,
            customer_profile_id=record.customer_profile_id,
            customer_name=record.customer_name,
            customer_gstin=record.customer_gstin,
            promotion_code=record.cart_snapshot.get("promotion_code"),
            loyalty_points_to_redeem=int(record.cart_snapshot.get("loyalty_points_to_redeem", 0)),
            store_credit_amount=float(record.cart_snapshot.get("summary", {}).get("store_credit_amount", 0.0)),
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

    async def _build_checkout_pricing_preview(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        customer_profile_id: str | None,
        customer_name: str,
        customer_gstin: str | None,
        promotion_code: str | None,
        loyalty_points_to_redeem: int,
        store_credit_amount: float,
        lines: list[dict[str, object]],
    ) -> dict[str, object]:
        preview = await self._checkout_pricing_service.build_preview(
            tenant_id=tenant_id,
            branch_id=branch_id,
            customer_profile_id=customer_profile_id,
            customer_name=customer_name,
            customer_gstin=customer_gstin,
            promotion_code=promotion_code,
            loyalty_points_to_redeem=loyalty_points_to_redeem,
            store_credit_amount=store_credit_amount,
            lines=lines,
            validate_stock=True,
        )
        return {
            **preview,
            "requested_lines": [{"product_id": str(line["product_id"]), "quantity": float(line["quantity"])} for line in lines],
        }

    async def _create_payment_session_record(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        actor_user_id: str,
        customer_profile_id: str | None,
        provider_name: str,
        payment_method: str,
        handoff_surface: str,
        provider_payment_mode: str,
        customer_name: str,
        customer_gstin: str | None,
        lines: list[dict[str, object]],
        pricing_preview: dict[str, object],
    ):
        cart_summary_hash = hashlib.sha256(json.dumps(pricing_preview, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        checkout_payment_session_id = new_id()
        provider = build_checkout_payment_provider(provider_name, self._settings)
        provider_result = await provider.create_checkout_payment(
            checkout_payment_session_id=checkout_payment_session_id,
            handoff_surface=handoff_surface,
            provider_payment_mode=provider_payment_mode,
            order_amount=float(pricing_preview["summary"]["final_payable_amount"]),
            currency_code="INR",
            customer_name=customer_name,
            customer_gstin=customer_gstin,
        )
        return await self._billing_repo.create_checkout_payment_session(
            session_id=checkout_payment_session_id,
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            customer_profile_id=customer_profile_id,
            provider_name=provider_name,
            provider_order_id=provider_result.provider_order_id,
            provider_payment_session_id=provider_result.provider_payment_session_id,
            payment_method=payment_method,
            handoff_surface=handoff_surface,
            provider_payment_mode=provider_payment_mode,
            lifecycle_status="ACTION_READY",
            provider_status=provider_result.provider_status,
            order_amount=float(pricing_preview["summary"]["final_payable_amount"]),
            currency_code="INR",
            cart_summary_hash=cart_summary_hash,
            cart_snapshot=pricing_preview,
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
                customer_profile_id=record.customer_profile_id,
                customer_name=record.customer_name,
                customer_gstin=record.customer_gstin,
                payment_method=record.payment_method,
                pricing_snapshot=dict(record.cart_snapshot),
                store_credit_amount=float(record.cart_snapshot.get("summary", {}).get("store_credit_amount", 0.0)),
                loyalty_points_to_redeem=int(record.cart_snapshot.get("loyalty_points_to_redeem", 0)),
                lines=list(record.cart_snapshot.get("requested_lines", [])),
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
            "customer_profile_id": record.customer_profile_id,
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
            "automatic_campaign_name": record.cart_snapshot.get("automatic_campaign", {}).get("name")
            if record.cart_snapshot.get("automatic_campaign")
            else None,
            "automatic_discount_total": float(record.cart_snapshot.get("summary", {}).get("automatic_discount_total", 0.0)),
            "promotion_code": record.cart_snapshot.get("promotion_code"),
            "promotion_discount_amount": float(record.cart_snapshot.get("summary", {}).get("promotion_code_discount_total", 0.0)),
            "promotion_code_discount_total": float(record.cart_snapshot.get("summary", {}).get("promotion_code_discount_total", 0.0)),
            "store_credit_amount": float(record.cart_snapshot.get("summary", {}).get("store_credit_amount", 0.0)),
            "action_payload": record.action_payload,
            "action_expires_at": record.action_expires_at,
            "qr_payload": qr_payload,
            "qr_expires_at": record.qr_expires_at,
            "last_error_message": record.last_error_message,
            "last_reconciled_at": record.last_reconciled_at,
            "recovery_state": self._recovery_state_for_record(record),
            "sale": sale,
        }
