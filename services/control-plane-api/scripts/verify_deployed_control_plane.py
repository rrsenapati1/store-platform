from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Callable

import httpx

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))


SendRequest = Callable[..., dict[str, object]]


def _normalize_base_url(base_url: str) -> str:
    normalized = base_url.strip().rstrip("/")
    if not normalized:
        raise ValueError("base URL is required")
    return normalized


def _default_send_request(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    json_body: dict[str, object] | None = None,
    timeout_seconds: float = 10.0,
) -> dict[str, object]:
    response = httpx.request(method, url, headers=headers, json=json_body, timeout=timeout_seconds)
    payload: dict[str, object] | None = None
    if response.content:
        try:
            parsed = response.json()
        except ValueError:
            parsed = None
        if isinstance(parsed, dict):
            payload = parsed
    return {
        "status_code": response.status_code,
        "headers": {key.lower(): value for key, value in response.headers.items()},
        "json": payload,
    }


def _expect_json_response(
    send_request: SendRequest,
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    json_body: dict[str, object] | None = None,
    expected_status_codes: tuple[int, ...] = (200,),
) -> dict[str, object]:
    response = send_request(
        method,
        url,
        headers=headers,
        json_body=json_body,
    )
    status_code = int(response.get("status_code") or 0)
    if status_code not in expected_status_codes:
        raise ValueError(f"unexpected status {status_code} from {url}")
    payload = response.get("json")
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object from {url}")
    return payload


def _payload_from_response(response: dict[str, object], *, url: str) -> dict[str, object]:
    payload = response.get("json")
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object from {url}")
    return payload


def _verify_secure_headers(*, health_headers: dict[str, str], security_controls: dict[str, object]) -> dict[str, object]:
    if not bool(security_controls.get("secure_headers_enabled")):
        return {"status": "failed", "summary": "secure headers are disabled"}
    missing_headers: list[str] = []
    expected_pairs = {
        "x-frame-options": "DENY",
        "x-content-type-options": "nosniff",
        "referrer-policy": "no-referrer",
    }
    for header_name, expected_value in expected_pairs.items():
        actual_value = health_headers.get(header_name)
        if actual_value != expected_value:
            missing_headers.append(header_name)
    csp = str(security_controls.get("secure_headers_csp") or "")
    if health_headers.get("content-security-policy") != csp:
        missing_headers.append("content-security-policy")
    if bool(security_controls.get("secure_headers_hsts_enabled")) and "strict-transport-security" not in health_headers:
        missing_headers.append("strict-transport-security")
    if missing_headers:
        return {
            "status": "failed",
            "summary": f"missing or mismatched headers: {', '.join(missing_headers)}",
        }
    return {"status": "passed"}


def _probe_rate_limit(
    send_request: SendRequest,
    *,
    resolved_base_url: str,
    path: str,
    payload: dict[str, object],
    limit: int,
    window_seconds: int,
) -> dict[str, object]:
    if limit <= 0:
        return {"status": "failed", "summary": "rate limit is not configured"}
    for attempt in range(1, limit + 1):
        response = send_request("POST", f"{resolved_base_url}{path}", json_body=payload)
        if int(response.get("status_code") or 0) == 429:
            return {
                "status": "failed",
                "summary": f"rate limit triggered early on attempt {attempt}",
            }
    throttled = send_request("POST", f"{resolved_base_url}{path}", json_body=payload)
    if int(throttled.get("status_code") or 0) != 429:
        return {
            "status": "failed",
            "summary": f"expected 429 on attempt {limit + 1}",
        }
    retry_after = str(dict(throttled.get("headers") or {}).get("retry-after") or "")
    if retry_after != str(window_seconds):
        return {
            "status": "failed",
            "summary": f"unexpected Retry-After header: {retry_after or 'missing'}",
        }
    return {
        "status": "passed",
        "throttled_on_attempt": limit + 1,
        "retry_after_seconds": retry_after,
    }


def verify_deployed_control_plane(
    *,
    base_url: str,
    expected_environment: str | None = None,
    expected_release_version: str | None = None,
    bearer_token: str | None = None,
    send_request: SendRequest | None = None,
) -> dict[str, object]:
    resolved_base_url = _normalize_base_url(base_url)
    request = send_request or _default_send_request

    health_url = f"{resolved_base_url}/v1/system/health"
    health_response = request("GET", health_url)
    health_headers = dict(health_response.get("headers") or {})
    health = _payload_from_response(health_response, url=health_url)
    if health.get("status") != "ok":
        raise ValueError("system health is not ok")
    if expected_environment and health.get("environment") != expected_environment:
        raise ValueError("deployed environment mismatch")
    if expected_release_version and health.get("release_version") != expected_release_version:
        raise ValueError("deployed release version mismatch")

    authority = _expect_json_response(request, "GET", f"{resolved_base_url}/v1/system/authority-boundary")
    security_controls = _expect_json_response(request, "GET", f"{resolved_base_url}/v1/system/security-controls")
    rate_limits = dict(security_controls.get("rate_limits") or {})
    secure_headers_result = _verify_secure_headers(
        health_headers=health_headers,
        security_controls=security_controls,
    )
    auth_rate_limit_result = _probe_rate_limit(
        request,
        resolved_base_url=resolved_base_url,
        path="/v1/auth/oidc/exchange",
        payload={"token": "security-probe-invalid-token"},
        limit=int(rate_limits.get("auth_requests") or 0),
        window_seconds=int(rate_limits.get("window_seconds") or 0),
    )
    webhook_rate_limit_result = _probe_rate_limit(
        request,
        resolved_base_url=resolved_base_url,
        path="/v1/billing/webhooks/cashfree/payments",
        payload={"probe": True},
        limit=int(rate_limits.get("webhook_requests") or 0),
        window_seconds=int(rate_limits.get("window_seconds") or 0),
    )
    security_result = {
        "status": "passed"
        if all(
            result.get("status") == "passed"
            for result in (secure_headers_result, auth_rate_limit_result, webhook_rate_limit_result)
        )
        else "failed",
        "controls": security_controls,
        "secure_headers": secure_headers_result,
        "auth_rate_limit": auth_rate_limit_result,
        "webhook_rate_limit": webhook_rate_limit_result,
    }
    result: dict[str, object] = {
        "status": str(health.get("status")),
        "environment": health.get("environment"),
        "release_version": health.get("release_version"),
        "alembic_head": health.get("alembic_head"),
        "legacy_write_mode": authority.get("legacy_write_mode"),
        "legacy_remaining_domains": authority.get("legacy_remaining_domains"),
        "security_result": security_result,
    }
    if bearer_token:
        actor = _expect_json_response(
            request,
            "GET",
            f"{resolved_base_url}/v1/auth/me",
            headers={"authorization": f"Bearer {bearer_token}"},
        )
        result["authenticated_actor_email"] = actor.get("email")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify a deployed Store control plane environment.")
    parser.add_argument("--base-url", required=True, help="Public control-plane base URL, for example https://control.store.korsenex.com")
    parser.add_argument("--expected-environment", help="Expected deployment environment label such as staging or prod.")
    parser.add_argument("--expected-release-version", help="Expected release version reported by the deployment.")
    parser.add_argument("--bearer-token", help="Optional bearer token used to verify /v1/auth/me against the deployment.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = verify_deployed_control_plane(
        base_url=args.base_url,
        expected_environment=args.expected_environment,
        expected_release_version=args.expected_release_version,
        bearer_token=args.bearer_token,
    )
    print(json.dumps(result, indent=2))
    if dict(result.get("security_result") or {}).get("status") == "failed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
