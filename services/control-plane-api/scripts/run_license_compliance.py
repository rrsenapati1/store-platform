from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


SERVICE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from store_control_plane.license_compliance import run_license_compliance


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Store release license-compliance evaluation from SBOM artifacts.")
    parser.add_argument("--sbom-report", required=True, help="JSON SBOM report path produced by generate_sbom_bundle.py.")
    parser.add_argument("--output-path", required=True, help="JSON file path for the generated license-compliance report.")
    parser.add_argument(
        "--policy-path",
        default=str(REPO_ROOT / "docs" / "launch" / "security" / "license-policy.json"),
        help="JSON license policy path. Defaults to docs/launch/security/license-policy.json.",
    )
    parser.add_argument(
        "--exceptions-path",
        default=str(REPO_ROOT / "docs" / "launch" / "security" / "license-exceptions.json"),
        help="JSON file containing approved license exceptions. Defaults to docs/launch/security/license-exceptions.json.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run_license_compliance(
        sbom_report_path=Path(args.sbom_report),
        output_path=Path(args.output_path),
        policy_path=Path(args.policy_path) if args.policy_path else None,
        exceptions_path=Path(args.exceptions_path) if args.exceptions_path else None,
    )
    print(json.dumps(result, indent=2))
    return 0 if result.get("status") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
