from __future__ import annotations

from base64 import b64encode
from dataclasses import dataclass
from datetime import datetime, timedelta
import os
from typing import Any

import httpx
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding

from ..config import Settings
from .purchase_policy import normalize_gstin


@dataclass(slots=True)
class IrpBranchCredentials:
    branch_gstin: str
    api_username: str
    api_password: str


@dataclass(slots=True)
class IrpTaxpayerProfile:
    gstin: str
    legal_name: str
    trade_name: str
    address_line1: str
    address_line2: str
    location: str
    pincode: str
    state_code: str


@dataclass(slots=True)
class IrpSubmissionResult:
    outcome: str
    irn: str | None = None
    ack_no: str | None = None
    signed_qr_payload: str | None = None
    provider_status: str = "SUBMITTED"


class IrpActionRequiredError(Exception):
    def __init__(self, *, code: str, message: str, provider_status: str):
        super().__init__(message)
        self.code = code
        self.message = message
        self.provider_status = provider_status


class IrpTransientError(Exception):
    pass


def _pick_first(payload: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in payload and payload[key] not in (None, ""):
            return payload[key]
    return None


def _unwrap_dict(payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict):
        for key in ("Data", "data", "Result", "result"):
            nested = payload.get(key)
            if isinstance(nested, dict):
                return nested
        return payload
    return {}


def _state_code_from_gstin(gstin: str) -> str:
    normalized = normalize_gstin(gstin)
    if not normalized or len(normalized) < 2:
        return ""
    return normalized[:2]


class DisabledIrpProvider:
    provider_name = "disabled"

    async def lookup_taxpayer(self, credentials: IrpBranchCredentials, *, gstin: str) -> IrpTaxpayerProfile:
        raise IrpActionRequiredError(
            code="PROVIDER_DISABLED",
            message="IRP provider mode is disabled",
            provider_status="PROVIDER_DISABLED",
        )

    async def submit_irn(self, credentials: IrpBranchCredentials, *, payload: dict[str, Any]) -> IrpSubmissionResult:
        raise IrpActionRequiredError(
            code="PROVIDER_DISABLED",
            message="IRP provider mode is disabled",
            provider_status="PROVIDER_DISABLED",
        )

    async def get_irn_by_document(
        self,
        credentials: IrpBranchCredentials,
        *,
        document_number: str,
        document_type: str,
        document_date: str,
    ) -> IrpSubmissionResult:
        raise IrpActionRequiredError(
            code="PROVIDER_DISABLED",
            message="IRP provider mode is disabled",
            provider_status="PROVIDER_DISABLED",
        )


class StubIrpProvider:
    provider_name = "stub"

    async def lookup_taxpayer(self, credentials: IrpBranchCredentials, *, gstin: str) -> IrpTaxpayerProfile:
        normalized = normalize_gstin(gstin) or ""
        suffix = normalized[-4:] if normalized else "0000"
        return IrpTaxpayerProfile(
            gstin=normalized,
            legal_name=f"Taxpayer {suffix}",
            trade_name=f"Taxpayer {suffix}",
            address_line1=f"{suffix} Market Road",
            address_line2="Suite 1",
            location="Bengaluru",
            pincode="560001",
            state_code=_state_code_from_gstin(normalized),
        )

    async def submit_irn(self, credentials: IrpBranchCredentials, *, payload: dict[str, Any]) -> IrpSubmissionResult:
        document_number = str(_unwrap_dict(payload.get("DocDtls")).get("No", "UNKNOWN"))
        return IrpSubmissionResult(
            outcome="success",
            irn=f"IRN-STUB-{document_number}",
            ack_no=f"ACK-STUB-{document_number}",
            signed_qr_payload=f"QR-STUB-{document_number}",
            provider_status="SUBMITTED",
        )

    async def get_irn_by_document(
        self,
        credentials: IrpBranchCredentials,
        *,
        document_number: str,
        document_type: str,
        document_date: str,
    ) -> IrpSubmissionResult:
        return IrpSubmissionResult(
            outcome="success",
            irn=f"IRN-STUB-{document_number}",
            ack_no=f"ACK-STUB-{document_number}",
            signed_qr_payload=f"QR-STUB-{document_number}",
            provider_status="DUPLICATE_RECOVERED",
        )


class IrisDirectIrpProvider:
    provider_name = "iris_direct"

    def __init__(self, settings: Settings):
        self._settings = settings
        self._token_cache: dict[tuple[str, str], tuple[str, datetime]] = {}

    async def lookup_taxpayer(self, credentials: IrpBranchCredentials, *, gstin: str) -> IrpTaxpayerProfile:
        response = await self._post_json(
            url=self._settings.compliance_irp_get_gstin_details_url,
            credentials=credentials,
            json_body={"Gstin": normalize_gstin(gstin)},
        )
        data = _unwrap_dict(response)
        normalized = normalize_gstin(gstin) or ""
        return IrpTaxpayerProfile(
            gstin=normalized,
            legal_name=str(_pick_first(data, "LglNm", "LegalName", "legalName", "GstinLglNm") or ""),
            trade_name=str(_pick_first(data, "TrdNm", "TradeName", "tradeName", "GstinTrdNm") or ""),
            address_line1=str(_pick_first(data, "Addr1", "AddrBnm", "addressLine1") or ""),
            address_line2=str(_pick_first(data, "Addr2", "AddrBno", "addressLine2") or ""),
            location=str(_pick_first(data, "Loc", "location", "city") or ""),
            pincode=str(_pick_first(data, "Pin", "pincode", "postalCode") or ""),
            state_code=str(_pick_first(data, "Stcd", "stateCode") or _state_code_from_gstin(normalized)),
        )

    async def submit_irn(self, credentials: IrpBranchCredentials, *, payload: dict[str, Any]) -> IrpSubmissionResult:
        response = await self._post_json(
            url=self._settings.compliance_irp_generate_irn_url,
            credentials=credentials,
            json_body=payload,
        )
        return self._parse_submission_response(response)

    async def get_irn_by_document(
        self,
        credentials: IrpBranchCredentials,
        *,
        document_number: str,
        document_type: str,
        document_date: str,
    ) -> IrpSubmissionResult:
        response = await self._post_json(
            url=self._settings.compliance_irp_get_by_document_url,
            credentials=credentials,
            json_body={"DocNo": document_number, "DocTyp": document_type, "DocDt": document_date},
        )
        return self._parse_submission_response(response, provider_status="DUPLICATE_RECOVERED")

    async def _post_json(
        self,
        *,
        url: str | None,
        credentials: IrpBranchCredentials,
        json_body: dict[str, Any],
    ) -> dict[str, Any]:
        if not url:
            raise IrpActionRequiredError(
                code="PROVIDER_NOT_CONFIGURED",
                message="IRP endpoint URL is not configured",
                provider_status="PROVIDER_NOT_CONFIGURED",
            )
        headers = await self._build_headers(credentials)
        try:
            async with httpx.AsyncClient(timeout=self._settings.compliance_irp_timeout_seconds) as client:
                response = await client.post(url, json=json_body, headers=headers)
        except httpx.HTTPError as error:
            raise IrpTransientError(str(error)) from error
        body = response.json() if response.content else {}
        if response.status_code >= 500:
            raise IrpTransientError(f"IRP provider returned {response.status_code}")
        if response.status_code >= 400:
            self._raise_action_required(body, default_status="REQUEST_REJECTED")
        if self._response_has_error(body):
            self._raise_action_required(body, default_status="REQUEST_REJECTED")
        return body

    async def _build_headers(self, credentials: IrpBranchCredentials) -> dict[str, str]:
        token = await self._get_auth_token(credentials)
        client_id = self._settings.compliance_irp_client_id
        client_secret = self._settings.compliance_irp_client_secret
        if not client_id or not client_secret:
            raise IrpActionRequiredError(
                code="PROVIDER_NOT_CONFIGURED",
                message="IRP client credentials are not configured",
                provider_status="PROVIDER_NOT_CONFIGURED",
            )
        return {
            "client_id": client_id,
            "client_secret": client_secret,
            "gstin": credentials.branch_gstin,
            "user_name": credentials.api_username,
            "auth-token": token,
        }

    async def _get_auth_token(self, credentials: IrpBranchCredentials) -> str:
        cache_key = (credentials.branch_gstin, credentials.api_username)
        cached = self._token_cache.get(cache_key)
        if cached is not None and cached[1] > datetime.utcnow() + timedelta(minutes=5):
            return cached[0]

        auth_url = self._settings.compliance_irp_auth_url
        client_id = self._settings.compliance_irp_client_id
        client_secret = self._settings.compliance_irp_client_secret
        public_key_pem = self._settings.compliance_irp_public_key_pem
        if not auth_url or not client_id or not client_secret or not public_key_pem:
            raise IrpActionRequiredError(
                code="PROVIDER_NOT_CONFIGURED",
                message="IRP auth configuration is incomplete",
                provider_status="PROVIDER_NOT_CONFIGURED",
            )

        public_key = serialization.load_pem_public_key(public_key_pem.encode("utf-8"))
        app_key = b64encode(os.urandom(32)).decode("utf-8")
        payload = {
            "UserName": credentials.api_username,
            "Password": self._encrypt(public_key, credentials.api_password),
            "AppKey": self._encrypt(public_key, app_key),
            "ForceRefreshAccessToken": True,
        }
        headers = {
            "client_id": client_id,
            "client_secret": client_secret,
            "gstin": credentials.branch_gstin,
        }
        try:
            async with httpx.AsyncClient(timeout=self._settings.compliance_irp_timeout_seconds) as client:
                response = await client.post(auth_url, json=payload, headers=headers)
        except httpx.HTTPError as error:
            raise IrpTransientError(str(error)) from error

        body = response.json() if response.content else {}
        if response.status_code >= 500:
            raise IrpTransientError(f"IRP auth returned {response.status_code}")
        if response.status_code >= 400 or self._response_has_error(body):
            self._raise_action_required(body, default_status="AUTH_FAILED")
        data = _unwrap_dict(body)
        token = _pick_first(data, "AuthToken", "auth_token", "token")
        if not token:
            raise IrpTransientError("IRP auth response did not contain an auth token")
        expires_at = datetime.utcnow() + timedelta(hours=6)
        self._token_cache[cache_key] = (str(token), expires_at)
        return str(token)

    @staticmethod
    def _encrypt(public_key, value: str) -> str:
        encrypted = public_key.encrypt(
            value.encode("utf-8"),
            padding.PKCS1v15(),
        )
        return b64encode(encrypted).decode("utf-8")

    @staticmethod
    def _response_has_error(body: dict[str, Any]) -> bool:
        if body.get("Status") in {0, "0", False}:
            return True
        if any(key in body for key in ("error", "Error", "ErrorMessage", "errorMessage", "ErrorDetails")):
            return bool(body.get("error") or body.get("Error") or body.get("ErrorMessage") or body.get("errorMessage") or body.get("ErrorDetails"))
        return False

    @staticmethod
    def _raise_action_required(body: dict[str, Any], *, default_status: str) -> None:
        data = _unwrap_dict(body)
        error_code = _pick_first(data, "ErrorCode", "errorCode", "ErrCd") or _pick_first(body, "ErrorCode", "errorCode", "ErrCd")
        message = _pick_first(data, "ErrorMessage", "errorMessage", "message", "Msg") or _pick_first(
            body,
            "ErrorMessage",
            "errorMessage",
            "message",
            "Msg",
        )
        if not error_code and isinstance(body.get("ErrorDetails"), list) and body["ErrorDetails"]:
            detail = body["ErrorDetails"][0]
            if isinstance(detail, dict):
                error_code = _pick_first(detail, "ErrorCode", "errorCode", "ErrCd")
                message = message or _pick_first(detail, "ErrorMessage", "errorMessage", "message", "Msg")
        normalized_code = str(error_code or default_status)
        normalized_message = str(message or "IRP request was rejected")
        provider_status = "DUPLICATE" if normalized_code in {"2150", "2154"} else default_status
        raise IrpActionRequiredError(code=normalized_code, message=normalized_message, provider_status=provider_status)

    @staticmethod
    def _parse_submission_response(body: dict[str, Any], *, provider_status: str = "SUBMITTED") -> IrpSubmissionResult:
        data = _unwrap_dict(body)
        irn = _pick_first(data, "Irn", "IRN", "irn")
        ack_no = _pick_first(data, "AckNo", "ackNo", "Ack_Number")
        signed_qr_payload = _pick_first(data, "SignedQRCode", "SignedQRCodeData", "signedQRCode", "signed_qr_payload")
        if not irn or not ack_no or not signed_qr_payload:
            raise IrpActionRequiredError(
                code="INVALID_PROVIDER_RESPONSE",
                message="IRP response did not contain the expected IRN data",
                provider_status="INVALID_PROVIDER_RESPONSE",
            )
        return IrpSubmissionResult(
            outcome="success",
            irn=str(irn),
            ack_no=str(ack_no),
            signed_qr_payload=str(signed_qr_payload),
            provider_status=provider_status,
        )


def build_irp_provider(settings: Settings):
    if settings.compliance_irp_mode == "stub":
        return StubIrpProvider()
    if settings.compliance_irp_mode == "iris_direct":
        return IrisDirectIrpProvider(settings)
    return DisabledIrpProvider()
