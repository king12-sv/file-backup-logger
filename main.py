# -*- coding: utf-8 -*-
"""
main.py — entry point for the Tkinter GUI.
"""
from __future__ import annotations

import os
import sys
import tkinter as tk
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.gui import BackupGUI  # noqa


def main():
    base_dir = str(PROJECT_ROOT)
    config_path = os.path.join(base_dir, "config.json")

    root = tk.Tk()
    app = BackupGUI(root, config_path=config_path, project_root=base_dir)
    root.mainloop()


if __name__ == "__main__":
    main()
