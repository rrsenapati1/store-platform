from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "run_release_gate.py"
    spec = importlib.util.spec_from_file_location("run_release_gate_script", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_run_release_gate_script_exits_zero_on_passed_gate(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    module = _load_script_module()
    output_dir = tmp_path / "release-gate"
    report_path = output_dir / "release-gate-report.json"

    def fake_run_release_gate(**_: object) -> dict[str, object]:
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps({"status": "passed"}), encoding="utf-8")
        return {
            "status": "passed",
            "report_path": str(report_path),
        }

    monkeypatch.setattr(module, "run_release_gate", fake_run_release_gate)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_release_gate.py",
            "--base-url",
            "https://control.store.korsenex.com",
            "--expected-environment",
            "prod",
            "--expected-release-version",
            "2026.04.19",
            "--release-owner",
            "ops@store.korsenex.com",
            "--output-dir",
            str(output_dir),
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
            "--image-ref",
            "store-control-plane-api:prod",
        ],
    )

    assert module.main() == 0
    assert json.loads(report_path.read_text(encoding="utf-8"))["status"] == "passed"


def test_run_release_gate_script_exits_non_zero_on_blocked_gate(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    module = _load_script_module()
    monkeypatch.setattr(
        module,
        "run_release_gate",
        lambda **_: {
            "status": "blocked",
            "summary": "retained evidence retrieval verification failed",
            "report_path": str(tmp_path / "release-gate-report.json"),
        },
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_release_gate.py",
            "--base-url",
            "https://control.store.korsenex.com",
            "--expected-environment",
            "prod",
            "--expected-release-version",
            "2026.04.19",
            "--release-owner",
            "ops@store.korsenex.com",
            "--output-dir",
            str(tmp_path / "release-gate"),
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
            "--image-ref",
            "store-control-plane-api:prod",
        ],
    )

    assert module.main() == 1
