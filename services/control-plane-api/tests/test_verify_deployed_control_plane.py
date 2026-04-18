from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_verify_script_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "verify_deployed_control_plane.py"
    spec = importlib.util.spec_from_file_location("verify_deployed_control_plane_script", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_verify_deployed_control_plane_checks_health_authority_and_optional_auth() -> None:
    module = _load_verify_script_module()
    seen: list[tuple[str, str, dict[str, str] | None]] = []
    auth_attempts = 0
    webhook_attempts = 0

    def fake_send_request(
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        json_body: dict[str, object] | None = None,
        timeout_seconds: float = 10.0,
    ) -> dict[str, object]:
        nonlocal auth_attempts, webhook_attempts
        del timeout_seconds
        seen.append((method, url, headers))
        if method == "GET" and url.endswith("/v1/system/health"):
            return {
                "status_code": 200,
                "headers": {
                    "x-frame-options": "DENY",
                    "x-content-type-options": "nosniff",
                    "referrer-policy": "no-referrer",
                    "content-security-policy": "default-src 'self'; frame-ancestors 'none'",
                    "strict-transport-security": "max-age=31536000; includeSubDomains",
                },
                "json": {
                    "status": "ok",
                    "environment": "staging",
                    "public_base_url": "https://control.staging.store.korsenex.com",
                    "release_version": "2026.04.14-staging",
                    "database": {"status": "ok"},
                    "operations_worker": {"configured": True},
                },
            }
        if method == "GET" and url.endswith("/v1/system/authority-boundary"):
            return {
                "status_code": 200,
                "headers": {},
                "json": {
                    "control_plane_service": "store-control-plane",
                    "legacy_service": "legacy-retail-api",
                    "cutover_phase": "post-cutover",
                    "legacy_write_mode": "cutover",
                    "migrated_domains": ["onboarding"],
                    "legacy_remaining_domains": [],
                    "shutdown_criteria": [],
                    "shutdown_steps": [],
                },
            }
        if method == "GET" and url.endswith("/v1/system/security-controls"):
            return {
                "status_code": 200,
                "headers": {},
                "json": {
                    "secure_headers_enabled": True,
                    "secure_headers_hsts_enabled": True,
                    "secure_headers_csp": "default-src 'self'; frame-ancestors 'none'",
                    "rate_limits": {
                        "window_seconds": 60,
                        "auth_requests": 2,
                        "activation_requests": 2,
                        "webhook_requests": 2,
                    },
                },
            }
        if method == "GET" and url.endswith("/v1/auth/me"):
            return {
                "status_code": 200,
                "headers": {},
                "json": {"email": "ops@store.korsenex.com"},
            }
        if method == "POST" and url.endswith("/v1/auth/oidc/exchange"):
            auth_attempts += 1
            if auth_attempts <= 2:
                assert json_body == {"token": "security-probe-invalid-token"}
                return {"status_code": 401, "headers": {}, "json": {"detail": "invalid token"}}
            return {
                "status_code": 429,
                "headers": {"retry-after": "60"},
                "json": {"detail": "Rate limit exceeded"},
            }
        if method == "POST" and url.endswith("/v1/billing/webhooks/cashfree/payments"):
            webhook_attempts += 1
            if webhook_attempts <= 2:
                return {"status_code": 400, "headers": {}, "json": {"detail": "invalid webhook"}}
            return {
                "status_code": 429,
                "headers": {"retry-after": "60"},
                "json": {"detail": "Rate limit exceeded"},
            }
        raise AssertionError(f"unexpected {method} {url}")

    result = module.verify_deployed_control_plane(
        base_url="https://control.staging.store.korsenex.com",
        expected_environment="staging",
        expected_release_version="2026.04.14-staging",
        bearer_token="secret-token",
        send_request=fake_send_request,
    )

    assert result["status"] == "ok"
    assert result["environment"] == "staging"
    assert result["authenticated_actor_email"] == "ops@store.korsenex.com"
    assert result["security_result"]["status"] == "passed"
    assert result["security_result"]["secure_headers"]["status"] == "passed"
    assert result["security_result"]["auth_rate_limit"]["status"] == "passed"
    assert result["security_result"]["webhook_rate_limit"]["status"] == "passed"
    assert (
        "GET",
        "https://control.staging.store.korsenex.com/v1/auth/me",
        {"authorization": "Bearer secret-token"},
    ) in seen


def test_verify_deployed_control_plane_flags_missing_secure_header() -> None:
    module = _load_verify_script_module()

    def fake_send_request(
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        json_body: dict[str, object] | None = None,
        timeout_seconds: float = 10.0,
    ) -> dict[str, object]:
        del headers, json_body, timeout_seconds
        if method == "GET" and url.endswith("/v1/system/health"):
            return {
                "status_code": 200,
                "headers": {
                    "x-content-type-options": "nosniff",
                    "referrer-policy": "no-referrer",
                    "content-security-policy": "default-src 'self'; frame-ancestors 'none'",
                    "strict-transport-security": "max-age=31536000; includeSubDomains",
                },
                "json": {
                    "status": "ok",
                    "environment": "staging",
                    "public_base_url": "https://control.staging.store.korsenex.com",
                    "release_version": "2026.04.14-staging",
                    "database": {"status": "ok"},
                    "operations_worker": {"configured": True},
                },
            }
        if method == "GET" and url.endswith("/v1/system/authority-boundary"):
            return {
                "status_code": 200,
                "headers": {},
                "json": {
                    "control_plane_service": "store-control-plane",
                    "legacy_service": "legacy-retail-api",
                    "cutover_phase": "post-cutover",
                    "legacy_write_mode": "cutover",
                    "migrated_domains": ["onboarding"],
                    "legacy_remaining_domains": [],
                    "shutdown_criteria": [],
                    "shutdown_steps": [],
                },
            }
        if method == "GET" and url.endswith("/v1/system/security-controls"):
            return {
                "status_code": 200,
                "headers": {},
                "json": {
                    "secure_headers_enabled": True,
                    "secure_headers_hsts_enabled": True,
                    "secure_headers_csp": "default-src 'self'; frame-ancestors 'none'",
                    "rate_limits": {
                        "window_seconds": 60,
                        "auth_requests": 1,
                        "activation_requests": 1,
                        "webhook_requests": 1,
                    },
                },
            }
        if method == "POST" and url.endswith("/v1/auth/oidc/exchange"):
            return {"status_code": 429, "headers": {"retry-after": "60"}, "json": {"detail": "Rate limit exceeded"}}
        if method == "POST" and url.endswith("/v1/billing/webhooks/cashfree/payments"):
            return {"status_code": 429, "headers": {"retry-after": "60"}, "json": {"detail": "Rate limit exceeded"}}
        raise AssertionError(f"unexpected {method} {url}")

    result = module.verify_deployed_control_plane(
        base_url="https://control.staging.store.korsenex.com",
        expected_environment="staging",
        expected_release_version="2026.04.14-staging",
        send_request=fake_send_request,
    )

    assert result["security_result"]["status"] == "failed"
    assert result["security_result"]["secure_headers"]["status"] == "failed"
