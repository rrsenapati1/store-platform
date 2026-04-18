from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "verify_retained_release_evidence.py"
    spec = importlib.util.spec_from_file_location("verify_retained_release_evidence_script", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_verify_retained_release_evidence_script_writes_report(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    module = _load_script_module()
    report_path = tmp_path / "retrieval-report.json"

    class FakeReport:
        status = "passed"

        def to_dict(self) -> dict[str, object]:
            return {"status": "passed", "environment": "prod", "release_version": "2026.04.19"}

    monkeypatch.setattr(module, "Settings", lambda: object())
    monkeypatch.setattr(module, "verify_retained_release_evidence", lambda **_: FakeReport())
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "verify_retained_release_evidence.py",
            "--environment",
            "prod",
            "--release-version",
            "2026.04.19",
            "--output-dir",
            str(tmp_path / "retrieved"),
            "--report-path",
            str(report_path),
        ],
    )

    assert module.main() == 0
    assert json.loads(report_path.read_text(encoding="utf-8"))["status"] == "passed"


def test_verify_retained_release_evidence_script_returns_non_zero_on_failed_report(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = _load_script_module()

    class FakeReport:
        status = "failed"

        def to_dict(self) -> dict[str, object]:
            return {"status": "failed"}

    monkeypatch.setattr(module, "Settings", lambda: object())
    monkeypatch.setattr(module, "verify_retained_release_evidence", lambda **_: FakeReport())
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "verify_retained_release_evidence.py",
            "--environment",
            "prod",
            "--release-version",
            "2026.04.19",
            "--output-dir",
            str(tmp_path / "retrieved"),
        ],
    )

    assert module.main() == 1
