from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from datetime import datetime, timedelta
from urllib.parse import quote

import httpx

from ..config import Settings
from ..utils import utc_now


@dataclass(slots=True)
class CheckoutPaymentCreateResult:
    provider_order_id: str
    provider_payment_session_id: str | None
    provider_status: str
    qr_payload: dict[str, object]
    qr_expires_at: datetime | None
    provider_response_payload: dict[str, object]


@dataclass(slots=True)
class NormalizedCheckoutPaymentEvent:
    provider_name: str
    provider_order_id: str
    provider_payment_id: str | None
    provider_status: str
    lifecycle_status: str
    payload: dict[str, object]


class StubCashfreeCheckoutPaymentProvider:
    provider_name = "cashfree"

    async def create_checkout_payment(
        self,
        *,
        checkout_payment_session_id: str,
        order_amount: float,
        currency_code: str,
        customer_name: str,
        customer_gstin: str | None,
    ) -> CheckoutPaymentCreateResult:
        provider_order_id = f"cf_order_{checkout_payment_session_id}"
        provider_payment_session_id = f"cf_ps_{checkout_payment_session_id}"
        qr_payload = {
            "format": "upi_qr",
            "value": (
                "upi://pay"
                f"?pa={quote('store.collect@cashfree')}"
                f"&pn={quote('Store Checkout')}"
                f"&tr={quote(provider_order_id)}"
                f"&am={order_amount:.2f}"
                f"&cu={quote(currency_code)}"
                f"&tn={quote(customer_name or 'Store Checkout')}"
            ),
        }
        qr_expires_at = utc_now() + timedelta(minutes=10)
        return CheckoutPaymentCreateResult(
            provider_order_id=provider_order_id,
            provider_payment_session_id=provider_payment_session_id,
            provider_status="ACTIVE",
            qr_payload=qr_payload,
            qr_expires_at=qr_expires_at,
            provider_response_payload={
                "mode": "stub",
                "order_id": provider_order_id,
                "payment_session_id": provider_payment_session_id,
                "order_amount": order_amount,
                "currency_code": currency_code,
                "customer_name": customer_name,
                "customer_gstin": customer_gstin,
                "qr_payload": qr_payload,
                "qr_expires_at": qr_expires_at.isoformat(),
            },
        )

    async def fetch_order_payments(self, *, provider_order_id: str) -> list[dict[str, object]]:
        return [{"provider_order_id": provider_order_id, "mode": "stub"}]

    def verify_webhook_signature(self, *, secret: str | None, raw_body: bytes, signature: str | None, timestamp: str | None) -> bool:
        if not secret or not signature or not timestamp:
            return False
        computed = hmac.new(secret.encode("utf-8"), f"{timestamp}{raw_body.decode('utf-8')}".encode("utf-8"), hashlib.sha256)
        return hmac.compare_digest(computed.hexdigest(), signature)

    def normalize_webhook_payload(self, payload: dict[str, object]) -> NormalizedCheckoutPaymentEvent:
        data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
        order = data.get("order") if isinstance(data.get("order"), dict) else {}
        payment = data.get("payment") if isinstance(data.get("payment"), dict) else {}
        provider_status = str(payment.get("payment_status") or payload.get("type") or "PENDING").strip().upper()
        event_type = str(payload.get("type") or "").strip().upper()
        lifecycle_status = "PENDING_CUSTOMER_PAYMENT"
        if provider_status == "SUCCESS" or event_type == "PAYMENT_SUCCESS_WEBHOOK":
            lifecycle_status = "CONFIRMED"
        elif provider_status in {"FAILED", "CANCELLED"} or event_type == "PAYMENT_FAILED_WEBHOOK":
            lifecycle_status = "FAILED"
        elif provider_status in {"USER_DROPPED", "EXPIRED"} or event_type == "PAYMENT_USER_DROPPED_WEBHOOK":
            lifecycle_status = "EXPIRED"
        return NormalizedCheckoutPaymentEvent(
            provider_name="cashfree",
            provider_order_id=str(order.get("order_id") or ""),
            provider_payment_id=str(payment.get("cf_payment_id")) if payment.get("cf_payment_id") else None,
            provider_status=provider_status,
            lifecycle_status=lifecycle_status,
            payload=payload,
        )


class CashfreeCheckoutPaymentProvider(StubCashfreeCheckoutPaymentProvider):
    def __init__(self, settings: Settings):
        self._settings = settings

    async def create_checkout_payment(
        self,
        *,
        checkout_payment_session_id: str,
        order_amount: float,
        currency_code: str,
        customer_name: str,
        customer_gstin: str | None,
    ) -> CheckoutPaymentCreateResult:
        if not self._settings.cashfree_payment_client_id or not self._settings.cashfree_payment_client_secret:
            raise ValueError("Cashfree checkout credentials are not configured")

        provider_order_id = f"cf_order_{checkout_payment_session_id}"
        headers = {
            "x-client-id": self._settings.cashfree_payment_client_id,
            "x-client-secret": self._settings.cashfree_payment_client_secret,
            "x-api-version": self._settings.cashfree_payment_api_version,
            "content-type": "application/json",
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            order_response = await client.post(
                f"{self._settings.cashfree_payment_api_base_url}/pg/orders",
                headers=headers,
                json={
                    "order_id": provider_order_id,
                    "order_amount": round(order_amount, 2),
                    "order_currency": currency_code,
                    "customer_details": {
                        "customer_id": checkout_payment_session_id,
                        "customer_name": customer_name,
                        "customer_email": "not-provided@store.local",
                        "customer_phone": "9999999999",
                    },
                    "order_note": customer_gstin or customer_name,
                },
            )
            order_response.raise_for_status()
            order_payload = order_response.json()
            payment_session_id = str(order_payload.get("payment_session_id") or "")

            qr_response = await client.post(
                f"{self._settings.cashfree_payment_api_base_url}/pg/orders/sessions",
                headers=headers,
                json={
                    "payment_session_id": payment_session_id,
                    "payment_method": {"upi": {"channel": "qrcode"}},
                },
            )
            qr_response.raise_for_status()
            qr_payload = qr_response.json()

        qr_value = (
            qr_payload.get("data", {}).get("url")
            if isinstance(qr_payload.get("data"), dict)
            else None
        ) or (
            qr_payload.get("payment_method", {}).get("upi", {}).get("qr_code")
            if isinstance(qr_payload.get("payment_method"), dict)
            else None
        ) or (
            order_payload.get("payment_link")
            if isinstance(order_payload, dict)
            else None
        )
        qr_expires_at = utc_now() + timedelta(minutes=10)
        return CheckoutPaymentCreateResult(
            provider_order_id=provider_order_id,
            provider_payment_session_id=payment_session_id or None,
            provider_status="ACTIVE",
            qr_payload={"format": "upi_qr", "value": str(qr_value or "")},
            qr_expires_at=qr_expires_at,
            provider_response_payload={"order": order_payload, "qr": qr_payload},
        )

    async def fetch_order_payments(self, *, provider_order_id: str) -> list[dict[str, object]]:
        if not self._settings.cashfree_payment_client_id or not self._settings.cashfree_payment_client_secret:
            raise ValueError("Cashfree checkout credentials are not configured")
        headers = {
            "x-client-id": self._settings.cashfree_payment_client_id,
            "x-client-secret": self._settings.cashfree_payment_client_secret,
            "x-api-version": self._settings.cashfree_payment_api_version,
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{self._settings.cashfree_payment_api_base_url}/pg/orders/{provider_order_id}/payments",
                headers=headers,
            )
            response.raise_for_status()
            payload = response.json()
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict) and isinstance(payload.get("data"), list):
            return payload["data"]
        return []


def build_checkout_payment_provider(provider_name: str, settings: Settings) -> StubCashfreeCheckoutPaymentProvider:
    normalized_provider = provider_name.strip().lower()
    if normalized_provider != "cashfree":
        raise ValueError(f"Unsupported checkout payment provider: {provider_name}")
    if settings.checkout_payment_provider_mode == "cashfree":
        return CashfreeCheckoutPaymentProvider(settings)
    return StubCashfreeCheckoutPaymentProvider()
