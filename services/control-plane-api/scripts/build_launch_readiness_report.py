from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from store_control_plane.launch_readiness import build_launch_readiness_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the V2 launch-readiness report from a structured beta/sign-off manifest and the strict release-gate report."
    )
    parser.add_argument("--launch-manifest", required=True, help="JSON manifest describing pilots, known issues, and sign-offs.")
    parser.add_argument("--release-gate-report", required=True, help="JSON report produced by run_release_gate.py.")
    parser.add_argument("--output-path", help="JSON output path for the launch-readiness report.")
    parser.add_argument("--markdown-output-path", help="Optional Markdown companion output path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_path = (
        Path(args.output_path)
        if args.output_path
        else Path(args.launch_manifest).with_name("launch-readiness-report.json")
    )
    result = build_launch_readiness_report(
        manifest_path=Path(args.launch_manifest),
        release_gate_report_path=Path(args.release_gate_report),
        output_path=output_path,
        markdown_output_path=Path(args.markdown_output_path) if args.markdown_output_path else None,
        generated_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    )
    print(json.dumps(result, indent=2))
    return 0 if result.get("status") == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
