from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from store_control_plane.config import Settings
from store_control_plane.ops.release_evidence_retention import run_release_evidence_retention


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Upload a published Store release evidence pack to object storage.")
    parser.add_argument("--publication-dir", required=True, help="Directory produced by publish_release_evidence_bundle.py.")
    parser.add_argument("--environment", required=True, help="Deployment environment label such as staging or prod.")
    parser.add_argument("--release-version", required=True, help="Release version associated with the publication.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        plan = run_release_evidence_retention(
            Settings(),
            publication_dir=Path(args.publication_dir),
            environment=args.environment,
            release_version=args.release_version,
        )
    except Exception as exc:  # pragma: no cover - exercised through CLI contract tests
        print(str(exc), file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "status": "retained",
                "bucket": plan.bucket,
                "archive_key": plan.archive_key,
                "publication_manifest_key": plan.publication_manifest_key,
                "catalog_key": plan.catalog_key,
                "retention_manifest_key": plan.retention_manifest_key,
                "retention_manifest_path": str(plan.retention_manifest_path),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
