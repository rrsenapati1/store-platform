from __future__ import annotations

import base64
import importlib
import json
from pathlib import Path
from types import SimpleNamespace

import httpx
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from store_control_plane.main import create_app
from conftest import sqlite_test_database_url


def _base64url_uint(value: int) -> str:
    raw = value.to_bytes((value.bit_length() + 7) // 8, "big")
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _rsa_jwks() -> tuple[rsa.RSAPrivateKey, dict[str, object]]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_numbers = private_key.public_key().public_numbers()
    return private_key, {
        "keys": [
            {
                "kty": "RSA",
                "use": "sig",
                "alg": "RS256",
                "kid": "test-key-1",
                "n": _base64url_uint(public_numbers.n),
                "e": _base64url_uint(public_numbers.e),
            }
        ]
    }


def _build_token(private_key: rsa.RSAPrivateKey) -> str:
    payload = {
        "sub": "platform-admin-1",
        "email": "admin@store.local",
        "name": "Platform Admin",
        "iss": "https://id.korsenex.local",
        "aud": "store-control-plane",
    }
    return jwt.encode(
        payload,
        private_key,
        algorithm="RS256",
        headers={"kid": "test-key-1"},
    )


def test_oidc_exchange_supports_jwks_mode(monkeypatch):
    database_url = sqlite_test_database_url("control-plane-jwks")
    private_key, jwks = _rsa_jwks()
    idp_module = importlib.import_module("store_control_plane.services.idp")

    def _fake_get(url: str, *, timeout: float = 5.0) -> httpx.Response:
        assert url == "https://id.korsenex.local/.well-known/jwks.json"
        return httpx.Response(
            status_code=200,
            content=json.dumps(jwks).encode("utf-8"),
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(idp_module, "httpx", SimpleNamespace(get=_fake_get), raising=False)

    client = TestClient(
        create_app(
            database_url=database_url,
            bootstrap_database=True,
            korsenex_idp_mode="jwks",
            korsenex_idp_jwks_url="https://id.korsenex.local/.well-known/jwks.json",
            korsenex_idp_issuer="https://id.korsenex.local",
            korsenex_idp_audience="store-control-plane",
            platform_admin_emails=["admin@store.local"],
        )
    )

    exchange = client.post(
        "/v1/auth/oidc/exchange",
        json={"token": _build_token(private_key)},
    )

    assert exchange.status_code == 200

    me = client.get(
        "/v1/auth/me",
        headers={"authorization": f"Bearer {exchange.json()['access_token']}"},
    )

    assert me.status_code == 200
    assert me.json()["email"] == "admin@store.local"
    assert me.json()["is_platform_admin"] is True
