from __future__ import annotations

import argparse
import importlib.util
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Callable

import httpx


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from store_control_plane.environment_drift import (  # noqa: E402
    build_environment_drift_report,
    summarize_environment_drift_report,
    write_environment_drift_report,
)


SendRequest = Callable[..., dict[str, object]]
VerifyDeployedCallable = Callable[..., dict[str, object]]


def _load_verify_script_module():
    script_path = SERVICE_ROOT / "scripts" / "verify_deployed_control_plane.py"
    spec = importlib.util.spec_from_file_location("verify_deployed_control_plane_script", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


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
) -> dict[str, object]:
    response = send_request(method, url)
    status_code = int(response.get("status_code") or 0)
    if status_code != 200:
        raise ValueError(f"unexpected status {status_code} from {url}")
    payload = response.get("json")
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object from {url}")
    return payload


def verify_environment_drift(
    *,
    base_url: str,
    expected_environment: str,
    expected_release_version: str | None = None,
    output_path: Path,
    verify_deployed: VerifyDeployedCallable | None = None,
    send_request: SendRequest | None = None,
) -> dict[str, object]:
    resolved_base_url = _normalize_base_url(base_url)
    deployed_verifier = verify_deployed or _load_verify_script_module().verify_deployed_control_plane
    request = send_request or _default_send_request

    deployed_result = deployed_verifier(
        base_url=resolved_base_url,
        expected_environment=expected_environment,
        expected_release_version=expected_release_version,
    )
    environment_contract = _expect_json_response(
        request,
        "GET",
        f"{resolved_base_url}/v1/system/environment-contract",
    )
    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    report = build_environment_drift_report(
        expected_environment=expected_environment,
        base_url=resolved_base_url,
        release_version=expected_release_version or str(deployed_result.get("release_version") or ""),
        environment_contract=environment_contract,
        generated_at=generated_at,
    )
    write_environment_drift_report(report, output_path=output_path)
    payload = report.to_dict()
    payload["output_path"] = str(output_path)
    payload["summary"] = summarize_environment_drift_report(report)
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify deployed environment contract drift for a Store control plane.")
    parser.add_argument("--base-url", required=True, help="Public control-plane base URL, for example https://control.store.korsenex.com")
    parser.add_argument("--expected-environment", required=True, help="Expected deployment environment label such as staging or prod.")
    parser.add_argument("--expected-release-version", help="Expected release version reported by the deployment.")
    parser.add_argument("--output-path", required=True, help="JSON report path for the generated environment drift evidence.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = verify_environment_drift(
        base_url=args.base_url,
        expected_environment=args.expected_environment,
        expected_release_version=args.expected_release_version,
        output_path=Path(args.output_path),
    )
    print(json.dumps(result, indent=2))
    return 0 if result.get("status") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
