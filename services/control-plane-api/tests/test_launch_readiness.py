from __future__ import annotations

import json
from pathlib import Path

from store_control_plane.launch_readiness import (
    assess_launch_readiness,
    render_launch_readiness_markdown,
    write_launch_readiness_report,
)


def _base_manifest() -> dict[str, object]:
    return {
        "release_version": "2026.04.19",
        "environment": "prod",
        "release_owner": "release@store.korsenex.com",
        "beta_owner": "beta@store.korsenex.com",
        "candidate_date": "2026-04-19",
        "pilots": [
            {
                "tenant_id": "tenant-1",
                "branch_id": "branch-1",
                "outcome": "passed",
                "surface_checks": {
                    "owner_web_onboarding": "passed",
                    "desktop_install_activation": "passed",
                    "runtime_hardware_validation": "passed",
                    "offline_continuity_reviewed": True,
                },
                "notes": "Completed packaged pilot on branch hardware.",
            }
        ],
        "issues": [
            {
                "id": "ISSUE-21",
                "severity": "sev2",
                "status": "accepted",
                "owner": "support@store.korsenex.com",
                "workaround": "Retry the queue from the runtime dashboard.",
                "target_release": "2026.04.20",
            }
        ],
        "sign_offs": {
            "backend_owner": {
                "status": "approved",
                "approver": "backend@store.korsenex.com",
                "date": "2026-04-19",
            },
            "runtime_owner": {
                "status": "approved",
                "approver": "runtime@store.korsenex.com",
                "date": "2026-04-19",
            },
            "infra_owner": {
                "status": "approved",
                "approver": "infra@store.korsenex.com",
                "date": "2026-04-19",
            },
            "support_owner": {
                "status": "approved",
                "approver": "support@store.korsenex.com",
                "date": "2026-04-19",
            },
            "release_owner": {
                "status": "approved",
                "approver": "release@store.korsenex.com",
                "date": "2026-04-19",
            },
        },
    }


def _base_release_gate_report() -> dict[str, object]:
    return {
        "status": "passed",
        "certification_status": "approved",
        "summary": "release certification approved",
        "report_paths": {
            "release_evidence": "D:/codes/projects/store/docs/launch/evidence/prod-2026.04.19.md",
            "certification_report": "D:/codes/projects/store/docs/launch/evidence/prod-2026.04.19-certification.json",
        },
    }


def test_assess_launch_readiness_returns_ready_when_manifest_and_gate_pass() -> None:
    report = assess_launch_readiness(
        manifest=_base_manifest(),
        release_gate_report=_base_release_gate_report(),
        generated_at="2026-04-19T10:00:00Z",
    )

    assert report["status"] == "ready"
    assert report["failing_checks"] == []
    assert report["release_gate_status"] == "passed"
    assert report["pilot_count"] == 1
    assert report["approved_sign_off_count"] == 5
    markdown = render_launch_readiness_markdown(report)
    assert "# V2 Launch Readiness Report" in markdown
    assert "Version: 2026.04.19" in markdown
    assert "release gate passed: passed" in markdown
    assert "ISSUE-21" in markdown


def test_assess_launch_readiness_blocks_failed_release_gate() -> None:
    release_gate_report = _base_release_gate_report()
    release_gate_report["status"] = "blocked"
    release_gate_report["certification_status"] = "blocked"

    report = assess_launch_readiness(
        manifest=_base_manifest(),
        release_gate_report=release_gate_report,
        generated_at="2026-04-19T10:00:00Z",
    )

    assert report["status"] == "hold"
    assert "release_gate_passed" in report["failing_checks"]


def test_assess_launch_readiness_blocks_accepted_issue_without_support_metadata() -> None:
    manifest = _base_manifest()
    manifest["issues"] = [
        {
            "id": "ISSUE-22",
            "severity": "sev2",
            "status": "accepted",
            "owner": "",
            "workaround": "",
            "target_release": "",
        }
    ]

    report = assess_launch_readiness(
        manifest=manifest,
        release_gate_report=_base_release_gate_report(),
        generated_at="2026-04-19T10:00:00Z",
    )

    assert report["status"] == "hold"
    assert "accepted_issues_documented" in report["failing_checks"]


def test_assess_launch_readiness_blocks_open_severity_one_issue_and_missing_signoff() -> None:
    manifest = _base_manifest()
    manifest["issues"] = [
        {
            "id": "ISSUE-1",
            "severity": "sev1",
            "status": "open",
            "owner": "backend@store.korsenex.com",
            "workaround": "",
            "target_release": "",
        }
    ]
    sign_offs = dict(manifest["sign_offs"])
    sign_offs["support_owner"] = {
        "status": "pending",
        "approver": "support@store.korsenex.com",
        "date": "",
    }
    manifest["sign_offs"] = sign_offs

    report = assess_launch_readiness(
        manifest=manifest,
        release_gate_report=_base_release_gate_report(),
        generated_at="2026-04-19T10:00:00Z",
    )

    assert report["status"] == "hold"
    assert "severity_one_blockers_cleared" in report["failing_checks"]
    assert "required_sign_offs_complete" in report["failing_checks"]


def test_write_launch_readiness_report_writes_json_and_markdown(tmp_path: Path) -> None:
    report = assess_launch_readiness(
        manifest=_base_manifest(),
        release_gate_report=_base_release_gate_report(),
        generated_at="2026-04-19T10:00:00Z",
    )
    json_path = tmp_path / "launch-readiness-report.json"
    markdown_path = tmp_path / "launch-readiness-report.md"

    write_launch_readiness_report(
        report,
        output_path=json_path,
        markdown_output_path=markdown_path,
    )

    assert json.loads(json_path.read_text(encoding="utf-8"))["status"] == "ready"
    assert "# V2 Launch Readiness Report" in markdown_path.read_text(encoding="utf-8")
