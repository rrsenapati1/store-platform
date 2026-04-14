from __future__ import annotations

import argparse
import sys
from pathlib import Path

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from store_control_plane.config import Settings
from store_control_plane.ops import execute_release_deployment


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Deploy a Store control-plane release bundle on the target app VM.")
    parser.add_argument("--release-bundle", required=True, help="Path to the prepared release artifact on the app VM.")
    parser.add_argument("--dry-run", action="store_true", help="Print the deployment plan without executing backup, migrations, or restarts.")
    parser.add_argument("--yes", action="store_true", help="Confirm the deployment for a non-dry-run execution.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.dry_run and not args.yes:
        raise SystemExit("Refusing deployment without --yes or --dry-run.")

    settings = Settings()
    plan = execute_release_deployment(
        settings,
        release_bundle_path=Path(args.release_bundle),
        backup_executor=lambda: print("[deploy-control-plane-release] pre-migration backup required"),
        command_runner=lambda command: print(f"[deploy-control-plane-release] {' '.join(command)}"),
        dry_run=args.dry_run,
    )
    print(
        "[deploy-control-plane-release]",
        f"release_bundle={plan.release_bundle_path}",
        f"environment={settings.deployment_environment}",
    )


if __name__ == "__main__":
    main()
