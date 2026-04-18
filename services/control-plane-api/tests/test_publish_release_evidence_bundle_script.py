from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "publish_release_evidence_bundle.py"
    spec = importlib.util.spec_from_file_location("publish_release_evidence_bundle_script", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_publish_release_evidence_bundle_script_writes_manifest(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = _load_script_module()
    output_dir = tmp_path / "published"
    manifest_path = output_dir / "prod-2026.04.19.publication.json"

    def fake_publish_release_evidence_bundle(**_: object) -> dict[str, object]:
        output_dir.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps({"status": "published"}), encoding="utf-8")
        return {
            "status": "published",
            "archive_path": str(output_dir / "store-release-evidence-prod-2026.04.19.tar.gz"),
            "publication_manifest_path": str(manifest_path),
            "catalog_path": str(output_dir / "release-evidence-catalog.json"),
            "summary": "published release evidence",
        }

    monkeypatch.setattr(module, "publish_release_evidence_bundle", fake_publish_release_evidence_bundle)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "publish_release_evidence_bundle.py",
            "--bundle-dir",
            str(tmp_path / "bundle"),
            "--output-dir",
            str(output_dir),
            "--environment",
            "prod",
            "--release-version",
            "2026.04.19",
        ],
    )

    assert module.main() == 0
    assert json.loads(manifest_path.read_text(encoding="utf-8"))["status"] == "published"


def test_publish_release_evidence_bundle_script_exits_non_zero_on_failed_publication(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = _load_script_module()
    monkeypatch.setattr(
        module,
        "publish_release_evidence_bundle",
        lambda **_: {
            "status": "failed",
            "summary": "bundle directory missing",
            "publication_manifest_path": str(tmp_path / "prod-2026.04.19.publication.json"),
        },
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "publish_release_evidence_bundle.py",
            "--bundle-dir",
            str(tmp_path / "bundle"),
            "--output-dir",
            str(tmp_path / "published"),
            "--environment",
            "prod",
            "--release-version",
            "2026.04.19",
        ],
    )

    assert module.main() == 1
