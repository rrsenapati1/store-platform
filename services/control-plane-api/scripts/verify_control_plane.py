from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve()
SERVICE_ROOT = SCRIPT_PATH.parents[1]
REPO_ROOT = SCRIPT_PATH.parents[3]

if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from store_control_plane.config import build_settings
from store_control_plane.verification import run_control_plane_smoke


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Store control-plane verification stack.")
    parser.add_argument("--database-url", help="Override STORE_CONTROL_PLANE_DATABASE_URL for verification.")
    parser.add_argument("--platform-admin-email", default="admin@store.local", help="Platform admin email for the smoke flow.")
    parser.add_argument("--skip-alembic", action="store_true", help="Skip Alembic upgrade.")
    parser.add_argument("--skip-backend-tests", action="store_true", help="Skip control-plane pytest suite.")
    parser.add_argument("--skip-frontend-tests", action="store_true", help="Skip workspace app-flow tests.")
    parser.add_argument("--skip-typecheck", action="store_true", help="Skip workspace typecheck.")
    parser.add_argument("--skip-build", action="store_true", help="Skip workspace build.")
    return parser.parse_args()


def run_command(command: list[str], *, cwd: Path, env: dict[str, str]) -> None:
    resolved = command[:]
    if os.name == "nt" and resolved[0] == "npm":
        resolved[0] = "npm.cmd"
    print(f"> {' '.join(resolved)}", flush=True)
    subprocess.run(resolved, cwd=str(cwd), env=env, check=True)


def main() -> int:
    args = parse_args()
    settings = build_settings(database_url=args.database_url)
    env = os.environ.copy()
    env["STORE_CONTROL_PLANE_DATABASE_URL"] = settings.database_url
    verification_temp_root = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "store-control-plane-verification"
    verification_temp_root.mkdir(exist_ok=True)
    env["TMP"] = str(verification_temp_root)
    env["TEMP"] = str(verification_temp_root)
    env["TMPDIR"] = str(verification_temp_root)
    pytest_base_temp = verification_temp_root / "pytest"
    pytest_base_temp.mkdir(parents=True, exist_ok=True)

    if not args.skip_alembic:
        run_command(
            [sys.executable, "-m", "alembic", "-c", "alembic.ini", "upgrade", "head"],
            cwd=SERVICE_ROOT,
            env=env,
        )

    if not args.skip_backend_tests:
        run_command(
            [sys.executable, "-m", "pytest", "tests", "-q", f"--basetemp={pytest_base_temp.as_posix()}"],
            cwd=SERVICE_ROOT,
            env=env,
        )

    if not args.skip_frontend_tests:
        for workspace in ("@store/platform-admin", "@store/owner-web", "@store/store-desktop"):
            run_command(
                ["npm", "run", "test", "--workspace", workspace],
                cwd=REPO_ROOT,
                env=env,
            )

    if not args.skip_typecheck:
        run_command(["npm", "run", "typecheck"], cwd=REPO_ROOT, env=env)

    if not args.skip_build:
        run_command(["npm", "run", "build"], cwd=REPO_ROOT, env=env)

    smoke_result = run_control_plane_smoke(
        database_url=settings.database_url,
        platform_admin_email=args.platform_admin_email,
    )
    print(json.dumps(smoke_result.to_dict(), indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
