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
            "status": "approved",
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

    assert result["final_status"] == "approved"
    assert result["output_path"] == str(output_path)
    content = output_path.read_text(encoding="utf-8")
    assert "Version: 2026.04.15-rc1" in content
    assert "Environment: staging" in content
    assert "Release owner: ops@store.korsenex.com" in content
    assert "local verification passed" in content
    assert "python services/control-plane-api/scripts/validate_performance_foundation.py" in content
    assert "8 scenarios passed" in content
    assert "`legacy_write_mode`: cutover" in content
    assert "`legacy_remaining_domains`: none" in content
    assert "Status: approved" in content


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
    assert "`legacy_write_mode`: shadow" in content
    assert "`legacy_remaining_domains`: legacy_customer_reads" in content
    assert "Status: blocked" in content


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
            "status": "approved",
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

    assert result["final_status"] == "approved"
    content = output_path.read_text(encoding="utf-8")
    assert "## Recovery Evidence" in content
    assert "restore drill status: passed" in content
    assert "control-plane/staging/postgres-backups/restore.dump" in content
    assert "2026.04.18-rc1" in content
