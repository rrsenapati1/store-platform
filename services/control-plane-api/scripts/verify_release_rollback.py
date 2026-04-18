from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import importlib.util
import sys
from pathlib import Path
from typing import Callable


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))


from store_control_plane.rollback_verification import (
    build_rollback_verification_report,
    load_release_bundle_manifest,
    write_rollback_verification_report,
)


VerifyCallable = Callable[..., dict[str, object]]


def _load_verify_script_module():
    script_path = SERVICE_ROOT / "scripts" / "verify_deployed_control_plane.py"
    spec = importlib.util.spec_from_file_location("verify_deployed_control_plane_script", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def verify_release_rollback(
    *,
    base_url: str,
    target_bundle_manifest_path: Path,
    output_path: Path,
    expected_environment: str | None = None,
    expected_release_version: str | None = None,
    bearer_token: str | None = None,
    generated_at: str | None = None,
    verify_deployed: VerifyCallable | None = None,
) -> dict[str, object]:
    verification = verify_deployed or _load_verify_script_module().verify_deployed_control_plane
    deployed_result = verification(
        base_url=base_url,
        expected_environment=expected_environment,
        expected_release_version=expected_release_version,
        bearer_token=bearer_token,
    )
    current_release_version = str(deployed_result.get("release_version") or "")
    current_alembic_head = str(deployed_result.get("alembic_head") or "")
    if not current_release_version:
        raise ValueError("deployed verification did not report release_version")
    if not current_alembic_head:
        raise ValueError("deployed verification did not report alembic_head")

    target_manifest = load_release_bundle_manifest(target_bundle_manifest_path)
    report = build_rollback_verification_report(
        environment=str(deployed_result.get("environment") or expected_environment or ""),
        current_release_version=current_release_version,
        current_alembic_head=current_alembic_head,
        target_manifest=target_manifest,
        generated_at=generated_at or datetime.now(timezone.utc).isoformat(),
    )
    write_rollback_verification_report(report, output_path=output_path)
    payload = report.to_dict()
    payload["output_path"] = str(output_path)
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify Store control-plane rollback eligibility against a target release bundle manifest.")
    parser.add_argument("--base-url", required=True, help="Public control-plane base URL, for example https://control.store.korsenex.com")
    parser.add_argument("--target-bundle-manifest", required=True, help="Path to the target control-plane bundle manifest JSON.")
    parser.add_argument("--output-path", required=True, help="JSON file path for the generated rollback verification report.")
    parser.add_argument("--expected-environment", help="Expected deployment environment label such as staging or prod.")
    parser.add_argument("--expected-release-version", help="Expected currently deployed release version.")
    parser.add_argument("--bearer-token", help="Optional bearer token used by verify_deployed_control_plane.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = verify_release_rollback(
        base_url=args.base_url,
        target_bundle_manifest_path=Path(args.target_bundle_manifest),
        output_path=Path(args.output_path),
        expected_environment=args.expected_environment,
        expected_release_version=args.expected_release_version,
        bearer_token=args.bearer_token,
    )
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
