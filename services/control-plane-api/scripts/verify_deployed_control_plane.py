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


FetchJson = Callable[[str], dict[str, object]]


def _normalize_base_url(base_url: str) -> str:
    normalized = base_url.strip().rstrip("/")
    if not normalized:
        raise ValueError("base URL is required")
    return normalized


def _default_fetch_json(url: str, *, headers: dict[str, str] | None = None, timeout_seconds: float = 10.0) -> dict[str, object]:
    response = httpx.get(url, headers=headers, timeout=timeout_seconds)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object from {url}")
    return payload


def verify_deployed_control_plane(
    *,
    base_url: str,
    expected_environment: str | None = None,
    expected_release_version: str | None = None,
    bearer_token: str | None = None,
    fetch_json: Callable[..., dict[str, object]] | None = None,
) -> dict[str, object]:
    resolved_base_url = _normalize_base_url(base_url)
    fetcher = fetch_json or _default_fetch_json

    health = fetcher(f"{resolved_base_url}/v1/system/health")
    if health.get("status") != "ok":
        raise ValueError("system health is not ok")
    if expected_environment and health.get("environment") != expected_environment:
        raise ValueError("deployed environment mismatch")
    if expected_release_version and health.get("release_version") != expected_release_version:
        raise ValueError("deployed release version mismatch")

    authority = fetcher(f"{resolved_base_url}/v1/system/authority-boundary")
    result: dict[str, object] = {
        "status": str(health.get("status")),
        "environment": health.get("environment"),
        "release_version": health.get("release_version"),
        "legacy_write_mode": authority.get("legacy_write_mode"),
        "legacy_remaining_domains": authority.get("legacy_remaining_domains"),
    }
    if bearer_token:
        actor = fetcher(
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


if __name__ == "__main__":
    main()
