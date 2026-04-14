from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Callable


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))


def _load_verify_script_module():
    script_path = SERVICE_ROOT / "scripts" / "verify_deployed_control_plane.py"
    spec = importlib.util.spec_from_file_location("verify_deployed_control_plane_script", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


VerifyDeployedCallable = Callable[..., dict[str, object]]


def certify_release_candidate(
    *,
    base_url: str,
    expected_environment: str | None = None,
    expected_release_version: str | None = None,
    bearer_token: str | None = None,
    verify_deployed: VerifyDeployedCallable | None = None,
) -> dict[str, object]:
    verification = verify_deployed or _load_verify_script_module().verify_deployed_control_plane
    deployed = verification(
        base_url=base_url,
        expected_environment=expected_environment,
        expected_release_version=expected_release_version,
        bearer_token=bearer_token,
    )

    environment = deployed.get("environment")
    release_version = deployed.get("release_version")
    legacy_write_mode = deployed.get("legacy_write_mode")
    legacy_remaining_domains = list(deployed.get("legacy_remaining_domains") or [])
    status = deployed.get("status")

    gates = {
      "health_ok": status == "ok",
      "environment_match": not expected_environment or environment == expected_environment,
      "release_version_match": not expected_release_version or release_version == expected_release_version,
      "legacy_write_mode_cutover": legacy_write_mode == "cutover",
      "legacy_remaining_domains_cleared": len(legacy_remaining_domains) == 0,
    }
    overall_status = "approved" if all(gates.values()) else "blocked"
    return {
      "status": overall_status,
      "environment": environment,
      "release_version": release_version,
      "legacy_write_mode": legacy_write_mode,
      "legacy_remaining_domains": legacy_remaining_domains,
      "gates": gates,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Certify a Store release candidate from deployed control-plane evidence.")
    parser.add_argument("--base-url", required=True, help="Public control-plane base URL, for example https://control.store.korsenex.com")
    parser.add_argument("--expected-environment", help="Expected deployment environment label such as staging or prod.")
    parser.add_argument("--expected-release-version", help="Expected release version reported by the deployment.")
    parser.add_argument("--bearer-token", help="Optional bearer token used to verify /v1/auth/me against the deployment.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = certify_release_candidate(
        base_url=args.base_url,
        expected_environment=args.expected_environment,
        expected_release_version=args.expected_release_version,
        bearer_token=args.bearer_token,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
