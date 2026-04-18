from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import importlib.util
import json
from time import perf_counter
import sys
from pathlib import Path
from typing import Callable

import httpx


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))


from store_control_plane.deployed_load_verification import (
    DeployedLoadSample,
    build_deployed_load_report,
    deployed_load_foundation_budgets,
    summarize_deployed_load_report,
    write_deployed_load_report,
)


VerifyCallable = Callable[..., dict[str, object]]
SendRequestCallable = Callable[..., dict[str, object]]


def _load_verify_script_module():
    script_path = SERVICE_ROOT / "scripts" / "verify_deployed_control_plane.py"
    spec = importlib.util.spec_from_file_location("verify_deployed_control_plane_script", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _normalize_base_url(base_url: str) -> str:
    return base_url.rstrip("/")


def _default_send_request(method: str, url: str, **kwargs: object) -> dict[str, object]:
    response = httpx.request(method, url, timeout=30.0, **kwargs)
    payload: object
    try:
        payload = response.json()
    except ValueError:
        payload = response.text
    return {"status_code": response.status_code, "json": payload}


def _require_fixture(name: str, value: str | None) -> str:
    if value is None or not value.strip():
        raise ValueError(f"{name} is required for deployed load verification")
    return value.strip()


def _measure_requests(
    *,
    action: Callable[[], None],
    concurrency: int,
    iterations_per_worker: int,
) -> list[DeployedLoadSample]:
    def worker() -> list[DeployedLoadSample]:
        samples: list[DeployedLoadSample] = []
        for _ in range(iterations_per_worker):
            started_at = perf_counter()
            try:
                action()
            except Exception as exc:  # pragma: no cover - exercised via report status
                samples.append(
                    DeployedLoadSample(
                        duration_ms=(perf_counter() - started_at) * 1000.0,
                        success=False,
                        error_message=str(exc),
                    )
                )
            else:
                samples.append(
                    DeployedLoadSample(
                        duration_ms=(perf_counter() - started_at) * 1000.0,
                        success=True,
                    )
                )
        return samples

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(worker) for _ in range(concurrency)]
    samples: list[DeployedLoadSample] = []
    for future in futures:
        samples.extend(future.result())
    return samples


def _expect_success_response(response: dict[str, object]) -> dict[str, object]:
    status_code = int(response.get("status_code") or 0)
    if status_code >= 400:
        raise RuntimeError(f"http_{status_code}")
    payload = response.get("json")
    if isinstance(payload, dict):
        return payload
    return {}


def verify_deployed_load_posture(
    *,
    base_url: str,
    output_path: Path,
    expected_environment: str | None = None,
    expected_release_version: str | None = None,
    admin_bearer_token: str | None = None,
    branch_bearer_token: str | None = None,
    tenant_id: str | None = None,
    branch_id: str | None = None,
    product_id: str | None = None,
    concurrency: int = 4,
    iterations_per_worker: int = 5,
    generated_at: str | None = None,
    verify_deployed: VerifyCallable | None = None,
    send_request: SendRequestCallable | None = None,
) -> dict[str, object]:
    if concurrency <= 0:
        raise ValueError("concurrency must be greater than zero")
    if iterations_per_worker <= 0:
        raise ValueError("iterations_per_worker must be greater than zero")

    admin_token = _require_fixture("admin_bearer_token", admin_bearer_token)
    branch_token = _require_fixture("branch_bearer_token", branch_bearer_token)
    resolved_tenant_id = _require_fixture("tenant_id", tenant_id)
    resolved_branch_id = _require_fixture("branch_id", branch_id)
    resolved_product_id = _require_fixture("product_id", product_id)

    verification = verify_deployed or _load_verify_script_module().verify_deployed_control_plane
    deployed_result = verification(
        base_url=base_url,
        expected_environment=expected_environment,
        expected_release_version=expected_release_version,
        bearer_token=branch_token,
    )

    resolved_base_url = _normalize_base_url(base_url)
    sender = send_request or _default_send_request

    def system_health_http() -> None:
        _expect_success_response(sender("GET", f"{resolved_base_url}/v1/system/health"))

    def observability_summary_http() -> None:
        _expect_success_response(
            sender(
                "GET",
                f"{resolved_base_url}/v1/platform/observability/summary",
                headers={"authorization": f"Bearer {admin_token}"},
            )
        )

    def checkout_price_preview_http() -> None:
        _expect_success_response(
            sender(
                "POST",
                f"{resolved_base_url}/v1/tenants/{resolved_tenant_id}/branches/{resolved_branch_id}/checkout-price-preview",
                headers={"authorization": f"Bearer {branch_token}"},
                json={
                    "customer_name": "Load Verification",
                    "customer_gstin": None,
                    "promotion_code": None,
                    "loyalty_points_to_redeem": 0,
                    "store_credit_amount": 0,
                    "lines": [{"product_id": resolved_product_id, "quantity": 1}],
                },
            )
        )

    def branch_management_dashboard_http() -> None:
        _expect_success_response(
            sender(
                "GET",
                f"{resolved_base_url}/v1/tenants/{resolved_tenant_id}/branches/{resolved_branch_id}/management-dashboard",
                headers={"authorization": f"Bearer {branch_token}"},
            )
        )

    scenario_samples = {
        "system_health_http": _measure_requests(action=system_health_http, concurrency=concurrency, iterations_per_worker=iterations_per_worker),
        "observability_summary_http": _measure_requests(action=observability_summary_http, concurrency=concurrency, iterations_per_worker=iterations_per_worker),
        "checkout_price_preview_http": _measure_requests(action=checkout_price_preview_http, concurrency=concurrency, iterations_per_worker=iterations_per_worker),
        "branch_management_dashboard_http": _measure_requests(action=branch_management_dashboard_http, concurrency=concurrency, iterations_per_worker=iterations_per_worker),
    }

    report = build_deployed_load_report(
        scenario_set="deployed-load-foundation",
        generated_at=generated_at or datetime.now(timezone.utc).isoformat(),
        environment=str(deployed_result.get("environment") or expected_environment or ""),
        release_version=str(deployed_result.get("release_version") or expected_release_version or ""),
        concurrency=concurrency,
        iterations_per_worker=iterations_per_worker,
        budgets=deployed_load_foundation_budgets(),
        scenario_samples=scenario_samples,
    )
    write_deployed_load_report(report, output_path=output_path)
    payload = report.to_dict()
    payload["summary"] = summarize_deployed_load_report(report)
    payload["output_path"] = str(output_path)
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify deployed Store load posture and write a JSON report.")
    parser.add_argument("--base-url", required=True, help="Public control-plane base URL, for example https://control.store.korsenex.com")
    parser.add_argument("--expected-environment", help="Expected deployment environment label such as staging or prod.")
    parser.add_argument("--expected-release-version", help="Expected release version reported by the deployment.")
    parser.add_argument("--output-path", required=True, help="JSON file path for the generated deployed load report.")
    parser.add_argument("--admin-bearer-token", required=True, help="Bearer token with observability-summary access.")
    parser.add_argument("--branch-bearer-token", required=True, help="Bearer token with branch checkout-preview and management-dashboard access.")
    parser.add_argument("--tenant-id", required=True, help="Fixture tenant identifier for branch-safe load scenarios.")
    parser.add_argument("--branch-id", required=True, help="Fixture branch identifier for branch-safe load scenarios.")
    parser.add_argument("--product-id", required=True, help="Fixture product identifier used for checkout preview requests.")
    parser.add_argument("--concurrency", type=int, default=4, help="Concurrent workers per scenario.")
    parser.add_argument("--iterations-per-worker", type=int, default=5, help="Requests executed by each worker per scenario.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = verify_deployed_load_posture(
        base_url=args.base_url,
        expected_environment=args.expected_environment,
        expected_release_version=args.expected_release_version,
        admin_bearer_token=args.admin_bearer_token,
        branch_bearer_token=args.branch_bearer_token,
        tenant_id=args.tenant_id,
        branch_id=args.branch_id,
        product_id=args.product_id,
        output_path=Path(args.output_path),
        concurrency=args.concurrency,
        iterations_per_worker=args.iterations_per_worker,
    )
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
