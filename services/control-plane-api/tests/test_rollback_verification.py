from __future__ import annotations

import json
from pathlib import Path

from store_control_plane.rollback_verification import (
    build_rollback_verification_report,
    load_release_bundle_manifest,
    parse_release_version,
    summarize_rollback_verification_report,
    write_rollback_verification_report,
)


def test_parse_release_version_orders_rc_and_final_versions() -> None:
    assert parse_release_version("2026.04.18-rc1") < parse_release_version("2026.04.18")
    assert parse_release_version("2026.04.18-rc2") > parse_release_version("2026.04.18-rc1")


def test_build_rollback_verification_report_passes_for_schema_compatible_older_target() -> None:
    report = build_rollback_verification_report(
        environment="staging",
        current_release_version="2026.04.18",
        current_alembic_head="20260418_0049_rollback_verification_foundation",
        target_manifest={
            "release_version": "2026.04.18-rc2",
            "alembic_head": "20260418_0049_rollback_verification_foundation",
            "bundle_name": "store-control-plane-2026.04.18-rc2",
            "built_at": "2026-04-18T04:00:00Z",
        },
        generated_at="2026-04-18T12:00:00Z",
    )

    assert report.status == "passed"
    assert report.rollback_mode == "app_only"
    assert report.failure_reason is None


def test_build_rollback_verification_report_fails_when_schema_head_differs() -> None:
    report = build_rollback_verification_report(
        environment="staging",
        current_release_version="2026.04.18",
        current_alembic_head="20260418_0049_rollback_verification_foundation",
        target_manifest={
            "release_version": "2026.04.17",
            "alembic_head": "20260417_0048_previous_head",
            "bundle_name": "store-control-plane-2026.04.17",
            "built_at": "2026-04-17T04:00:00Z",
        },
        generated_at="2026-04-18T12:00:00Z",
    )

    assert report.status == "failed"
    assert report.rollback_mode == "restore_required"
    assert report.failure_reason == "target bundle schema head differs from deployed schema head"


def test_load_release_bundle_manifest_and_write_report(tmp_path: Path) -> None:
    manifest_path = tmp_path / "store-control-plane-2026.04.17.manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "release_version": "2026.04.17",
                "alembic_head": "20260418_0049_rollback_verification_foundation",
                "bundle_name": "store-control-plane-2026.04.17",
                "built_at": "2026-04-17T04:00:00Z",
            }
        ),
        encoding="utf-8",
    )

    manifest = load_release_bundle_manifest(manifest_path)
    report = build_rollback_verification_report(
        environment="staging",
        current_release_version="2026.04.18",
        current_alembic_head="20260418_0049_rollback_verification_foundation",
        target_manifest=manifest,
        generated_at="2026-04-18T12:00:00Z",
    )

    output_path = tmp_path / "rollback-report.json"
    write_rollback_verification_report(report, output_path=output_path)
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert payload["target_release_version"] == "2026.04.17"
    assert summarize_rollback_verification_report(report) == "rollback target verified for app-only rollback"
