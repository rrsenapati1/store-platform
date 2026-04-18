from __future__ import annotations

import json
from pathlib import Path
import tarfile

from store_control_plane.release_evidence_publication import publish_release_evidence_bundle


def _create_bundle(root: Path) -> Path:
    bundle_dir = root / "evidence-bundle"
    (bundle_dir / "reports").mkdir(parents=True)
    (bundle_dir / "artifacts" / "sbom-artifacts").mkdir(parents=True)
    (bundle_dir / "reports" / "release-candidate-evidence.md").write_text(
        "# Release Candidate Evidence\n",
        encoding="utf-8",
    )
    (bundle_dir / "reports" / "certification-report.json").write_text(
        json.dumps(
            {
                "status": "approved",
                "environment": "prod",
                "release_version": "2026.04.19",
            }
        ),
        encoding="utf-8",
    )
    (bundle_dir / "reports" / "launch-readiness-report.json").write_text(
        json.dumps({"status": "ready"}),
        encoding="utf-8",
    )
    (bundle_dir / "reports" / "launch-readiness-manifest.json").write_text(
        json.dumps({"release_version": "2026.04.19"}),
        encoding="utf-8",
    )
    (bundle_dir / "artifacts" / "sbom-artifacts" / "control-plane-api.cdx.json").write_text(
        '{"bomFormat":"CycloneDX"}',
        encoding="utf-8",
    )
    (bundle_dir / "bundle-manifest.json").write_text(
        json.dumps(
            {
                "status": "passed",
                "reports": {
                    "release_candidate_evidence": {
                        "bundle_path": "reports/release-candidate-evidence.md"
                    },
                    "certification_report": {
                        "bundle_path": "reports/certification-report.json"
                    },
                    "launch_readiness_report": {
                        "bundle_path": "reports/launch-readiness-report.json"
                    },
                    "launch_readiness_manifest": {
                        "bundle_path": "reports/launch-readiness-manifest.json"
                    },
                },
                "directories": {
                    "sbom_artifacts": {
                        "bundle_path": "artifacts/sbom-artifacts"
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    (bundle_dir / "bundle-index.md").write_text("# Release Evidence Bundle\n", encoding="utf-8")
    return bundle_dir


def test_publish_release_evidence_bundle_writes_archive_manifest_and_catalog(tmp_path: Path) -> None:
    bundle_dir = _create_bundle(tmp_path)
    output_dir = tmp_path / "published"

    result = publish_release_evidence_bundle(
        bundle_dir=bundle_dir,
        output_dir=output_dir,
        release_version="2026.04.19",
        environment="prod",
        published_at="2026-04-19T12:00:00Z",
    )

    assert result["status"] == "published"
    archive_path = Path(str(result["archive_path"]))
    manifest_path = Path(str(result["publication_manifest_path"]))
    catalog_path = Path(str(result["catalog_path"]))
    assert archive_path.exists()
    assert manifest_path.exists()
    assert catalog_path.exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["release_version"] == "2026.04.19"
    assert manifest["environment"] == "prod"
    assert manifest["certification_status"] == "approved"
    assert manifest["launch_readiness_status"] == "ready"
    assert manifest["bundle_manifest_sha256"]
    assert manifest["archive_sha256"]

    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    assert len(catalog["publications"]) == 1
    assert catalog["publications"][0]["release_version"] == "2026.04.19"
    assert catalog["publications"][0]["environment"] == "prod"
    assert catalog["publications"][0]["launch_readiness_status"] == "ready"

    with tarfile.open(archive_path, "r:gz") as archive:
        names = sorted(archive.getnames())
    assert "store-release-evidence-prod-2026.04.19/bundle-manifest.json" in names
    assert "store-release-evidence-prod-2026.04.19/reports/certification-report.json" in names
    assert "store-release-evidence-prod-2026.04.19/reports/launch-readiness-report.json" in names
    assert "store-release-evidence-prod-2026.04.19/artifacts/sbom-artifacts/control-plane-api.cdx.json" in names


def test_publish_release_evidence_bundle_updates_existing_catalog_without_duplicates(tmp_path: Path) -> None:
    bundle_dir = _create_bundle(tmp_path)
    output_dir = tmp_path / "published"
    output_dir.mkdir()
    (output_dir / "release-evidence-catalog.json").write_text(
        json.dumps(
            {
                "publications": [
                    {
                        "environment": "staging",
                        "release_version": "2026.04.18",
                        "publication_manifest_path": "staging-2026.04.18.publication.json",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    publish_release_evidence_bundle(
        bundle_dir=bundle_dir,
        output_dir=output_dir,
        release_version="2026.04.19",
        environment="prod",
        published_at="2026-04-19T12:00:00Z",
    )
    publish_release_evidence_bundle(
        bundle_dir=bundle_dir,
        output_dir=output_dir,
        release_version="2026.04.19",
        environment="prod",
        published_at="2026-04-19T13:00:00Z",
    )

    catalog = json.loads((output_dir / "release-evidence-catalog.json").read_text(encoding="utf-8"))
    assert len(catalog["publications"]) == 2
    assert catalog["publications"][0]["release_version"] == "2026.04.19"
    assert catalog["publications"][1]["release_version"] == "2026.04.18"
