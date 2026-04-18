from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "retain_release_evidence.py"
    spec = importlib.util.spec_from_file_location("retain_release_evidence_script", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_retain_release_evidence_script_writes_manifest(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    module = _load_script_module()
    retention_manifest_path = tmp_path / "published" / "prod-2026.04.19.offsite-retention.json"

    def fake_run_release_evidence_retention(*_: object, **__: object):
        retention_manifest_path.parent.mkdir(parents=True, exist_ok=True)
        retention_manifest_path.write_text(json.dumps({"environment": "prod"}), encoding="utf-8")
        return type(
            "Plan",
            (),
            {
                "bucket": "store-platform-prod",
                "archive_key": "control-plane/prod/release-evidence/prod/2026.04.19/store-release-evidence-prod-2026.04.19.tar.gz",
                "publication_manifest_key": "control-plane/prod/release-evidence/prod/2026.04.19/prod-2026.04.19.publication.json",
                "catalog_key": "control-plane/prod/release-evidence/release-evidence-catalog.json",
                "retention_manifest_key": "control-plane/prod/release-evidence/prod/2026.04.19/prod-2026.04.19.offsite-retention.json",
                "retention_manifest_path": retention_manifest_path,
            },
        )()

    monkeypatch.setattr(module, "Settings", lambda: object())
    monkeypatch.setattr(module, "run_release_evidence_retention", fake_run_release_evidence_retention)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "retain_release_evidence.py",
            "--publication-dir",
            str(tmp_path / "published"),
            "--environment",
            "prod",
            "--release-version",
            "2026.04.19",
        ],
    )

    assert module.main() == 0
    assert json.loads(retention_manifest_path.read_text(encoding="utf-8"))["environment"] == "prod"


def test_retain_release_evidence_script_returns_non_zero_on_failure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    module = _load_script_module()

    def fake_run_release_evidence_retention(*_: object, **__: object):
        raise FileNotFoundError("publication directory missing")

    monkeypatch.setattr(module, "Settings", lambda: object())
    monkeypatch.setattr(module, "run_release_evidence_retention", fake_run_release_evidence_retention)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "retain_release_evidence.py",
            "--publication-dir",
            str(tmp_path / "published"),
            "--environment",
            "prod",
            "--release-version",
            "2026.04.19",
        ],
    )

    assert module.main() == 1
