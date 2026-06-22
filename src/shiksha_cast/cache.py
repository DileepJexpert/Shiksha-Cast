from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def content_hash(*parts: str) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(p.encode())
    return h.hexdigest()[:16]


class BuildManifest:
    def __init__(self, build_dir: Path):
        self.build_dir = build_dir
        self.path = build_dir / "manifest.json"
        self._data: dict[str, Any] = {}
        if self.path.exists():
            with open(self.path) as f:
                self._data = json.load(f)

    def get(self, stage: str, key: str) -> dict | None:
        return self._data.get(stage, {}).get(key)

    def set(self, stage: str, key: str, value: dict) -> None:
        if stage not in self._data:
            self._data[stage] = {}
        self._data[stage][key] = value

    def save(self) -> None:
        self.build_dir.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w") as f:
            json.dump(self._data, f, indent=2)
