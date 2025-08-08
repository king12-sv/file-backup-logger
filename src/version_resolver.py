# -*- coding: utf-8 -*-
"""
version_resolver.py
-------------------
Detect a version string from the source folder:
- In "manual" mode use config["manual_version"]
- In "auto" mode scan common files and parse a version
If no version is found, return "" (omit suffix).
"""
from __future__ import annotations

import os
import json
import re

class VersionResolver:
    def __init__(self, config) -> None:
        self.config = config

    def get_version_for_source(self, source_folder: str) -> str:
        mode = (self.config.get("version_mode", "auto") or "auto").lower()
        if mode == "manual":
            return (self.config.get("manual_version", "") or "").strip()

        # auto mode
        prefs = self.config.get("preferred_version_files", []) or []
        for fname in prefs:
            fpath = os.path.join(source_folder, fname)
            if not os.path.isfile(fpath):
                continue
            try:
                if fname == "package.json":
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    v = str(data.get("version", "")).strip()
                    if v:
                        return self._normalize(v)
                else:
                    with open(fpath, "r", encoding="utf-8") as f:
                        text = f.read()
                    # Examples: version = "1.2.3", __version__="0.9.1", tool.poetry.version = "x.y.z"
                    m = re.search(r"(?:__version__|version)\s*[:=]\s*[\"']([^\"']+)[\"']", text, re.I)
                    if m:
                        return self._normalize(m.group(1))
                    m = re.search(r"tool\.poetry\.version\s*=\s*[\"']([^\"']+)[\"']", text, re.I)
                    if m:
                        return self._normalize(m.group(1))
                    m = re.search(r"^\s*version\s*=\s*([^\s]+)\s*$", text, re.I | re.M)
                    if m:
                        return self._normalize(m.group(1))
                    m = re.search(r"^\s*([0-9]+(?:[\.\-][0-9A-Za-z]+)*)\s*$", text, re.M)
                    if m:
                        return self._normalize(m.group(1))
            except Exception:
                continue
        return ""

    def _normalize(self, v: str) -> str:
        v = v.strip()
        v = v[1:] if v.lower().startswith("v") else v
        v = v.replace(" ", "").replace("/", "-")
        v = v.replace(":", "-").replace(".", "-")
        return v
