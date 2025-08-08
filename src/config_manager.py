# -*- coding: utf-8 -*-
"""
config_manager.py
-----------------
JSON config manager for user preferences:
- source, destination, zip mode, backup interval
- versioning mode (auto/manual) and manual version value
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict


DEFAULT_CONFIG: Dict[str, Any] = {
    "source": "",
    "destination": "",
    "zip": True,
    "backup_interval_minutes": 0,   # 0 disables scheduler
    "version_mode": "auto",        # "auto" or "manual"
    "manual_version": "",          # used when version_mode == "manual"
    "preferred_version_files": [     # files scanned in auto mode
        "version.txt",
        "VERSION",
        "package.json",
        "pyproject.toml",
        "setup.cfg",
        "setup.py"
    ]
}


class ConfigManager:
    def __init__(self, path: str) -> None:
        self.path = path
        if not os.path.exists(self.path):
            self._write(DEFAULT_CONFIG)
        self._data = self._read()

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value) -> None:
        self._data[key] = value
        self._write(self._data)

    def as_dict(self) -> Dict[str, Any]:
        return dict(self._data)

    # ---------- internals ----------
    def _read(self) -> Dict[str, Any]:
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data: Dict[str, Any]) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
