from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any

import httpx
import jwt
from fastapi import HTTPException, status
from jwt import InvalidTokenError
from jwt.algorithms import RSAAlgorithm

from ..config import Settings


@dataclass(slots=True)
class IdentityClaims:
    external_subject: str
    email: str
    full_name: str
    provider: str = "korsenex_idp"


class StubKorsenexIdentityProvider:
    provider_name = "korsenex_idp"

    def validate_token(self, token: str) -> IdentityClaims:
        if not token.startswith("stub:"):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid stub token")
        fields: dict[str, str] = {}
        for segment in token.removeprefix("stub:").split(";"):
            key, _, value = segment.partition("=")
            if key and value:
                fields[key] = value
        if not {"sub", "email", "name"}.issubset(fields):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incomplete stub token")
        return IdentityClaims(
            external_subject=fields["sub"],
            email=fields["email"].lower(),
            full_name=fields["name"],
            provider=self.provider_name,
        )


class JwksKorsenexIdentityProvider:
    provider_name = "korsenex_idp"

    def __init__(
        self,
        *,
        jwks_url: str,
        issuer: str,
        audience: str,
        algorithms: list[str],
        timeout_seconds: float,
        cache_seconds: int,
    ) -> None:
        self._jwks_url = jwks_url
        self._issuer = issuer
        self._audience = audience
        self._algorithms = algorithms
        self._timeout_seconds = timeout_seconds
        self._cache_seconds = cache_seconds
        self._jwks_cache: dict[str, Any] | None = None
        self._jwks_cached_at = 0.0

    def validate_token(self, token: str) -> IdentityClaims:
        key = self._resolve_signing_key(token)
        try:
            payload = jwt.decode(
                token,
                key=key,
                algorithms=self._algorithms,
                audience=self._audience,
                issuer=self._issuer,
            )
        except InvalidTokenError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid identity token") from exc

        subject = str(payload.get("sub") or "").strip()
        email = str(payload.get("email") or payload.get("preferred_username") or "").strip().lower()
        if not subject:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identity token missing subject")
        if not email:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identity token missing email")
        full_name = (
            str(payload.get("name") or "").strip()
            or str(payload.get("preferred_username") or "").strip()
            or email
        )
        return IdentityClaims(
            external_subject=subject,
            email=email,
            full_name=full_name,
            provider=self.provider_name,
        )

    def _resolve_signing_key(self, token: str):
        try:
            header = jwt.get_unverified_header(token)
        except InvalidTokenError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid identity token") from exc
        key_id = str(header.get("kid") or "").strip()
        if not key_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identity token missing kid")

        for jwk in self._load_jwks()["keys"]:
            if jwk.get("kid") == key_id:
                if jwk.get("kty") != "RSA":
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Unsupported identity signing key type",
                    )
                return RSAAlgorithm.from_jwk(json.dumps(jwk))
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unknown identity signing key")

    def _load_jwks(self) -> dict[str, Any]:
        now = time.monotonic()
        if self._jwks_cache is not None and now - self._jwks_cached_at < self._cache_seconds:
            return self._jwks_cache

        try:
            response = httpx.get(self._jwks_url, timeout=self._timeout_seconds)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Identity provider key fetch failed",
            ) from exc
        jwks = response.json()
        if not isinstance(jwks, dict) or not isinstance(jwks.get("keys"), list):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Identity provider returned invalid JWKS",
            )
        self._jwks_cache = jwks
        self._jwks_cached_at = now
        return jwks


def build_identity_provider(settings: Settings):
    if settings.korsenex_idp_mode == "stub":
        return StubKorsenexIdentityProvider()
    if settings.korsenex_idp_mode == "jwks":
        if not settings.korsenex_idp_jwks_url:
            raise RuntimeError("Korsenex JWKS mode requires korsenex_idp_jwks_url")
        if not settings.korsenex_idp_issuer:
            raise RuntimeError("Korsenex JWKS mode requires korsenex_idp_issuer")
        if not settings.korsenex_idp_audience:
            raise RuntimeError("Korsenex JWKS mode requires korsenex_idp_audience")
        return JwksKorsenexIdentityProvider(
            jwks_url=settings.korsenex_idp_jwks_url,
            issuer=settings.korsenex_idp_issuer,
            audience=settings.korsenex_idp_audience,
            algorithms=settings.korsenex_idp_algorithms,
            timeout_seconds=settings.korsenex_idp_jwks_timeout_seconds,
            cache_seconds=settings.korsenex_idp_jwks_cache_seconds,
        )
    raise RuntimeError(f"Unsupported Korsenex IDP mode: {settings.korsenex_idp_mode}")
