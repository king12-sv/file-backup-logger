# -*- coding: utf-8 -*-
"""
logger_setup.py
---------------
Centralized logging configuration.
Writes human-readable logs to 'backup.log' at project root.
"""
import logging
import os

def get_logger(base_dir: str) -> logging.Logger:
    logger = logging.getLogger("file_backup_logger")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        log_path = os.path.join(base_dir, "backup.log")
        fh = logging.FileHandler(log_path, encoding="utf-8")
        fmt = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        fh.setFormatter(fmt)
        logger.addHandler(fh)

        ch = logging.StreamHandler()
        ch.setFormatter(fmt)
        logger.addHandler(ch)

        logger.info("Logger initialized")
    return logger
