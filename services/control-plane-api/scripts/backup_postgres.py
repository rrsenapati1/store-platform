from __future__ import annotations

import argparse
import sys
from pathlib import Path

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from store_control_plane.config import Settings
from store_control_plane.ops import run_postgres_backup


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create and upload a Store control-plane Postgres backup.")
    parser.add_argument(
        "--output-dir",
        default=str(SERVICE_ROOT / ".artifacts" / "postgres-backups"),
        help="Directory to stage the local dump and metadata manifest before upload.",
    )
    parser.add_argument("--alembic-head", help="Override the Alembic head stored in backup metadata.")
    parser.add_argument("--pg-dump-command", default="pg_dump", help="Override the pg_dump executable path.")
    parser.add_argument("--dry-run", action="store_true", help="Write metadata only and skip pg_dump or upload.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = Settings()
    plan = run_postgres_backup(
        settings,
        output_root=Path(args.output_dir),
        alembic_head=args.alembic_head,
        dry_run=args.dry_run,
        pg_dump_command=args.pg_dump_command,
    )
    print(f"[postgres-backup] bucket={plan.bucket} dump_key={plan.dump_key} metadata_key={plan.metadata_key}")


if __name__ == "__main__":
    main()
