from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import sys
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))


from store_control_plane.config import build_settings
from store_control_plane.performance_validation import (
    build_performance_report,
    launch_foundation_budgets,
    summarize_performance_report,
    write_performance_report,
)
from store_control_plane.performance_workloads import run_launch_foundation_workloads


def run_performance_validation(
    *,
    database_url: str | None = None,
    iterations: int = 3,
    output_path: Path,
    generated_at: str | None = None,
) -> dict[str, object]:
    settings = build_settings(database_url=database_url)
    scenario_samples = run_launch_foundation_workloads(
        database_url=settings.database_url,
        iterations=iterations,
    )
    report = build_performance_report(
        scenario_set="launch-foundation",
        budgets=launch_foundation_budgets(),
        scenario_samples=scenario_samples,
        generated_at=generated_at or datetime.now(timezone.utc).isoformat(),
    )
    write_performance_report(report, output_path=output_path)
    payload = report.to_dict()
    payload["command"] = f"python services/control-plane-api/scripts/validate_performance_foundation.py --iterations {iterations} --output-path {output_path}"
    payload["summary"] = summarize_performance_report(report)
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Store V2 performance validation against the launch-foundation scenario set.")
    parser.add_argument("--database-url", help="Override STORE_CONTROL_PLANE_DATABASE_URL for validation.")
    parser.add_argument("--iterations", type=int, default=3, help="Iterations to run for each launch-foundation scenario.")
    parser.add_argument("--output-path", help="JSON file path for the generated performance report.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_path = Path(args.output_path) if args.output_path else (
        SERVICE_ROOT.parents[1] / "docs" / "launch" / "evidence" / "performance-launch-foundation.json"
    )
    result = run_performance_validation(
        database_url=args.database_url,
        iterations=args.iterations,
        output_path=output_path,
    )
    print(json.dumps(result, indent=2))
    if result["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
