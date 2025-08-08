# -*- coding: utf-8 -*-
"""
backup.py
----------
Core backup logic implemented with OOP (BackupManager):
- Plain copy or ZIP mode
- Timestamp + version suffix in backup names
- Logging (backup.log) with file count & duration
- Robust error handling
- Config persistence via ConfigManager
"""
from __future__ import annotations

import os
import shutil
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .config_manager import ConfigManager
from .version_resolver import VersionResolver


def ensure_dir(path: str) -> None:
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


@dataclass
class BackupResult:
    success: bool
    message: str
    backup_path: Optional[str]
    file_count: int = 0
    duration_seconds: float = 0.0


class BackupManager:
    def __init__(self, config: ConfigManager, logger: logging.Logger) -> None:
        self.config = config
        self.log = logger
        self.version_resolver = VersionResolver(config)

    def run_backup(self, source: Optional[str] = None, destination: Optional[str] = None,
                   use_zip: Optional[bool] = None) -> BackupResult:
        """Run a backup. Parameters override values from config.json."""
        src = source or self.config.get("source", "")
        dst = destination or self.config.get("destination", "")
        zip_mode = self._resolve_zip_mode(use_zip)

        if not src or not os.path.isdir(src):
            msg = f"Source folder does not exist or is not set: '{src}'"
            self.log.error(msg)
            return BackupResult(False, msg, None)

        if not dst:
            msg = "Destination folder is not set."
            self.log.error(msg)
            return BackupResult(False, msg, None)

        try:
            ensure_dir(dst)
        except Exception as e:
            msg = f"Cannot create destination folder '{dst}': {e}"
            self.log.error(msg)
            return BackupResult(False, msg, None)

        # Prepare backup name
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        version = self.version_resolver.get_version_for_source(src)
        version_suffix = f"_v{version}" if version else ""
        backup_name = f"backup_{ts}{version_suffix}"
        backup_base_path = os.path.join(dst, backup_name)

        # Metrics
        start = datetime.now()
        file_count = self._count_files(src)

        try:
            if zip_mode:
                archive = shutil.make_archive(backup_base_path, "zip", root_dir=src)
                backup_path = archive
            else:
                shutil.copytree(src, backup_base_path)
                backup_path = backup_base_path

            duration = (datetime.now() - start).total_seconds()
            msg = (f"Backup successful -> {backup_path} | files={file_count} | "
                   f"duration={duration:.2f}s | zip={zip_mode}")
            self.log.info(msg)
            return BackupResult(True, msg, backup_path, file_count, duration)

        except shutil.Error as e:
            duration = (datetime.now() - start).total_seconds()
            msg = f"Backup failed (shutil.Error): {e}"
            self.log.exception(msg)
            return BackupResult(False, msg, None, file_count, duration)

        except PermissionError as e:
            duration = (datetime.now() - start).total_seconds()
            msg = f"Backup failed (permission): {e}"
            self.log.exception(msg)
            return BackupResult(False, msg, None, file_count, duration)

        except Exception as e:
            duration = (datetime.now() - start).total_seconds()
            msg = f"Backup failed: {e}"
            self.log.exception(msg)
            return BackupResult(False, msg, None, file_count, duration)

    def _resolve_zip_mode(self, use_zip: Optional[bool]) -> bool:
        if use_zip is not None:
            return bool(use_zip)
        return bool(self.config.get("zip", False))

    @staticmethod
    def _count_files(folder: str) -> int:
        count = 0
        for _, _, files in os.walk(folder):
            count += len(files)
        return count
