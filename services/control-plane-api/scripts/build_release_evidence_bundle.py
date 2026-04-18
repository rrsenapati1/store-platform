from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))


from store_control_plane.release_evidence_bundle import build_release_evidence_bundle


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Assemble a deterministic Store release evidence bundle.")
    parser.add_argument("--output-dir", required=True, help="Output directory for the assembled evidence bundle.")
    parser.add_argument("--release-evidence", required=True, help="Markdown evidence path produced by generate_release_candidate_evidence.py.")
    parser.add_argument("--certification-report", help="Optional JSON report path for certify_release_candidate.py output.")
    parser.add_argument("--performance-report", help="Optional JSON performance report path.")
    parser.add_argument("--operational-alert-report", help="Optional JSON operational alert report path.")
    parser.add_argument("--environment-drift-report", help="Optional JSON environment drift report path.")
    parser.add_argument("--tls-posture-report", help="Optional JSON TLS posture report path.")
    parser.add_argument("--sbom-report", help="Optional JSON SBOM report path.")
    parser.add_argument("--provenance-report", help="Optional JSON provenance report path.")
    parser.add_argument("--license-compliance-report", help="Optional JSON license compliance report path.")
    parser.add_argument("--deployed-load-report", help="Optional JSON deployed load report path.")
    parser.add_argument("--rollback-report", help="Optional JSON rollback verification report path.")
    parser.add_argument("--vulnerability-scan-report", help="Optional JSON vulnerability report path.")
    parser.add_argument("--restore-drill-report", help="Optional JSON restore-drill report path.")
    parser.add_argument("--launch-readiness-report", help="Optional JSON launch-readiness report path.")
    parser.add_argument("--launch-manifest", help="Optional JSON launch-readiness manifest path.")
    parser.add_argument("--sbom-artifact-dir", help="Optional directory containing raw SBOM artifacts.")
    parser.add_argument("--vulnerability-raw-output-dir", help="Optional directory containing raw vulnerability scan output.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = build_release_evidence_bundle(
        output_dir=Path(args.output_dir),
        report_paths={
            "release_candidate_evidence": Path(args.release_evidence),
            "certification_report": Path(args.certification_report) if args.certification_report else None,
            "performance_report": Path(args.performance_report) if args.performance_report else None,
            "operational_alert_report": Path(args.operational_alert_report) if args.operational_alert_report else None,
            "environment_drift_report": Path(args.environment_drift_report) if args.environment_drift_report else None,
            "tls_posture_report": Path(args.tls_posture_report) if args.tls_posture_report else None,
            "sbom_report": Path(args.sbom_report) if args.sbom_report else None,
            "provenance_report": Path(args.provenance_report) if args.provenance_report else None,
            "license_compliance_report": Path(args.license_compliance_report) if args.license_compliance_report else None,
            "deployed_load_report": Path(args.deployed_load_report) if args.deployed_load_report else None,
            "rollback_report": Path(args.rollback_report) if args.rollback_report else None,
            "vulnerability_scan_report": Path(args.vulnerability_scan_report) if args.vulnerability_scan_report else None,
            "restore_drill_report": Path(args.restore_drill_report) if args.restore_drill_report else None,
            "launch_readiness_report": Path(args.launch_readiness_report) if args.launch_readiness_report else None,
            "launch_readiness_manifest": Path(args.launch_manifest) if args.launch_manifest else None,
        },
        directory_paths={
            "sbom_artifacts": Path(args.sbom_artifact_dir) if args.sbom_artifact_dir else None,
            "vulnerability_raw_output": Path(args.vulnerability_raw_output_dir) if args.vulnerability_raw_output_dir else None,
        },
    )
    print(json.dumps(result, indent=2))
    return 0 if result.get("status") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
