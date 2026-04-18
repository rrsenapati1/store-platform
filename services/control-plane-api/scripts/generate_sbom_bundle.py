from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from store_control_plane.sbom_generation import generate_sbom_bundle  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate normalized SBOM evidence for Store release surfaces.")
    parser.add_argument("--output-path", required=True, help="JSON report path for the generated SBOM summary report.")
    parser.add_argument("--raw-output-dir", help="Optional directory for raw CycloneDX artifacts. Defaults beside the report.")
    parser.add_argument("--image-ref", action="append", default=[], help="Optional container image reference to include in the SBOM bundle.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = generate_sbom_bundle(
        output_path=Path(args.output_path),
        raw_output_dir=Path(args.raw_output_dir) if args.raw_output_dir else None,
        image_refs=list(args.image_ref or []),
    )
    print(json.dumps(result, indent=2))
    return 0 if result.get("status") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
