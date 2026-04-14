from __future__ import annotations

import argparse
import sys
from pathlib import Path

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from store_control_plane.config import Settings
from store_control_plane.ops import run_postgres_restore


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Restore a Store control-plane Postgres backup from object storage.")
    parser.add_argument("--dump-key", required=True, help="Object-storage key for the backup dump artifact.")
    parser.add_argument("--metadata-key", required=True, help="Object-storage key for the backup metadata manifest.")
    parser.add_argument("--target-database-url", required=True, help="Target Postgres database URL to restore into.")
    parser.add_argument(
        "--output-dir",
        default=str(SERVICE_ROOT / ".artifacts" / "postgres-restore"),
        help="Directory to stage downloaded dump and metadata files.",
    )
    parser.add_argument("--pg-restore-command", default="pg_restore", help="Override the pg_restore executable path.")
    parser.add_argument("--allow-environment-mismatch", action="store_true", help="Bypass environment metadata safety checks.")
    parser.add_argument("--dry-run", action="store_true", help="Download and validate artifacts but skip pg_restore.")
    parser.add_argument("--yes", action="store_true", help="Confirm the restore for a non-dry-run execution.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.dry_run and not args.yes:
        raise SystemExit("Refusing destructive restore without --yes or --dry-run.")

    settings = Settings()
    plan = run_postgres_restore(
        settings,
        dump_key=args.dump_key,
        metadata_key=args.metadata_key,
        output_root=Path(args.output_dir),
        target_database_url=args.target_database_url,
        dry_run=args.dry_run,
        pg_restore_command=args.pg_restore_command,
        allow_environment_mismatch=args.allow_environment_mismatch,
    )
    print(
        "[postgres-restore]",
        f"bucket={plan.bucket}",
        f"dump_key={plan.dump_key}",
        f"target_database_url={plan.target_database_url}",
    )


if __name__ == "__main__":
    main()
