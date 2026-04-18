from __future__ import annotations

import argparse
import importlib.util
from datetime import datetime, timezone
import json
import sys
from pathlib import Path
from typing import Callable

import httpx


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))


from store_control_plane.operational_alerts import build_operational_alert_report, write_operational_alert_report


SendRequest = Callable[..., dict[str, object]]
VerifyDeployed = Callable[..., dict[str, object]]


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


def _expect_json_response(send_request: SendRequest, method: str, url: str) -> dict[str, object]:
    response = send_request(method, url)
    status_code = int(response.get("status_code") or 0)
    if status_code != 200:
        raise ValueError(f"unexpected status {status_code} from {url}")
    payload = response.get("json")
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object from {url}")
    return payload


def verify_operational_alert_posture(
    *,
    base_url: str,
    output_path: Path,
    expected_environment: str | None = None,
    expected_release_version: str | None = None,
    max_retryable_count: int = 0,
    max_degraded_branch_count: int = 0,
    max_backup_age_hours: float = 26,
    verify_deployed: VerifyDeployed | None = None,
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
    observability_summary = _expect_json_response(
        request,
        "GET",
        f"{resolved_base_url}/v1/platform/observability/summary",
    )
    report = build_operational_alert_report(
        generated_at=datetime.now(timezone.utc).isoformat(),
        environment=str(deployed_result.get("environment") or ""),
        release_version=str(deployed_result.get("release_version") or ""),
        observability_summary=observability_summary,
        security_result=dict(deployed_result.get("security_result") or {}),
        thresholds={
            "max_retryable_count": max_retryable_count,
            "max_degraded_branch_count": max_degraded_branch_count,
            "max_backup_age_hours": max_backup_age_hours,
        },
    )
    write_operational_alert_report(report, output_path=output_path)
    report["output_path"] = str(output_path)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify deployed Store operational alert posture and write a JSON report.")
    parser.add_argument("--base-url", required=True, help="Public control-plane base URL, for example https://control.store.korsenex.com")
    parser.add_argument("--expected-environment", help="Expected deployment environment label such as staging or prod.")
    parser.add_argument("--expected-release-version", help="Expected release version reported by the deployment.")
    parser.add_argument("--output-path", required=True, help="JSON file path for the generated operational alert report.")
    parser.add_argument("--max-retryable-count", type=int, default=0, help="Maximum allowed retryable operations jobs before alert verification fails.")
    parser.add_argument("--max-degraded-branch-count", type=int, default=0, help="Maximum allowed degraded branches before alert verification fails.")
    parser.add_argument("--max-backup-age-hours", type=float, default=26, help="Maximum allowed backup age in hours before alert verification fails.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = verify_operational_alert_posture(
        base_url=args.base_url,
        output_path=Path(args.output_path),
        expected_environment=args.expected_environment,
        expected_release_version=args.expected_release_version,
        max_retryable_count=args.max_retryable_count,
        max_degraded_branch_count=args.max_degraded_branch_count,
        max_backup_age_hours=args.max_backup_age_hours,
    )
    print(json.dumps(result, indent=2))
    return 0 if result.get("status") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
