from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class JsonStateStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def load_snapshot(self) -> dict[str, Any] | None:
        if not self.path.exists():
            return None
        return json.loads(self.path.read_text(encoding="utf-8"))

    def save_snapshot(self, snapshot: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.path.with_suffix(f"{self.path.suffix}.tmp")
        temp_path.write_text(json.dumps(snapshot, indent=2, sort_keys=True), encoding="utf-8")
        temp_path.replace(self.path)
