from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "generate_release_candidate_evidence.py"
    spec = importlib.util.spec_from_file_location("generate_release_candidate_evidence_script", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_generate_release_candidate_evidence_writes_markdown_with_verification_results(tmp_path: Path) -> None:
    module = _load_script_module()
    output_path = tmp_path / "rc-evidence.md"

    def fake_local_verify() -> dict[str, object]:
        return {
            "status": "passed",
            "command": "python services/control-plane-api/scripts/verify_control_plane.py",
            "summary": "local verification passed",
        }

    def fake_verify_deployed(**_: object) -> dict[str, object]:
        return {
            "status": "ok",
            "environment": "staging",
            "release_version": "2026.04.15-rc1",
            "legacy_write_mode": "cutover",
            "legacy_remaining_domains": [],
        }

    def fake_certify(**_: object) -> dict[str, object]:
        return {
            "status": "blocked",
            "environment": "staging",
            "release_version": "2026.04.15-rc1",
            "legacy_write_mode": "cutover",
            "legacy_remaining_domains": [],
            "gates": {
                "health_ok": True,
                "environment_match": True,
                "release_version_match": True,
                "legacy_write_mode_cutover": True,
                "legacy_remaining_domains_cleared": True,
                "vulnerability_scans_passed": False,
            },
        }

    def fake_performance_validate() -> dict[str, object]:
        return {
            "status": "passed",
            "command": "python services/control-plane-api/scripts/validate_performance_foundation.py",
            "summary": "8 scenarios passed",
            "scenario_set": "launch-foundation",
            "failing_scenarios": [],
        }

    result = module.generate_release_candidate_evidence(
        base_url="https://control.staging.store.korsenex.com",
        expected_environment="staging",
        expected_release_version="2026.04.15-rc1",
        release_owner="ops@store.korsenex.com",
        output_path=output_path,
        local_verify=fake_local_verify,
        verify_deployed=fake_verify_deployed,
        certify_release_candidate=fake_certify,
        performance_validate=fake_performance_validate,
        date_text="2026-04-15",
    )

    assert result["final_status"] == "blocked"
    assert result["output_path"] == str(output_path)
    content = output_path.read_text(encoding="utf-8")
    assert "Version: 2026.04.15-rc1" in content
    assert "Environment: staging" in content
    assert "Release owner: ops@store.korsenex.com" in content
    assert "local verification passed" in content
    assert "python services/control-plane-api/scripts/validate_performance_foundation.py" in content
    assert "8 scenarios passed" in content
    assert "Security verification status: not-run" in content
    assert "`legacy_write_mode`: cutover" in content
    assert "`legacy_remaining_domains`: none" in content
    assert "Status: blocked" in content


def test_generate_release_candidate_evidence_records_blocked_state_and_skipped_local_verification(tmp_path: Path) -> None:
    module = _load_script_module()
    output_path = tmp_path / "rc-evidence-blocked.md"

    def fake_verify_deployed(**_: object) -> dict[str, object]:
        return {
            "status": "ok",
            "environment": "prod",
            "release_version": "2026.04.15",
            "legacy_write_mode": "shadow",
            "legacy_remaining_domains": ["legacy_customer_reads"],
        }

    def fake_certify(**_: object) -> dict[str, object]:
        return {
            "status": "blocked",
            "environment": "prod",
            "release_version": "2026.04.15",
            "legacy_write_mode": "shadow",
            "legacy_remaining_domains": ["legacy_customer_reads"],
            "gates": {
                "health_ok": True,
                "environment_match": True,
                "release_version_match": True,
                "legacy_write_mode_cutover": False,
                "legacy_remaining_domains_cleared": False,
                "vulnerability_scans_passed": False,
            },
        }

    result = module.generate_release_candidate_evidence(
        base_url="https://control.store.korsenex.com",
        expected_environment="prod",
        expected_release_version="2026.04.15",
        release_owner="release@store.korsenex.com",
        output_path=output_path,
        run_local_verification=False,
        run_performance_validation=False,
        verify_deployed=fake_verify_deployed,
        certify_release_candidate=fake_certify,
        date_text="2026-04-15",
    )

    assert result["final_status"] == "blocked"
    content = output_path.read_text(encoding="utf-8")
    assert "result: skipped" in content
    assert "Performance validation command: not-run" in content
    assert "Security verification status: not-run" in content
    assert "`legacy_write_mode`: shadow" in content
    assert "`legacy_remaining_domains`: legacy_customer_reads" in content
    assert "Status: blocked" in content


def test_generate_release_candidate_evidence_renders_security_posture(tmp_path: Path) -> None:
    module = _load_script_module()
    output_path = tmp_path / "rc-evidence-security.md"

    def fake_verify_deployed(**_: object) -> dict[str, object]:
        return {
            "status": "ok",
            "environment": "staging",
            "release_version": "2026.04.18-rc1",
            "legacy_write_mode": "cutover",
            "legacy_remaining_domains": [],
            "security_result": {
                "status": "passed",
                "secure_headers": {"status": "passed"},
                "auth_rate_limit": {"status": "passed"},
                "webhook_rate_limit": {"status": "passed"},
            },
        }

    def fake_certify(**_: object) -> dict[str, object]:
        return {
            "status": "blocked",
            "environment": "staging",
            "release_version": "2026.04.18-rc1",
            "legacy_write_mode": "cutover",
            "legacy_remaining_domains": [],
            "gates": {
                "health_ok": True,
                "environment_match": True,
                "release_version_match": True,
                "legacy_write_mode_cutover": True,
                "legacy_remaining_domains_cleared": True,
                "security_controls_verified": True,
                "vulnerability_scans_passed": False,
            },
        }

    result = module.generate_release_candidate_evidence(
        base_url="https://control.staging.store.korsenex.com",
        expected_environment="staging",
        expected_release_version="2026.04.18-rc1",
        release_owner="ops@store.korsenex.com",
        output_path=output_path,
        run_local_verification=False,
        run_performance_validation=False,
        verify_deployed=fake_verify_deployed,
        certify_release_candidate=fake_certify,
        date_text="2026-04-18",
    )

    assert result["final_status"] == "blocked"
    content = output_path.read_text(encoding="utf-8")
    assert "Security verification status: passed" in content
    assert "auth rate limit: passed" in content
    assert "webhook rate limit: passed" in content
    assert "Vulnerability scan status: not-run" in content


def test_generate_release_candidate_evidence_renders_restore_drill_report(tmp_path: Path) -> None:
    module = _load_script_module()
    output_path = tmp_path / "rc-evidence-with-restore-drill.md"
    restore_drill_report_path = tmp_path / "restore-drill-report.json"
    restore_drill_report_path.write_text(
        json.dumps(
            {
                "status": "passed",
                "source": {
                    "bucket": "store-platform-staging",
                    "dump_key": "control-plane/staging/postgres-backups/restore.dump",
                    "metadata_key": "control-plane/staging/postgres-backups/metadata.json",
                },
                "target": {
                    "target_database_url": "postgresql://store:***@db.internal:5432/store_restore",
                },
                "restored_manifest": {
                    "environment": "staging",
                    "release_version": "2026.04.18-rc1",
                    "alembic_head": "20260418_0044_restore_drill_foundation",
                },
                "health_result": {"status": "passed"},
                "verification_result": {"status": "skipped"},
                "failure_reason": None,
            }
        ),
        encoding="utf-8",
    )

    def fake_verify_deployed(**_: object) -> dict[str, object]:
        return {
            "status": "ok",
            "environment": "staging",
            "release_version": "2026.04.18-rc1",
            "legacy_write_mode": "cutover",
            "legacy_remaining_domains": [],
        }

    def fake_certify(**_: object) -> dict[str, object]:
        return {
            "status": "blocked",
            "environment": "staging",
            "release_version": "2026.04.18-rc1",
            "legacy_write_mode": "cutover",
            "legacy_remaining_domains": [],
            "gates": {
                "health_ok": True,
                "environment_match": True,
                "release_version_match": True,
                "legacy_write_mode_cutover": True,
                "legacy_remaining_domains_cleared": True,
                "vulnerability_scans_passed": False,
            },
        }

    result = module.generate_release_candidate_evidence(
        base_url="https://control.staging.store.korsenex.com",
        expected_environment="staging",
        expected_release_version="2026.04.18-rc1",
        release_owner="ops@store.korsenex.com",
        output_path=output_path,
        run_local_verification=False,
        run_performance_validation=False,
        verify_deployed=fake_verify_deployed,
        certify_release_candidate=fake_certify,
        restore_drill_report_path=restore_drill_report_path,
        date_text="2026-04-18",
    )

    assert result["final_status"] == "blocked"
    content = output_path.read_text(encoding="utf-8")
    assert "## Recovery Evidence" in content
    assert "restore drill status: passed" in content
    assert "control-plane/staging/postgres-backups/restore.dump" in content
    assert "2026.04.18-rc1" in content


def test_generate_release_candidate_evidence_renders_vulnerability_scan_posture(tmp_path: Path) -> None:
    module = _load_script_module()
    output_path = tmp_path / "rc-evidence-vulnerability.md"
    vulnerability_report_path = tmp_path / "vulnerability-report.json"
    vulnerability_report_path.write_text(
        json.dumps(
            {
                "status": "passed",
                "surfaces": {
                    "python": {"status": "passed"},
                    "node": {"status": "passed"},
                    "rust": {"status": "passed"},
                    "images": {"status": "passed"},
                },
                "failing_surfaces": [],
                "summary": "4 surfaces passed",
            }
        ),
        encoding="utf-8",
    )

    def fake_verify_deployed(**_: object) -> dict[str, object]:
        return {
            "status": "ok",
            "environment": "staging",
            "release_version": "2026.04.18-rc2",
            "legacy_write_mode": "cutover",
            "legacy_remaining_domains": [],
        }

    def fake_certify(**_: object) -> dict[str, object]:
        return {
            "status": "approved",
            "environment": "staging",
            "release_version": "2026.04.18-rc2",
            "legacy_write_mode": "cutover",
            "legacy_remaining_domains": [],
            "gates": {
                "health_ok": True,
                "environment_match": True,
                "release_version_match": True,
                "legacy_write_mode_cutover": True,
                "legacy_remaining_domains_cleared": True,
                "vulnerability_scans_passed": True,
            },
        }

    result = module.generate_release_candidate_evidence(
        base_url="https://control.staging.store.korsenex.com",
        expected_environment="staging",
        expected_release_version="2026.04.18-rc2",
        release_owner="ops@store.korsenex.com",
        output_path=output_path,
        run_local_verification=False,
        run_performance_validation=False,
        verify_deployed=fake_verify_deployed,
        certify_release_candidate=fake_certify,
        vulnerability_scan_report_path=vulnerability_report_path,
        date_text="2026-04-18",
    )

    assert result["final_status"] == "approved"
    content = output_path.read_text(encoding="utf-8")
    assert "## Vulnerability Scan Evidence" in content
    assert "overall scan status: passed" in content
    assert "python: passed" in content
    assert "images: passed" in content


def test_generate_release_candidate_evidence_renders_provenance_posture(tmp_path: Path) -> None:
    module = _load_script_module()
    output_path = tmp_path / "rc-evidence-provenance.md"
    provenance_report_path = tmp_path / "provenance-report.json"
    provenance_report_path.write_text(
        json.dumps(
            {
                "status": "passed",
                "release_version": "2026.04.18-rc4",
                "bundle_name": "store-control-plane-2026.04.18-rc4",
                "archive_sha256": "a" * 64,
                "manifest_sha256": "b" * 64,
                "source_commit": "c" * 40,
                "source_tree": "d" * 40,
                "source_ref": "main",
                "source_remote": "https://github.com/korsenex/store.git",
                "source_worktree_clean": True,
                "summary": "release provenance verified",
            }
        ),
        encoding="utf-8",
    )

    def fake_verify_deployed(**_: object) -> dict[str, object]:
        return {
            "status": "ok",
            "environment": "staging",
            "release_version": "2026.04.18-rc4",
            "legacy_write_mode": "cutover",
            "legacy_remaining_domains": [],
        }

    def fake_certify(**_: object) -> dict[str, object]:
        return {
            "status": "approved",
            "environment": "staging",
            "release_version": "2026.04.18-rc4",
            "legacy_write_mode": "cutover",
            "legacy_remaining_domains": [],
            "gates": {
                "health_ok": True,
                "environment_match": True,
                "release_version_match": True,
                "legacy_write_mode_cutover": True,
                "legacy_remaining_domains_cleared": True,
                "provenance_verified": True,
                "vulnerability_scans_passed": True,
            },
        }

    result = module.generate_release_candidate_evidence(
        base_url="https://control.staging.store.korsenex.com",
        expected_environment="staging",
        expected_release_version="2026.04.18-rc4",
        release_owner="ops@store.korsenex.com",
        output_path=output_path,
        run_local_verification=False,
        run_performance_validation=False,
        verify_deployed=fake_verify_deployed,
        certify_release_candidate=fake_certify,
        provenance_report_path=provenance_report_path,
        date_text="2026-04-18",
    )

    assert result["final_status"] == "approved"
    content = output_path.read_text(encoding="utf-8")
    assert "## Release Provenance Evidence" in content
    assert "provenance status: passed" in content
    assert "source commit:" in content
    assert "source worktree clean: True" in content


def test_generate_release_candidate_evidence_renders_license_compliance_posture(tmp_path: Path) -> None:
    module = _load_script_module()
    output_path = tmp_path / "rc-evidence-license.md"
    license_report_path = tmp_path / "license-report.json"
    license_report_path.write_text(
        json.dumps(
            {
                "status": "failed",
                "surfaces": {
                    "control_plane_api": {
                        "status": "failed",
                        "license_summary": {"allowed": 41, "review_required": 1, "denied": 0, "unknown": 0},
                        "findings": [
                            {
                                "package_or_identifier": "review-lib",
                                "license": "LGPL-2.1-only",
                                "status": "review_required",
                            }
                        ],
                    }
                },
                "failing_surfaces": ["control_plane_api"],
                "summary": "1 surfaces failed: control_plane_api",
            }
        ),
        encoding="utf-8",
    )

    def fake_verify_deployed(**_: object) -> dict[str, object]:
        return {
            "status": "ok",
            "environment": "staging",
            "release_version": "2026.04.18-rc5",
            "legacy_write_mode": "cutover",
            "legacy_remaining_domains": [],
        }

    def fake_certify(**_: object) -> dict[str, object]:
        return {
            "status": "blocked",
            "environment": "staging",
            "release_version": "2026.04.18-rc5",
            "legacy_write_mode": "cutover",
            "legacy_remaining_domains": [],
            "gates": {
                "health_ok": True,
                "environment_match": True,
                "release_version_match": True,
                "legacy_write_mode_cutover": True,
                "legacy_remaining_domains_cleared": True,
                "license_compliance_verified": False,
                "vulnerability_scans_passed": True,
            },
        }

    result = module.generate_release_candidate_evidence(
        base_url="https://control.staging.store.korsenex.com",
        expected_environment="staging",
        expected_release_version="2026.04.18-rc5",
        release_owner="ops@store.korsenex.com",
        output_path=output_path,
        run_local_verification=False,
        run_performance_validation=False,
        verify_deployed=fake_verify_deployed,
        certify_release_candidate=fake_certify,
        license_compliance_report_path=license_report_path,
        date_text="2026-04-18",
    )

    assert result["final_status"] == "blocked"
    content = output_path.read_text(encoding="utf-8")
    assert "## License Compliance Evidence" in content
    assert "license compliance status: failed" in content
    assert "control_plane_api" in content


def test_generate_release_candidate_evidence_renders_operational_alert_posture(tmp_path: Path) -> None:
    module = _load_script_module()
    output_path = tmp_path / "rc-evidence-alerts.md"
    alert_report_path = tmp_path / "operational-alerts.json"
    alert_report_path.write_text(
        json.dumps(
            {
                "status": "failed",
                "summary": "1 alert check failing",
                "failing_checks": ["backup_freshness_within_limit"],
                "alert_checks": [
                    {
                        "name": "operations_dead_letter_clear",
                        "status": "passed",
                        "observed_value": 0,
                        "threshold": 0,
                        "reason": "dead letter queue clear",
                    },
                    {
                        "name": "backup_freshness_within_limit",
                        "status": "failed",
                        "observed_value": 31,
                        "threshold": 26,
                        "reason": "backup age breached",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    def fake_verify_deployed(**_: object) -> dict[str, object]:
        return {
            "status": "ok",
            "environment": "staging",
            "release_version": "2026.04.18-rc3",
            "legacy_write_mode": "cutover",
            "legacy_remaining_domains": [],
        }

    def fake_certify(**_: object) -> dict[str, object]:
        return {
            "status": "blocked",
            "environment": "staging",
            "release_version": "2026.04.18-rc3",
            "legacy_write_mode": "cutover",
            "legacy_remaining_domains": [],
            "gates": {
                "health_ok": True,
                "environment_match": True,
                "release_version_match": True,
                "legacy_write_mode_cutover": True,
                "legacy_remaining_domains_cleared": True,
                "operational_alerts_verified": False,
                "vulnerability_scans_passed": False,
            },
        }

    result = module.generate_release_candidate_evidence(
        base_url="https://control.staging.store.korsenex.com",
        expected_environment="staging",
        expected_release_version="2026.04.18-rc3",
        release_owner="ops@store.korsenex.com",
        output_path=output_path,
        run_local_verification=False,
        run_performance_validation=False,
        verify_deployed=fake_verify_deployed,
        certify_release_candidate=fake_certify,
        alert_report_path=alert_report_path,
        date_text="2026-04-18",
    )

    assert result["final_status"] == "blocked"
    content = output_path.read_text(encoding="utf-8")
    assert "## Operational Alert Evidence" in content
    assert "overall alert status: failed" in content
    assert "operations dead letter clear: passed" in content
    assert "backup freshness within limit: failed" in content
    assert "failing checks: backup_freshness_within_limit" in content


def test_generate_release_candidate_evidence_renders_deployed_load_posture(tmp_path: Path) -> None:
    module = _load_script_module()
    output_path = tmp_path / "rc-evidence-deployed-load.md"
    deployed_load_report_path = tmp_path / "deployed-load-report.json"
    deployed_load_report_path.write_text(
        json.dumps(
            {
                "status": "failed",
                "environment": "staging",
                "release_version": "2026.04.18-rc5",
                "concurrency": 4,
                "iterations_per_worker": 5,
                "failing_scenarios": ["checkout_price_preview_http"],
                "scenario_results": [
                    {"scenario_name": "system_health_http", "status": "passed"},
                    {"scenario_name": "checkout_price_preview_http", "status": "failed"},
                ],
            }
        ),
        encoding="utf-8",
    )

    def fake_verify_deployed(**_: object) -> dict[str, object]:
        return {
            "status": "ok",
            "environment": "staging",
            "release_version": "2026.04.18-rc5",
            "legacy_write_mode": "cutover",
            "legacy_remaining_domains": [],
        }

    def fake_certify(**_: object) -> dict[str, object]:
        return {
            "status": "blocked",
            "environment": "staging",
            "release_version": "2026.04.18-rc5",
            "legacy_write_mode": "cutover",
            "legacy_remaining_domains": [],
            "gates": {
                "health_ok": True,
                "environment_match": True,
                "release_version_match": True,
                "legacy_write_mode_cutover": True,
                "legacy_remaining_domains_cleared": True,
                "operational_alerts_verified": False,
                "vulnerability_scans_passed": False,
                "deployed_load_verified": False,
            },
        }

    result = module.generate_release_candidate_evidence(
        base_url="https://control.staging.store.korsenex.com",
        expected_environment="staging",
        expected_release_version="2026.04.18-rc5",
        release_owner="ops@store.korsenex.com",
        output_path=output_path,
        run_local_verification=False,
        run_performance_validation=False,
        verify_deployed=fake_verify_deployed,
        certify_release_candidate=fake_certify,
        deployed_load_report_path=deployed_load_report_path,
        date_text="2026-04-18",
    )

    assert result["final_status"] == "blocked"
    content = output_path.read_text(encoding="utf-8")
    assert "## Deployed Load Evidence" in content
    assert "overall deployed load status: failed" in content
    assert "concurrency: 4" in content
    assert "checkout price preview http: failed" in content
    assert "failing scenarios: checkout_price_preview_http" in content


def test_generate_release_candidate_evidence_renders_rollback_posture(tmp_path: Path) -> None:
    module = _load_script_module()
    output_path = tmp_path / "rc-evidence-rollback.md"
    rollback_report_path = tmp_path / "rollback-report.json"
    rollback_report_path.write_text(
        json.dumps(
            {
                "status": "failed",
                "environment": "staging",
                "current_release_version": "2026.04.18",
                "current_alembic_head": "20260418_0049_rollback_verification_foundation",
                "target_release_version": "2026.04.17",
                "target_alembic_head": "20260417_0048_previous_head",
                "rollback_mode": "restore_required",
                "failure_reason": "target bundle schema head differs from deployed schema head",
            }
        ),
        encoding="utf-8",
    )

    def fake_verify_deployed(**_: object) -> dict[str, object]:
        return {
            "status": "ok",
            "environment": "staging",
            "release_version": "2026.04.18",
            "legacy_write_mode": "cutover",
            "legacy_remaining_domains": [],
        }

    def fake_certify(**_: object) -> dict[str, object]:
        return {
            "status": "blocked",
            "environment": "staging",
            "release_version": "2026.04.18",
            "legacy_write_mode": "cutover",
            "legacy_remaining_domains": [],
            "gates": {
                "health_ok": True,
                "environment_match": True,
                "release_version_match": True,
                "legacy_write_mode_cutover": True,
                "legacy_remaining_domains_cleared": True,
                "deployed_load_verified": True,
                "rollback_verified": False,
                "operational_alerts_verified": False,
                "vulnerability_scans_passed": False,
            },
        }

    result = module.generate_release_candidate_evidence(
        base_url="https://control.staging.store.korsenex.com",
        expected_environment="staging",
        expected_release_version="2026.04.18",
        release_owner="ops@store.korsenex.com",
        output_path=output_path,
        run_local_verification=False,
        run_performance_validation=False,
        verify_deployed=fake_verify_deployed,
        certify_release_candidate=fake_certify,
        rollback_report_path=rollback_report_path,
        date_text="2026-04-18",
    )

    assert result["final_status"] == "blocked"
    content = output_path.read_text(encoding="utf-8")
    assert "## Rollback Evidence" in content
    assert "rollback status: failed" in content
    assert "current release version: 2026.04.18" in content
    assert "target release version: 2026.04.17" in content
    assert "rollback mode: restore_required" in content
    assert "failure reason: target bundle schema head differs from deployed schema head" in content


def test_generate_release_candidate_evidence_renders_environment_drift_posture(tmp_path: Path) -> None:
    module = _load_script_module()
    output_path = tmp_path / "rc-evidence-environment-drift.md"
    environment_drift_report_path = tmp_path / "environment-drift-report.json"
    environment_drift_report_path.write_text(
        json.dumps(
            {
                "status": "failed",
                "environment": "staging",
                "release_version": "2026.04.18-rc9",
                "failing_checks": ["log_format_json", "sentry_configured"],
                "checks": [
                    {"name": "deployment_environment_match", "status": "passed"},
                    {"name": "log_format_json", "status": "failed"},
                    {"name": "sentry_configured", "status": "failed"},
                ],
                "summary": "2 checks failed: log_format_json, sentry_configured",
            }
        ),
        encoding="utf-8",
    )

    def fake_verify_deployed(**_: object) -> dict[str, object]:
        return {
            "status": "ok",
            "environment": "staging",
            "release_version": "2026.04.18-rc9",
            "legacy_write_mode": "cutover",
            "legacy_remaining_domains": [],
        }

    def fake_certify(**_: object) -> dict[str, object]:
        return {
            "status": "blocked",
            "environment": "staging",
            "release_version": "2026.04.18-rc9",
            "legacy_write_mode": "cutover",
            "legacy_remaining_domains": [],
            "gates": {
                "health_ok": True,
                "environment_match": True,
                "release_version_match": True,
                "legacy_write_mode_cutover": True,
                "legacy_remaining_domains_cleared": True,
                "operational_alerts_verified": True,
                "environment_drift_verified": False,
                "vulnerability_scans_passed": True,
            },
        }

    result = module.generate_release_candidate_evidence(
        base_url="https://control.staging.store.korsenex.com",
        expected_environment="staging",
        expected_release_version="2026.04.18-rc9",
        release_owner="ops@store.korsenex.com",
        output_path=output_path,
        run_local_verification=False,
        run_performance_validation=False,
        verify_deployed=fake_verify_deployed,
        certify_release_candidate=fake_certify,
        environment_drift_report_path=environment_drift_report_path,
        date_text="2026-04-18",
    )

    assert result["final_status"] == "blocked"
    content = output_path.read_text(encoding="utf-8")
    assert "## Environment Drift Evidence" in content
    assert "environment drift status: failed" in content
    assert "failing checks: log_format_json, sentry_configured" in content
    assert "deployment environment match: passed" in content
    assert "log format json: failed" in content


def test_generate_release_candidate_evidence_renders_tls_posture(tmp_path: Path) -> None:
    module = _load_script_module()
    output_path = tmp_path / "rc-evidence-tls.md"
    tls_report_path = tmp_path / "tls-posture.json"
    tls_report_path.write_text(
        json.dumps(
            {
                "status": "failed",
                "host": "control.store.korsenex.com",
                "port": 443,
                "scheme": "https",
                "failing_checks": ["certificate_validity_window"],
                "checks": [
                    {"name": "https_required", "status": "passed"},
                    {"name": "hostname_match", "status": "passed"},
                    {"name": "certificate_validity_window", "status": "failed"},
                ],
                "summary": "1 checks failed: certificate_validity_window",
            }
        ),
        encoding="utf-8",
    )

    def fake_verify_deployed(**_: object) -> dict[str, object]:
        return {
            "status": "ok",
            "environment": "staging",
            "release_version": "2026.04.18-rc10",
            "legacy_write_mode": "cutover",
            "legacy_remaining_domains": [],
        }

    def fake_certify(**_: object) -> dict[str, object]:
        return {
            "status": "blocked",
            "environment": "staging",
            "release_version": "2026.04.18-rc10",
            "legacy_write_mode": "cutover",
            "legacy_remaining_domains": [],
            "gates": {
                "health_ok": True,
                "environment_match": True,
                "release_version_match": True,
                "legacy_write_mode_cutover": True,
                "legacy_remaining_domains_cleared": True,
                "operational_alerts_verified": True,
                "environment_drift_verified": True,
                "tls_posture_verified": False,
                "vulnerability_scans_passed": True,
            },
        }

    result = module.generate_release_candidate_evidence(
        base_url="https://control.staging.store.korsenex.com",
        expected_environment="staging",
        expected_release_version="2026.04.18-rc10",
        release_owner="ops@store.korsenex.com",
        output_path=output_path,
        run_local_verification=False,
        run_performance_validation=False,
        verify_deployed=fake_verify_deployed,
        certify_release_candidate=fake_certify,
        tls_posture_report_path=tls_report_path,
        date_text="2026-04-18",
    )

    assert result["final_status"] == "blocked"
    content = output_path.read_text(encoding="utf-8")
    assert "## TLS Evidence" in content
    assert "tls posture status: failed" in content
    assert "failing checks: certificate_validity_window" in content
    assert "certificate validity window: failed" in content


def test_generate_release_candidate_evidence_renders_sbom_posture(tmp_path: Path) -> None:
    module = _load_script_module()
    output_path = tmp_path / "rc-evidence-sbom.md"
    sbom_report_path = tmp_path / "sbom-report.json"
    sbom_report_path.write_text(
        json.dumps(
            {
                "status": "failed",
                "failing_surfaces": ["owner_web"],
                "surfaces": {
                    "control_plane_api": {
                        "status": "passed",
                        "format": "cyclonedx-json",
                        "component_count": 42,
                    },
                    "owner_web": {
                        "status": "tool-unavailable",
                        "format": "cyclonedx-json",
                        "component_count": 0,
                    },
                },
                "summary": "1 surfaces failed: owner_web",
            }
        ),
        encoding="utf-8",
    )

    def fake_verify_deployed(**_: object) -> dict[str, object]:
        return {
            "status": "ok",
            "environment": "staging",
            "release_version": "2026.04.18-rc11",
            "legacy_write_mode": "cutover",
            "legacy_remaining_domains": [],
        }

    def fake_certify(**_: object) -> dict[str, object]:
        return {
            "status": "blocked",
            "environment": "staging",
            "release_version": "2026.04.18-rc11",
            "legacy_write_mode": "cutover",
            "legacy_remaining_domains": [],
            "gates": {
                "health_ok": True,
                "environment_match": True,
                "release_version_match": True,
                "legacy_write_mode_cutover": True,
                "legacy_remaining_domains_cleared": True,
                "operational_alerts_verified": True,
                "environment_drift_verified": True,
                "tls_posture_verified": True,
                "sbom_verified": False,
                "vulnerability_scans_passed": True,
            },
        }

    result = module.generate_release_candidate_evidence(
        base_url="https://control.staging.store.korsenex.com",
        expected_environment="staging",
        expected_release_version="2026.04.18-rc11",
        release_owner="ops@store.korsenex.com",
        output_path=output_path,
        run_local_verification=False,
        run_performance_validation=False,
        verify_deployed=fake_verify_deployed,
        certify_release_candidate=fake_certify,
        sbom_report_path=sbom_report_path,
        date_text="2026-04-18",
    )

    assert result["final_status"] == "blocked"
    content = output_path.read_text(encoding="utf-8")
    assert "## SBOM Evidence" in content
    assert "sbom status: failed" in content
    assert "failing surfaces: owner_web" in content
    assert "control plane api: passed" in content
    assert "owner web: tool-unavailable" in content
