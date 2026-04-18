from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))


from store_control_plane.config import Settings
from store_control_plane.ops.release_evidence_retrieval import verify_retained_release_evidence


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download and verify retained Store control-plane release evidence from object storage.")
    parser.add_argument("--environment", required=True, help="Release environment label such as staging or prod.")
    parser.add_argument("--release-version", required=True, help="Release version to verify from retained evidence.")
    parser.add_argument("--output-dir", required=True, help="Local directory used to download retained artifacts for verification.")
    parser.add_argument("--report-path", help="Optional JSON path for the retrieval verification report. Defaults under --output-dir.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    report = verify_retained_release_evidence(
        settings=Settings(),
        environment=args.environment,
        release_version=args.release_version,
        output_root=output_dir,
    )
    report_path = (
        Path(args.report_path)
        if args.report_path
        else output_dir / f"{args.environment}-{args.release_version}.retrieval-verification.json"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = report.to_dict()
    payload["report_path"] = str(report_path)
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if report.status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
