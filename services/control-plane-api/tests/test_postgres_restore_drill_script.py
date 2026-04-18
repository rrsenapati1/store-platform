from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "run_restore_drill.py"
    spec = importlib.util.spec_from_file_location("run_restore_drill_script", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class _FakeReport:
    def __init__(self, *, status: str) -> None:
        self.status = status

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "source": {
                "bucket": "store-platform-staging",
                "dump_key": "control-plane/staging/postgres-backups/restore.dump",
                "metadata_key": "control-plane/staging/postgres-backups/metadata.json",
            },
            "target": {"target_database_url": "postgresql://store:***@db.internal:5432/store_restore"},
            "restored_manifest": {
                "environment": "staging",
                "release_version": "2026.04.18-rc1",
                "alembic_head": "20260418_0044_restore_drill_foundation",
            },
            "health_result": {"status": "passed"},
            "verification_result": {"status": "skipped"},
            "failure_reason": None if self.status == "passed" else "post-restore health verification failed",
        }


def test_run_restore_drill_script_requires_yes_for_destructive_execution(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_script_module()
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_restore_drill.py",
            "--dump-key",
            "control-plane/staging/postgres-backups/restore.dump",
            "--metadata-key",
            "control-plane/staging/postgres-backups/metadata.json",
            "--target-database-url",
            "postgresql+asyncpg://store:secret@db.internal:5432/store_restore",
            "--output-path",
            "restore-report.json",
        ],
    )

    with pytest.raises(SystemExit, match="--yes"):
        module.main()


def test_run_restore_drill_script_writes_json_report(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    module = _load_script_module()
    output_path = tmp_path / "restore-report.json"
    calls: list[dict[str, object]] = []

    def fake_run_restore_drill(**kwargs: object) -> _FakeReport:
        calls.append(kwargs)
        return _FakeReport(status="passed")

    def fake_write_restore_drill_report(report: _FakeReport, destination: Path) -> Path:
        destination.write_text(json.dumps(report.to_dict()), encoding="utf-8")
        return destination

    monkeypatch.setattr(module, "Settings", lambda: object())
    monkeypatch.setattr(module, "run_postgres_restore_drill", fake_run_restore_drill)
    monkeypatch.setattr(module, "write_restore_drill_report", fake_write_restore_drill_report)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_restore_drill.py",
            "--dump-key",
            "control-plane/staging/postgres-backups/restore.dump",
            "--metadata-key",
            "control-plane/staging/postgres-backups/metadata.json",
            "--target-database-url",
            "postgresql+asyncpg://store:secret@db.internal:5432/store_restore",
            "--output-path",
            str(output_path),
            "--yes",
        ],
    )

    exit_code = module.main()

    assert exit_code == 0
    assert calls[0]["verify_smoke"] is False
    assert json.loads(output_path.read_text(encoding="utf-8"))["status"] == "passed"
    assert "status=passed" in capsys.readouterr().out


def test_run_restore_drill_script_returns_non_zero_on_failed_report(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    module = _load_script_module()
    output_path = tmp_path / "restore-report.json"

    def fake_write_restore_drill_report(report: _FakeReport, destination: Path) -> Path:
        destination.write_text(json.dumps(report.to_dict()), encoding="utf-8")
        return destination

    monkeypatch.setattr(module, "Settings", lambda: object())
    monkeypatch.setattr(module, "run_postgres_restore_drill", lambda **_: _FakeReport(status="failed"))
    monkeypatch.setattr(module, "write_restore_drill_report", fake_write_restore_drill_report)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_restore_drill.py",
            "--dump-key",
            "control-plane/staging/postgres-backups/restore.dump",
            "--metadata-key",
            "control-plane/staging/postgres-backups/metadata.json",
            "--target-database-url",
            "postgresql+asyncpg://store:secret@db.internal:5432/store_restore",
            "--output-path",
            str(output_path),
            "--yes",
        ],
    )

    assert module.main() == 1
    assert json.loads(output_path.read_text(encoding="utf-8"))["status"] == "failed"

