from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "run_v2_launch_gate.py"
    spec = importlib.util.spec_from_file_location("run_v2_launch_gate_script", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_run_v2_launch_gate_script_exits_zero_on_ready(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    module = _load_script_module()
    output_dir = tmp_path / "v2-launch-gate"
    report_path = output_dir / "v2-launch-gate-report.json"

    def fake_run_v2_launch_gate(**_: object) -> dict[str, object]:
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps({"status": "ready"}), encoding="utf-8")
        return {
            "status": "ready",
            "report_path": str(report_path),
        }

    monkeypatch.setattr(module, "run_v2_launch_gate", fake_run_v2_launch_gate)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_v2_launch_gate.py",
            "--base-url",
            "https://control.store.korsenex.com",
            "--expected-environment",
            "prod",
            "--expected-release-version",
            "2026.04.19",
            "--release-owner",
            "release@store.korsenex.com",
            "--output-dir",
            str(output_dir),
            "--launch-manifest",
            str(tmp_path / "v2-launch-readiness-manifest.json"),
            "--admin-bearer-token",
            "admin-token",
            "--branch-bearer-token",
            "branch-token",
            "--tenant-id",
            "tenant-1",
            "--branch-id",
            "branch-1",
            "--product-id",
            "product-1",
            "--dump-key",
            "control-plane/prod/postgres-backups/restore.dump",
            "--metadata-key",
            "control-plane/prod/postgres-backups/metadata.json",
            "--target-database-url",
            "postgresql+asyncpg://store:secret@db.internal:5432/store_restore",
        ],
    )

    assert module.main() == 0
    assert json.loads(report_path.read_text(encoding="utf-8"))["status"] == "ready"


def test_run_v2_launch_gate_script_exits_non_zero_on_hold(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    module = _load_script_module()
    monkeypatch.setattr(
        module,
        "run_v2_launch_gate",
        lambda **_: {
            "status": "hold",
            "summary": "launch readiness hold",
            "report_path": str(tmp_path / "v2-launch-gate-report.json"),
        },
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_v2_launch_gate.py",
            "--base-url",
            "https://control.store.korsenex.com",
            "--expected-environment",
            "prod",
            "--expected-release-version",
            "2026.04.19",
            "--release-owner",
            "release@store.korsenex.com",
            "--output-dir",
            str(tmp_path / "v2-launch-gate"),
            "--launch-manifest",
            str(tmp_path / "v2-launch-readiness-manifest.json"),
            "--admin-bearer-token",
            "admin-token",
            "--branch-bearer-token",
            "branch-token",
            "--tenant-id",
            "tenant-1",
            "--branch-id",
            "branch-1",
            "--product-id",
            "product-1",
            "--dump-key",
            "control-plane/prod/postgres-backups/restore.dump",
            "--metadata-key",
            "control-plane/prod/postgres-backups/metadata.json",
            "--target-database-url",
            "postgresql+asyncpg://store:secret@db.internal:5432/store_restore",
        ],
    )

    assert module.main() == 1
