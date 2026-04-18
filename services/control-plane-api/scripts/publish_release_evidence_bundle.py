from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))


from store_control_plane.release_evidence_publication import publish_release_evidence_bundle


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Publish a Store release evidence bundle into an archived retention pack.")
    parser.add_argument("--bundle-dir", required=True, help="Existing evidence bundle directory produced by build_release_evidence_bundle.py or generate_release_candidate_evidence.py.")
    parser.add_argument("--output-dir", required=True, help="Output directory where archive, publication manifest, and catalog should be written.")
    parser.add_argument("--environment", required=True, help="Deployment environment label such as staging or prod.")
    parser.add_argument("--release-version", required=True, help="Release version associated with the evidence bundle.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = publish_release_evidence_bundle(
        bundle_dir=Path(args.bundle_dir),
        output_dir=Path(args.output_dir),
        release_version=args.release_version,
        environment=args.environment,
    )
    print(json.dumps(result, indent=2))
    return 0 if result.get("status") == "published" else 1


if __name__ == "__main__":
    raise SystemExit(main())
