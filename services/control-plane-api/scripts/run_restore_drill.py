from __future__ import annotations

import argparse
import sys
from pathlib import Path

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from store_control_plane.config import Settings
from store_control_plane.ops import run_postgres_restore_drill, write_restore_drill_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a Store control-plane Postgres restore drill and write a JSON recovery report."
    )
    parser.add_argument("--dump-key", required=True, help="Object-storage key for the backup dump artifact.")
    parser.add_argument("--metadata-key", required=True, help="Object-storage key for the backup metadata manifest.")
    parser.add_argument("--target-database-url", required=True, help="Target Postgres database URL to restore into.")
    parser.add_argument("--output-path", required=True, help="JSON path for the restore-drill report.")
    parser.add_argument("--allow-environment-mismatch", action="store_true", help="Bypass environment metadata safety checks.")
    parser.add_argument("--verify-smoke", action="store_true", help="Run bounded control-plane smoke verification after health succeeds.")
    parser.add_argument("--yes", action="store_true", help="Confirm the destructive restore drill.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.yes:
        raise SystemExit("Refusing destructive restore drill without --yes.")

    settings = Settings()
    output_path = Path(args.output_path)
    output_root = output_path.parent / f"{output_path.stem}-artifacts"
    report = run_postgres_restore_drill(
        settings=settings,
        dump_key=args.dump_key,
        metadata_key=args.metadata_key,
        output_root=output_root,
        target_database_url=args.target_database_url,
        verify_smoke=args.verify_smoke,
        allow_environment_mismatch=args.allow_environment_mismatch,
    )
    write_restore_drill_report(report, output_path)
    print(
        "[restore-drill]",
        f"status={report.status}",
        f"dump_key={args.dump_key}",
        f"output_path={output_path}",
    )
    return 0 if report.status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
