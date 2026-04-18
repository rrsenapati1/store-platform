from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))


from store_control_plane.launch_gate_orchestration import run_v2_launch_gate


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the full V2 launch gate: strict technical gate, launch readiness, publication, and optional retained-evidence verification.")
    parser.add_argument("--base-url", required=True, help="Public control-plane base URL, for example https://control.store.korsenex.com")
    parser.add_argument("--expected-environment", required=True, help="Expected deployment environment label such as staging or prod.")
    parser.add_argument("--expected-release-version", required=True, help="Expected deployed release version.")
    parser.add_argument("--release-owner", required=True, help="Release owner recorded in the launch output.")
    parser.add_argument("--output-dir", required=True, help="Directory where the V2 launch-gate reports and artifacts will be written.")
    parser.add_argument("--launch-manifest", required=True, help="JSON launch-readiness manifest containing pilot evidence, issues, and sign-offs.")
    parser.add_argument("--admin-bearer-token", required=True, help="Bearer token with observability-summary access.")
    parser.add_argument("--branch-bearer-token", required=True, help="Bearer token with branch-safe checkout preview and dashboard access.")
    parser.add_argument("--tenant-id", required=True, help="Fixture tenant identifier for deployed-load scenarios.")
    parser.add_argument("--branch-id", required=True, help="Fixture branch identifier for deployed-load scenarios.")
    parser.add_argument("--product-id", required=True, help="Fixture product identifier for deployed-load scenarios.")
    parser.add_argument("--dump-key", required=True, help="Object-storage key for the restore-drill backup dump artifact.")
    parser.add_argument("--metadata-key", required=True, help="Object-storage key for the restore-drill metadata manifest.")
    parser.add_argument("--target-database-url", required=True, help="Target Postgres database URL used for the restore drill.")
    parser.add_argument("--bearer-token", help="Optional bearer token for deployed verification calls.")
    parser.add_argument("--image-ref", action="append", default=[], help="Container image reference to include in vulnerability and SBOM scans.")
    parser.add_argument("--vulnerability-exceptions-path", help="Optional JSON file containing approved vulnerability exceptions.")
    parser.add_argument("--retain-evidence-offsite", action="store_true", help="Upload the published launch evidence pack to configured object storage.")
    parser.add_argument("--verify-retained-evidence", action="store_true", help="Download retained launch evidence back from object storage and verify it.")
    parser.add_argument("--verify-smoke-restore-drill", action="store_true", help="Run bounded smoke verification after restore-drill health succeeds.")
    parser.add_argument("--allow-restore-environment-mismatch", action="store_true", help="Bypass restore-drill environment metadata safety checks.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run_v2_launch_gate(
        base_url=args.base_url,
        expected_environment=args.expected_environment,
        expected_release_version=args.expected_release_version,
        release_owner=args.release_owner,
        output_dir=Path(args.output_dir),
        launch_manifest_path=Path(args.launch_manifest),
        admin_bearer_token=args.admin_bearer_token,
        branch_bearer_token=args.branch_bearer_token,
        tenant_id=args.tenant_id,
        branch_id=args.branch_id,
        product_id=args.product_id,
        dump_key=args.dump_key,
        metadata_key=args.metadata_key,
        target_database_url=args.target_database_url,
        bearer_token=args.bearer_token,
        image_refs=list(args.image_ref or []),
        vulnerability_exceptions_path=Path(args.vulnerability_exceptions_path) if args.vulnerability_exceptions_path else None,
        retain_evidence_offsite=args.retain_evidence_offsite,
        verify_retained_evidence=args.verify_retained_evidence,
        verify_smoke_restore_drill=args.verify_smoke_restore_drill,
        allow_restore_environment_mismatch=args.allow_restore_environment_mismatch,
    )
    print(json.dumps(result, indent=2))
    return 0 if result.get("status") == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
