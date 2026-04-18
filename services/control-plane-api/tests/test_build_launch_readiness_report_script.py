from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "build_launch_readiness_report.py"
    spec = importlib.util.spec_from_file_location("build_launch_readiness_report_script", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_build_launch_readiness_report_script_writes_ready_report(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = _load_script_module()
    report_path = tmp_path / "launch-readiness-report.json"
    markdown_path = tmp_path / "launch-readiness-report.md"

    def fake_build_launch_readiness_report(**_: object) -> dict[str, object]:
        report_path.write_text(json.dumps({"status": "ready"}), encoding="utf-8")
        markdown_path.write_text("# V2 Launch Readiness Report\n", encoding="utf-8")
        return {
            "status": "ready",
            "output_path": str(report_path),
            "markdown_output_path": str(markdown_path),
            "summary": "launch readiness ready",
        }

    monkeypatch.setattr(module, "build_launch_readiness_report", fake_build_launch_readiness_report)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_launch_readiness_report.py",
            "--launch-manifest",
            str(tmp_path / "launch-manifest.json"),
            "--release-gate-report",
            str(tmp_path / "release-gate-report.json"),
            "--output-path",
            str(report_path),
            "--markdown-output-path",
            str(markdown_path),
        ],
    )

    assert module.main() == 0
    assert json.loads(report_path.read_text(encoding="utf-8"))["status"] == "ready"


def test_build_launch_readiness_report_script_exits_non_zero_on_hold(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = _load_script_module()

    monkeypatch.setattr(
        module,
        "build_launch_readiness_report",
        lambda **_: {
            "status": "hold",
            "output_path": str(tmp_path / "launch-readiness-report.json"),
            "markdown_output_path": str(tmp_path / "launch-readiness-report.md"),
            "summary": "launch readiness hold",
        },
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_launch_readiness_report.py",
            "--launch-manifest",
            str(tmp_path / "launch-manifest.json"),
            "--release-gate-report",
            str(tmp_path / "release-gate-report.json"),
        ],
    )

    assert module.main() == 1
