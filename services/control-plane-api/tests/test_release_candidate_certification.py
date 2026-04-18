from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_certification_script_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "certify_release_candidate.py"
    spec = importlib.util.spec_from_file_location("certify_release_candidate_script", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_release_candidate_certification_approves_cutover_ready_deployment() -> None:
    module = _load_certification_script_module()

    result = module.certify_release_candidate(
        base_url="https://control.store.korsenex.com",
        expected_environment="prod",
        expected_release_version="2026.04.15-rc1",
        operational_alert_result={"status": "passed", "failing_checks": []},
        vulnerability_scan_result={"status": "passed", "failing_surfaces": []},
        verify_deployed=lambda **_: {
            "status": "ok",
            "environment": "prod",
            "release_version": "2026.04.15-rc1",
            "legacy_write_mode": "cutover",
            "legacy_remaining_domains": [],
            "security_result": {"status": "passed"},
        },
    )

    assert result["status"] == "approved"
    assert result["gates"]["health_ok"] is True
    assert result["gates"]["environment_match"] is True
    assert result["gates"]["release_version_match"] is True
    assert result["gates"]["legacy_write_mode_cutover"] is True
    assert result["gates"]["legacy_remaining_domains_cleared"] is True
    assert result["gates"]["security_controls_verified"] is True
    assert result["gates"]["operational_alerts_verified"] is True
    assert result["gates"]["vulnerability_scans_passed"] is True


def test_release_candidate_certification_blocks_shadow_mode() -> None:
    module = _load_certification_script_module()

    result = module.certify_release_candidate(
        base_url="https://control.store.korsenex.com",
        expected_environment="prod",
        expected_release_version="2026.04.15-rc1",
        operational_alert_result={"status": "passed", "failing_checks": []},
        vulnerability_scan_result={"status": "passed", "failing_surfaces": []},
        verify_deployed=lambda **_: {
            "status": "ok",
            "environment": "prod",
            "release_version": "2026.04.15-rc1",
            "legacy_write_mode": "shadow",
            "legacy_remaining_domains": [],
            "security_result": {"status": "passed"},
        },
    )

    assert result["status"] == "blocked"
    assert result["gates"]["legacy_write_mode_cutover"] is False


def test_release_candidate_certification_blocks_remaining_legacy_domains() -> None:
    module = _load_certification_script_module()

    result = module.certify_release_candidate(
        base_url="https://control.store.korsenex.com",
        expected_environment="prod",
        expected_release_version="2026.04.15-rc1",
        operational_alert_result={"status": "passed", "failing_checks": []},
        vulnerability_scan_result={"status": "passed", "failing_surfaces": []},
        verify_deployed=lambda **_: {
            "status": "ok",
            "environment": "prod",
            "release_version": "2026.04.15-rc1",
            "legacy_write_mode": "cutover",
            "legacy_remaining_domains": ["legacy_customer_lookup"],
            "security_result": {"status": "passed"},
        },
    )

    assert result["status"] == "blocked"
    assert result["gates"]["legacy_remaining_domains_cleared"] is False
    assert result["legacy_remaining_domains"] == ["legacy_customer_lookup"]


def test_release_candidate_certification_approves_when_performance_budgets_pass() -> None:
    module = _load_certification_script_module()

    result = module.certify_release_candidate(
        base_url="https://control.store.korsenex.com",
        expected_environment="prod",
        expected_release_version="2026.04.15-rc1",
        performance_result={
            "status": "passed",
            "scenario_set": "launch-foundation",
            "failing_scenarios": [],
        },
        operational_alert_result={"status": "passed", "failing_checks": []},
        vulnerability_scan_result={"status": "passed", "failing_surfaces": []},
        verify_deployed=lambda **_: {
            "status": "ok",
            "environment": "prod",
            "release_version": "2026.04.15-rc1",
            "legacy_write_mode": "cutover",
            "legacy_remaining_domains": [],
            "security_result": {"status": "passed"},
        },
    )

    assert result["status"] == "approved"
    assert result["gates"]["performance_budgets_passed"] is True


def test_release_candidate_certification_blocks_when_performance_budgets_fail() -> None:
    module = _load_certification_script_module()

    result = module.certify_release_candidate(
        base_url="https://control.store.korsenex.com",
        expected_environment="prod",
        expected_release_version="2026.04.15-rc1",
        performance_result={
            "status": "failed",
            "scenario_set": "launch-foundation",
            "failing_scenarios": ["offline_sale_replay"],
        },
        operational_alert_result={"status": "passed", "failing_checks": []},
        vulnerability_scan_result={"status": "passed", "failing_surfaces": []},
        verify_deployed=lambda **_: {
            "status": "ok",
            "environment": "prod",
            "release_version": "2026.04.15-rc1",
            "legacy_write_mode": "cutover",
            "legacy_remaining_domains": [],
            "security_result": {"status": "passed"},
        },
    )

    assert result["status"] == "blocked"
    assert result["gates"]["performance_budgets_passed"] is False


def test_release_candidate_certification_blocks_failed_security_verification() -> None:
    module = _load_certification_script_module()

    result = module.certify_release_candidate(
        base_url="https://control.store.korsenex.com",
        expected_environment="prod",
        expected_release_version="2026.04.15-rc1",
        operational_alert_result={"status": "passed", "failing_checks": []},
        vulnerability_scan_result={"status": "passed", "failing_surfaces": []},
        verify_deployed=lambda **_: {
            "status": "ok",
            "environment": "prod",
            "release_version": "2026.04.15-rc1",
            "legacy_write_mode": "cutover",
            "legacy_remaining_domains": [],
            "security_result": {"status": "failed"},
        },
    )

    assert result["status"] == "blocked"
    assert result["gates"]["security_controls_verified"] is False


def test_release_candidate_certification_blocks_failed_vulnerability_report() -> None:
    module = _load_certification_script_module()

    result = module.certify_release_candidate(
        base_url="https://control.store.korsenex.com",
        expected_environment="prod",
        expected_release_version="2026.04.18-rc2",
        operational_alert_result={"status": "passed", "failing_checks": []},
        vulnerability_scan_result={"status": "failed", "failing_surfaces": ["python"]},
        verify_deployed=lambda **_: {
            "status": "ok",
            "environment": "prod",
            "release_version": "2026.04.18-rc2",
            "legacy_write_mode": "cutover",
            "legacy_remaining_domains": [],
            "security_result": {"status": "passed"},
        },
    )

    assert result["status"] == "blocked"
    assert result["gates"]["vulnerability_scans_passed"] is False


def test_release_candidate_certification_blocks_missing_vulnerability_report_by_default() -> None:
    module = _load_certification_script_module()

    result = module.certify_release_candidate(
        base_url="https://control.store.korsenex.com",
        expected_environment="prod",
        expected_release_version="2026.04.18-rc2",
        verify_deployed=lambda **_: {
            "status": "ok",
            "environment": "prod",
            "release_version": "2026.04.18-rc2",
            "legacy_write_mode": "cutover",
            "legacy_remaining_domains": [],
            "security_result": {"status": "passed"},
        },
    )

    assert result["status"] == "blocked"
    assert result["gates"]["vulnerability_scans_passed"] is False


def test_release_candidate_certification_blocks_missing_operational_alert_report_by_default() -> None:
    module = _load_certification_script_module()

    result = module.certify_release_candidate(
        base_url="https://control.store.korsenex.com",
        expected_environment="prod",
        expected_release_version="2026.04.18-rc3",
        vulnerability_scan_result={"status": "passed", "failing_surfaces": []},
        verify_deployed=lambda **_: {
            "status": "ok",
            "environment": "prod",
            "release_version": "2026.04.18-rc3",
            "legacy_write_mode": "cutover",
            "legacy_remaining_domains": [],
            "security_result": {"status": "passed"},
        },
    )

    assert result["status"] == "blocked"
    assert result["gates"]["operational_alerts_verified"] is False


def test_release_candidate_certification_blocks_failed_operational_alert_report() -> None:
    module = _load_certification_script_module()

    result = module.certify_release_candidate(
        base_url="https://control.store.korsenex.com",
        expected_environment="prod",
        expected_release_version="2026.04.18-rc3",
        vulnerability_scan_result={"status": "passed", "failing_surfaces": []},
        operational_alert_result={
            "status": "failed",
            "failing_checks": ["operations_dead_letter_clear"],
        },
        verify_deployed=lambda **_: {
            "status": "ok",
            "environment": "prod",
            "release_version": "2026.04.18-rc3",
            "legacy_write_mode": "cutover",
            "legacy_remaining_domains": [],
            "security_result": {"status": "passed"},
        },
    )

    assert result["status"] == "blocked"
    assert result["gates"]["operational_alerts_verified"] is False


def test_release_candidate_certification_approves_when_operational_alerts_pass() -> None:
    module = _load_certification_script_module()

    result = module.certify_release_candidate(
        base_url="https://control.store.korsenex.com",
        expected_environment="prod",
        expected_release_version="2026.04.18-rc3",
        vulnerability_scan_result={"status": "passed", "failing_surfaces": []},
        operational_alert_result={
            "status": "passed",
            "failing_checks": [],
        },
        verify_deployed=lambda **_: {
            "status": "ok",
            "environment": "prod",
            "release_version": "2026.04.18-rc3",
            "legacy_write_mode": "cutover",
            "legacy_remaining_domains": [],
            "security_result": {"status": "passed"},
        },
    )

    assert result["status"] == "approved"
    assert result["gates"]["operational_alerts_verified"] is True
