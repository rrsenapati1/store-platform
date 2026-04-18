from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "build_release_evidence_bundle.py"
    spec = importlib.util.spec_from_file_location("build_release_evidence_bundle_script", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_build_release_evidence_bundle_script_writes_manifest(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    module = _load_script_module()
    output_dir = tmp_path / "evidence-bundle"
    manifest_path = output_dir / "bundle-manifest.json"

    def fake_build_release_evidence_bundle(**_: object) -> dict[str, object]:
        output_dir.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps({"status": "passed"}), encoding="utf-8")
        return {
            "status": "passed",
            "manifest_path": str(manifest_path),
            "output_dir": str(output_dir),
            "summary": "bundle assembled",
        }

    monkeypatch.setattr(module, "build_release_evidence_bundle", fake_build_release_evidence_bundle)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_release_evidence_bundle.py",
            "--output-dir",
            str(output_dir),
            "--release-evidence",
            str(tmp_path / "release-candidate-evidence.md"),
        ],
    )

    assert module.main() == 0
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["status"] == "passed"


def test_build_release_evidence_bundle_script_exits_non_zero_on_failed_bundle(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = _load_script_module()

    monkeypatch.setattr(
        module,
        "build_release_evidence_bundle",
        lambda **_: {
            "status": "failed",
            "manifest_path": str(tmp_path / "bundle-manifest.json"),
            "output_dir": str(tmp_path / "evidence-bundle"),
            "summary": "missing release evidence",
        },
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_release_evidence_bundle.py",
            "--output-dir",
            str(tmp_path / "evidence-bundle"),
            "--release-evidence",
            str(tmp_path / "release-candidate-evidence.md"),
        ],
    )

    assert module.main() == 1
