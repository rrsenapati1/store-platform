from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Callable

from .config import Settings
from .ops.postgres_restore_drill import run_postgres_restore_drill, write_restore_drill_report


SERVICE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]

Runner = Callable[..., Any]


def _load_script_module(script_name: str, module_name: str):
    script_path = SERVICE_ROOT / "scripts" / script_name
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _as_payload(value: Any) -> dict[str, object]:
    if hasattr(value, "to_dict"):
        payload = value.to_dict()
        if isinstance(payload, dict):
            return payload
    if isinstance(value, dict):
        return value
    raise TypeError(f"unsupported result payload type: {type(value)!r}")


def write_release_gate_report(payload: dict[str, object], *, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output_path


def _default_package_release(*, release_version: str, output_dir: Path, node_command: str = "node") -> dict[str, object]:
    command = [
        node_command,
        str(REPO_ROOT / "scripts" / "package-control-plane-release.mjs"),
        "--version",
        release_version,
        "--output-dir",
        str(output_dir),
    ]
    completed = subprocess.run(
        command,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError((completed.stderr or completed.stdout).strip() or "control-plane release packaging failed")
    bundle_name = f"store-control-plane-{release_version}"
    archive_path = output_dir / f"{bundle_name}.tar.gz"
    manifest_path = output_dir / f"{bundle_name}.manifest.json"
    provenance_report_path = output_dir / f"{bundle_name}.provenance.json"
    for required_path in (archive_path, manifest_path, provenance_report_path):
        if not required_path.exists():
            raise FileNotFoundError(f"expected release packaging artifact missing: {required_path}")
    return {
        "archive_path": str(archive_path),
        "manifest_path": str(manifest_path),
        "provenance_report_path": str(provenance_report_path),
        "command": " ".join(command),
    }


def _default_restore_drill(
    *,
    settings: Settings,
    dump_key: str,
    metadata_key: str,
    target_database_url: str,
    output_path: Path,
    verify_smoke: bool,
    allow_environment_mismatch: bool,
) -> dict[str, object]:
    output_root = output_path.parent / f"{output_path.stem}-artifacts"
    report = run_postgres_restore_drill(
        settings=settings,
        dump_key=dump_key,
        metadata_key=metadata_key,
        output_root=output_root,
        target_database_url=target_database_url,
        verify_smoke=verify_smoke,
        allow_environment_mismatch=allow_environment_mismatch,
    )
    write_restore_drill_report(report, output_path)
    payload = report.to_dict()
    payload["output_path"] = str(output_path)
    return payload


def run_release_gate(
    *,
    base_url: str,
    expected_environment: str,
    expected_release_version: str,
    release_owner: str | None,
    output_dir: Path,
    admin_bearer_token: str,
    branch_bearer_token: str,
    tenant_id: str,
    branch_id: str,
    product_id: str,
    dump_key: str,
    metadata_key: str,
    target_database_url: str,
    bearer_token: str | None = None,
    image_refs: list[str] | None = None,
    vulnerability_exceptions_path: Path | None = None,
    retain_evidence_offsite: bool = False,
    verify_retained_evidence: bool = False,
    verify_smoke_restore_drill: bool = False,
    allow_restore_environment_mismatch: bool = False,
    settings_factory: Callable[[], Settings] | None = None,
    run_vulnerability_scans: Runner | None = None,
    verify_operational_alert_posture: Runner | None = None,
    verify_environment_drift: Runner | None = None,
    verify_tls_posture: Runner | None = None,
    generate_sbom_bundle: Runner | None = None,
    run_license_compliance: Runner | None = None,
    package_release: Runner | None = None,
    verify_deployed_load_posture: Runner | None = None,
    verify_release_rollback: Runner | None = None,
    run_restore_drill: Runner | None = None,
    generate_release_candidate_evidence: Runner | None = None,
    certify_release_candidate: Runner | None = None,
    verify_retained_release_evidence: Runner | None = None,
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    reports_dir = output_dir / "reports"
    raw_dir = output_dir / "raw"
    vulnerability_raw_dir = raw_dir / "vulnerability-scans"
    sbom_raw_dir = raw_dir / "sbom"
    release_bundle_dir = output_dir / "release-bundle"
    evidence_bundle_dir = output_dir / "evidence-bundle"
    publication_dir = output_dir / "published"
    retrieved_dir = output_dir / "retrieved" / f"{expected_environment}-{expected_release_version}"
    report_path = output_dir / "release-gate-report.json"

    vulnerability_scan_report_path = reports_dir / "vulnerability-scan-report.json"
    operational_alert_report_path = reports_dir / "operational-alert-report.json"
    environment_drift_report_path = reports_dir / "environment-drift-report.json"
    tls_posture_report_path = reports_dir / "tls-posture-report.json"
    sbom_report_path = reports_dir / "sbom-report.json"
    license_compliance_report_path = reports_dir / "license-compliance-report.json"
    deployed_load_report_path = reports_dir / "deployed-load-report.json"
    rollback_report_path = reports_dir / "rollback-report.json"
    restore_drill_report_path = reports_dir / "restore-drill-report.json"
    release_evidence_path = reports_dir / "release-candidate-evidence.md"
    certification_report_path = reports_dir / "certification-report.json"

    settings = (settings_factory or Settings)()
    effective_image_refs = list(image_refs or [])

    vulnerability_runner = run_vulnerability_scans or _load_script_module(
        "run_vulnerability_scans.py",
        "run_vulnerability_scans_script",
    ).run_vulnerability_scans
    alert_runner = verify_operational_alert_posture or _load_script_module(
        "verify_operational_alert_posture.py",
        "verify_operational_alert_posture_script",
    ).verify_operational_alert_posture
    environment_drift_runner = verify_environment_drift or _load_script_module(
        "verify_environment_drift.py",
        "verify_environment_drift_script",
    ).verify_environment_drift
    tls_runner = verify_tls_posture or _load_script_module(
        "verify_tls_posture.py",
        "verify_tls_posture_script",
    ).verify_tls_posture
    sbom_runner = generate_sbom_bundle or _load_script_module(
        "generate_sbom_bundle.py",
        "generate_sbom_bundle_script",
    ).generate_sbom_bundle
    license_runner = run_license_compliance or _load_script_module(
        "run_license_compliance.py",
        "run_license_compliance_script",
    ).run_license_compliance
    package_runner = package_release or _default_package_release
    deployed_load_runner = verify_deployed_load_posture or _load_script_module(
        "verify_deployed_load_posture.py",
        "verify_deployed_load_posture_script",
    ).verify_deployed_load_posture
    rollback_runner = verify_release_rollback or _load_script_module(
        "verify_release_rollback.py",
        "verify_release_rollback_script",
    ).verify_release_rollback
    evidence_generator = generate_release_candidate_evidence or _load_script_module(
        "generate_release_candidate_evidence.py",
        "generate_release_candidate_evidence_script",
    ).generate_release_candidate_evidence
    certifier = certify_release_candidate or _load_script_module(
        "certify_release_candidate.py",
        "certify_release_candidate_script",
    ).certify_release_candidate
    retrieval_runner = verify_retained_release_evidence or _load_script_module(
        "verify_retained_release_evidence.py",
        "verify_retained_release_evidence_script",
    ).verify_retained_release_evidence

    vulnerability_scan_result = _as_payload(
        vulnerability_runner(
            output_path=vulnerability_scan_report_path,
            exceptions_path=vulnerability_exceptions_path,
            image_refs=effective_image_refs,
            raw_output_dir=vulnerability_raw_dir,
        )
    )
    operational_alert_result = _as_payload(
        alert_runner(
            base_url=base_url,
            output_path=operational_alert_report_path,
            expected_environment=expected_environment,
            expected_release_version=expected_release_version,
        )
    )
    environment_drift_result = _as_payload(
        environment_drift_runner(
            base_url=base_url,
            expected_environment=expected_environment,
            expected_release_version=expected_release_version,
            output_path=environment_drift_report_path,
        )
    )
    tls_posture_result = _as_payload(
        tls_runner(
            base_url=base_url,
            output_path=tls_posture_report_path,
        )
    )
    sbom_result = _as_payload(
        sbom_runner(
            output_path=sbom_report_path,
            raw_output_dir=sbom_raw_dir,
            image_refs=effective_image_refs,
        )
    )
    license_compliance_result = _as_payload(
        license_runner(
            sbom_report_path=sbom_report_path,
            output_path=license_compliance_report_path,
        )
    )
    package_result = _as_payload(
        package_runner(
            release_version=expected_release_version,
            output_dir=release_bundle_dir,
        )
    )
    deployed_load_result = _as_payload(
        deployed_load_runner(
            base_url=base_url,
            expected_environment=expected_environment,
            expected_release_version=expected_release_version,
            admin_bearer_token=admin_bearer_token,
            branch_bearer_token=branch_bearer_token,
            tenant_id=tenant_id,
            branch_id=branch_id,
            product_id=product_id,
            output_path=deployed_load_report_path,
        )
    )
    rollback_result = _as_payload(
        rollback_runner(
            base_url=base_url,
            target_bundle_manifest_path=Path(str(package_result["manifest_path"])),
            output_path=rollback_report_path,
            expected_environment=expected_environment,
            expected_release_version=expected_release_version,
            bearer_token=bearer_token,
        )
    )
    restore_result = _as_payload(
        (
            run_restore_drill
            or (
                lambda **kwargs: _default_restore_drill(
                    settings=settings,
                    **kwargs,
                )
            )
        )(
            dump_key=dump_key,
            metadata_key=metadata_key,
            target_database_url=target_database_url,
            output_path=restore_drill_report_path,
            verify_smoke=verify_smoke_restore_drill,
            allow_environment_mismatch=allow_restore_environment_mismatch,
        )
    )

    strict_certifier = lambda **kwargs: certifier(
        require_deployed_load=True,
        require_rollback_verification=True,
        require_restore_drill=True,
        **kwargs,
    )
    evidence_result = _as_payload(
        evidence_generator(
            base_url=base_url,
            expected_environment=expected_environment,
            expected_release_version=expected_release_version,
            release_owner=release_owner,
            output_path=release_evidence_path,
            alert_report_path=operational_alert_report_path,
            environment_drift_report_path=environment_drift_report_path,
            tls_posture_report_path=tls_posture_report_path,
            sbom_report_path=sbom_report_path,
            provenance_report_path=Path(str(package_result["provenance_report_path"])),
            license_compliance_report_path=license_compliance_report_path,
            deployed_load_report_path=deployed_load_report_path,
            rollback_report_path=rollback_report_path,
            vulnerability_scan_report_path=vulnerability_scan_report_path,
            restore_drill_report_path=restore_drill_report_path,
            certification_output_path=certification_report_path,
            evidence_bundle_output_dir=evidence_bundle_dir,
            evidence_publication_output_dir=publication_dir,
            sbom_artifact_dir=sbom_raw_dir,
            vulnerability_raw_output_dir=vulnerability_raw_dir,
            retain_evidence_offsite=retain_evidence_offsite or verify_retained_evidence,
            bearer_token=bearer_token,
            certify_release_candidate=strict_certifier,
            settings_factory=lambda: settings,
        )
    )

    retrieval_result: dict[str, object] | None = None
    effective_retain_offsite = retain_evidence_offsite or verify_retained_evidence
    if verify_retained_evidence:
        if not effective_retain_offsite or evidence_result.get("offsite_retention_result") is None:
            retrieval_result = {
                "status": "failed",
                "reason": "retained evidence verification requested but offsite retention did not run",
            }
        else:
            retrieval_result = _as_payload(
                retrieval_runner(
                    settings=settings,
                    environment=expected_environment,
                    release_version=expected_release_version,
                    output_root=retrieved_dir,
                )
            )

    final_status = "passed" if evidence_result.get("final_status") == "approved" else "blocked"
    summary_parts = [f"release certification {evidence_result.get('final_status') or 'blocked'}"]
    if retrieval_result is not None:
        if retrieval_result.get("status") == "passed":
            summary_parts.append("retained evidence retrieval verified")
        else:
            final_status = "blocked"
            summary_parts.append("retained evidence retrieval verification failed")

    report_payload = {
        "status": final_status,
        "summary": "; ".join(summary_parts),
        "environment": expected_environment,
        "release_version": expected_release_version,
        "release_owner": release_owner,
        "output_dir": str(output_dir),
        "report_paths": {
            "vulnerability_scan_report": str(vulnerability_scan_report_path),
            "operational_alert_report": str(operational_alert_report_path),
            "environment_drift_report": str(environment_drift_report_path),
            "tls_posture_report": str(tls_posture_report_path),
            "sbom_report": str(sbom_report_path),
            "license_compliance_report": str(license_compliance_report_path),
            "deployed_load_report": str(deployed_load_report_path),
            "rollback_report": str(rollback_report_path),
            "restore_drill_report": str(restore_drill_report_path),
            "release_evidence": str(release_evidence_path),
            "certification_report": str(certification_report_path),
        },
        "certification_status": evidence_result.get("final_status"),
        "retained_evidence_status": None if retrieval_result is None else retrieval_result.get("status"),
        "package_result": package_result,
        "vulnerability_scan_result": vulnerability_scan_result,
        "operational_alert_result": operational_alert_result,
        "environment_drift_result": environment_drift_result,
        "tls_posture_result": tls_posture_result,
        "sbom_result": sbom_result,
        "license_compliance_result": license_compliance_result,
        "deployed_load_result": deployed_load_result,
        "rollback_result": rollback_result,
        "restore_drill_result": restore_result,
        "evidence_result": evidence_result,
        "retained_evidence_result": retrieval_result,
        "report_path": str(report_path),
    }
    write_release_gate_report(report_payload, output_path=report_path)
    return report_payload
