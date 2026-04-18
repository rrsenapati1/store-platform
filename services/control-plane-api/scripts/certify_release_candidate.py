from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Callable


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))


def _load_verify_script_module():
    script_path = SERVICE_ROOT / "scripts" / "verify_deployed_control_plane.py"
    spec = importlib.util.spec_from_file_location("verify_deployed_control_plane_script", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


VerifyDeployedCallable = Callable[..., dict[str, object]]


def certify_release_candidate(
    *,
    base_url: str,
    expected_environment: str | None = None,
    expected_release_version: str | None = None,
    bearer_token: str | None = None,
    performance_result: dict[str, object] | None = None,
    operational_alert_result: dict[str, object] | None = None,
    environment_drift_result: dict[str, object] | None = None,
    tls_posture_result: dict[str, object] | None = None,
    sbom_result: dict[str, object] | None = None,
    provenance_result: dict[str, object] | None = None,
    deployed_load_result: dict[str, object] | None = None,
    rollback_result: dict[str, object] | None = None,
    vulnerability_scan_result: dict[str, object] | None = None,
    require_operational_alerts: bool = True,
    require_environment_drift: bool = True,
    require_tls_posture: bool = True,
    require_sbom: bool = True,
    require_provenance: bool = True,
    require_deployed_load: bool = False,
    require_rollback_verification: bool = False,
    require_vulnerability_scan: bool = True,
    verify_deployed: VerifyDeployedCallable | None = None,
) -> dict[str, object]:
    verification = verify_deployed or _load_verify_script_module().verify_deployed_control_plane
    deployed = verification(
        base_url=base_url,
        expected_environment=expected_environment,
        expected_release_version=expected_release_version,
        bearer_token=bearer_token,
    )

    environment = deployed.get("environment")
    release_version = deployed.get("release_version")
    legacy_write_mode = deployed.get("legacy_write_mode")
    legacy_remaining_domains = list(deployed.get("legacy_remaining_domains") or [])
    security_result = dict(deployed.get("security_result") or {})
    status = deployed.get("status")

    gates = {
      "health_ok": status == "ok",
      "environment_match": not expected_environment or environment == expected_environment,
      "release_version_match": not expected_release_version or release_version == expected_release_version,
      "legacy_write_mode_cutover": legacy_write_mode == "cutover",
      "legacy_remaining_domains_cleared": len(legacy_remaining_domains) == 0,
      "security_controls_verified": not security_result or security_result.get("status") == "passed",
      "performance_budgets_passed": performance_result is None or performance_result.get("status") == "passed",
      "operational_alerts_verified": (not require_operational_alerts) or (
          operational_alert_result is not None and operational_alert_result.get("status") == "passed"
      ),
      "environment_drift_verified": (not require_environment_drift) or (
          environment_drift_result is not None and environment_drift_result.get("status") == "passed"
      ),
      "tls_posture_verified": (not require_tls_posture) or (
          tls_posture_result is not None and tls_posture_result.get("status") == "passed"
      ),
      "sbom_verified": (not require_sbom) or (
          sbom_result is not None and sbom_result.get("status") == "passed"
      ),
      "provenance_verified": (not require_provenance) or (
          provenance_result is not None and provenance_result.get("status") == "passed"
      ),
      "deployed_load_verified": (
          deployed_load_result.get("status") == "passed"
          if deployed_load_result is not None
          else not require_deployed_load
      ),
      "rollback_verified": (
          rollback_result.get("status") == "passed"
          if rollback_result is not None
          else not require_rollback_verification
      ),
      "vulnerability_scans_passed": (not require_vulnerability_scan) or (
          vulnerability_scan_result is not None and vulnerability_scan_result.get("status") == "passed"
      ),
    }
    overall_status = "approved" if all(gates.values()) else "blocked"
    return {
      "status": overall_status,
      "environment": environment,
      "release_version": release_version,
      "legacy_write_mode": legacy_write_mode,
      "legacy_remaining_domains": legacy_remaining_domains,
      "security_result_status": security_result.get("status"),
      "performance_result_status": None if performance_result is None else performance_result.get("status"),
      "performance_failing_scenarios": [] if performance_result is None else list(performance_result.get("failing_scenarios") or []),
      "operational_alert_result_status": None if operational_alert_result is None else operational_alert_result.get("status"),
      "operational_alert_failing_checks": [] if operational_alert_result is None else list(operational_alert_result.get("failing_checks") or []),
      "environment_drift_result_status": None if environment_drift_result is None else environment_drift_result.get("status"),
      "environment_drift_failing_checks": [] if environment_drift_result is None else list(environment_drift_result.get("failing_checks") or []),
      "tls_posture_result_status": None if tls_posture_result is None else tls_posture_result.get("status"),
      "tls_posture_failing_checks": [] if tls_posture_result is None else list(tls_posture_result.get("failing_checks") or []),
      "sbom_result_status": None if sbom_result is None else sbom_result.get("status"),
      "sbom_failing_surfaces": [] if sbom_result is None else list(sbom_result.get("failing_surfaces") or []),
      "provenance_result_status": None if provenance_result is None else provenance_result.get("status"),
      "provenance_failure_reason": None if provenance_result is None else provenance_result.get("failure_reason"),
      "deployed_load_result_status": None if deployed_load_result is None else deployed_load_result.get("status"),
      "deployed_load_failing_scenarios": [] if deployed_load_result is None else list(deployed_load_result.get("failing_scenarios") or []),
      "rollback_result_status": None if rollback_result is None else rollback_result.get("status"),
      "rollback_failure_reason": None if rollback_result is None else rollback_result.get("failure_reason"),
      "vulnerability_result_status": None if vulnerability_scan_result is None else vulnerability_scan_result.get("status"),
      "vulnerability_failing_surfaces": [] if vulnerability_scan_result is None else list(vulnerability_scan_result.get("failing_surfaces") or []),
      "gates": gates,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Certify a Store release candidate from deployed control-plane evidence.")
    parser.add_argument("--base-url", required=True, help="Public control-plane base URL, for example https://control.store.korsenex.com")
    parser.add_argument("--expected-environment", help="Expected deployment environment label such as staging or prod.")
    parser.add_argument("--expected-release-version", help="Expected release version reported by the deployment.")
    parser.add_argument("--bearer-token", help="Optional bearer token used to verify /v1/auth/me against the deployment.")
    parser.add_argument("--performance-report", help="Optional JSON performance report path produced by validate_performance_foundation.py.")
    parser.add_argument("--operational-alert-report", help="Optional JSON operational alert report path produced by verify_operational_alert_posture.py.")
    parser.add_argument("--environment-drift-report", help="Optional JSON environment drift report path produced by verify_environment_drift.py.")
    parser.add_argument("--tls-posture-report", help="Optional JSON TLS posture report path produced by verify_tls_posture.py.")
    parser.add_argument("--sbom-report", help="Optional JSON SBOM report path produced by generate_sbom_bundle.py.")
    parser.add_argument("--provenance-report", help="Optional JSON provenance report path produced by package-control-plane-release.mjs.")
    parser.add_argument("--deployed-load-report", help="Optional JSON deployed load report path produced by verify_deployed_load_posture.py.")
    parser.add_argument("--rollback-report", help="Optional JSON rollback verification report path produced by verify_release_rollback.py.")
    parser.add_argument("--vulnerability-scan-report", help="Optional JSON vulnerability report path produced by run_vulnerability_scans.py.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    performance_result = None
    if args.performance_report:
        performance_result = json.loads(Path(args.performance_report).read_text(encoding="utf-8"))
    operational_alert_result = None
    if args.operational_alert_report:
        operational_alert_result = json.loads(Path(args.operational_alert_report).read_text(encoding="utf-8"))
    environment_drift_result = None
    if args.environment_drift_report:
        environment_drift_result = json.loads(Path(args.environment_drift_report).read_text(encoding="utf-8"))
    tls_posture_result = None
    if args.tls_posture_report:
        tls_posture_result = json.loads(Path(args.tls_posture_report).read_text(encoding="utf-8"))
    sbom_result = None
    if args.sbom_report:
        sbom_result = json.loads(Path(args.sbom_report).read_text(encoding="utf-8"))
    provenance_result = None
    if args.provenance_report:
        provenance_result = json.loads(Path(args.provenance_report).read_text(encoding="utf-8"))
    deployed_load_result = None
    if args.deployed_load_report:
        deployed_load_result = json.loads(Path(args.deployed_load_report).read_text(encoding="utf-8"))
    rollback_result = None
    if args.rollback_report:
        rollback_result = json.loads(Path(args.rollback_report).read_text(encoding="utf-8"))
    vulnerability_scan_result = None
    if args.vulnerability_scan_report:
        vulnerability_scan_result = json.loads(Path(args.vulnerability_scan_report).read_text(encoding="utf-8"))
    result = certify_release_candidate(
        base_url=args.base_url,
        expected_environment=args.expected_environment,
        expected_release_version=args.expected_release_version,
        bearer_token=args.bearer_token,
        performance_result=performance_result,
        operational_alert_result=operational_alert_result,
        environment_drift_result=environment_drift_result,
        tls_posture_result=tls_posture_result,
        sbom_result=sbom_result,
        provenance_result=provenance_result,
        deployed_load_result=deployed_load_result,
        rollback_result=rollback_result,
        vulnerability_scan_result=vulnerability_scan_result,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
