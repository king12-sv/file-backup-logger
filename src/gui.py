# -*- coding: utf-8 -*-
"""
gui.py
------
Tkinter GUI to:
- Select source and destination folders
- Toggle ZIP mode
- Choose version mode (auto/manual)
- Set manual version
- Set backup interval and start/stop the scheduler
- Trigger an immediate backup
"""
from __future__ import annotations

import threading
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from .config_manager import ConfigManager
from .logger_setup import get_logger
from .backup import BackupManager


class BackupGUI:
    def __init__(self, root, config_path: str, project_root: str):
        self.root = root
        self.root.title("File Backup Logger")
        self.root.geometry("740x520")

        self.config = ConfigManager(config_path)
        self.logger = get_logger(project_root)
        self.manager = BackupManager(self.config, self.logger)

        self.scheduler_thread = None
        self.scheduler_stop = threading.Event()

        pad = {"padx": 8, "pady": 6}

        # Source
        frm_source = ttk.Frame(root)
        frm_source.pack(fill="x", **pad)
        ttk.Label(frm_source, text="Source folder").pack(anchor="w")
        self.var_source = tk.StringVar(value=self.config.get("source", ""))
        ttk.Entry(frm_source, textvariable=self.var_source, width=70).pack(side="left", expand=True, fill="x")
        ttk.Button(frm_source, text="Browse...", command=self.choose_source).pack(side="left", padx=5)

        # Destination
        frm_dest = ttk.Frame(root)
        frm_dest.pack(fill="x", **pad)
        ttk.Label(frm_dest, text="Destination folder").pack(anchor="w")
        self.var_dest = tk.StringVar(value=self.config.get("destination", ""))
        ttk.Entry(frm_dest, textvariable=self.var_dest, width=70).pack(side="left", expand=True, fill="x")
        ttk.Button(frm_dest, text="Browse...", command=self.choose_dest).pack(side="left", padx=5)

        # ZIP checkbox
        frm_zip = ttk.Frame(root)
        frm_zip.pack(fill="x", **pad)
        self.var_zip = tk.BooleanVar(value=bool(self.config.get("zip", True)))
        ttk.Checkbutton(frm_zip, text="Create ZIP archive", variable=self.var_zip).pack(anchor="w")

        # Versioning
        frm_ver = ttk.LabelFrame(root, text="Versioning")
        frm_ver.pack(fill="x", **pad)
        self.var_mode = tk.StringVar(value=self.config.get("version_mode", "auto"))
        ttk.Radiobutton(frm_ver, text="Auto-detect", variable=self.var_mode, value="auto",
                        command=self._on_mode_change).pack(anchor="w")
        ttk.Radiobutton(frm_ver, text="Manual", variable=self.var_mode, value="manual",
                        command=self._on_mode_change).pack(anchor="w")

        frm_manual = ttk.Frame(frm_ver)
        frm_manual.pack(fill="x", **pad)
        ttk.Label(frm_manual, text="Manual version (e.g., 227-3-3)").pack(anchor="w")
        self.var_manual = tk.StringVar(value=self.config.get("manual_version", ""))
        ttk.Entry(frm_manual, textvariable=self.var_manual, width=30).pack(anchor="w")

        # Scheduler
        frm_int = ttk.LabelFrame(root, text="Scheduler")
        frm_int.pack(fill="x", **pad)
        ttk.Label(frm_int, text="Interval (minutes) — 0 disables").pack(anchor="w")
        self.var_interval = tk.IntVar(value=int(self.config.get("backup_interval_minutes", 0)))
        ttk.Spinbox(frm_int, from_=0, to=100000, textvariable=self.var_interval, width=10).pack(anchor="w")

        # Buttons
        frm_btns = ttk.Frame(root)
        frm_btns.pack(fill="x", **pad)
        ttk.Button(frm_btns, text="Run backup now", command=self.run_now).pack(side="left")
        ttk.Button(frm_btns, text="Start scheduler", command=self.start_scheduler).pack(side="left", padx=5)
        ttk.Button(frm_btns, text="Stop scheduler", command=self.stop_scheduler).pack(side="left", padx=5)

        self._on_mode_change()

    def choose_source(self):
        path = filedialog.askdirectory(title="Choose source folder")
        if path:
            self.var_source.set(path)
            self.config.set("source", path)

    def choose_dest(self):
        path = filedialog.askdirectory(title="Choose destination folder")
        if path:
            self.var_dest.set(path)
            self.config.set("destination", path)

    def _on_mode_change(self):
        mode = self.var_mode.get()
        self.config.set("version_mode", mode)

    def _save_current_options(self):
        self.config.set("zip", bool(self.var_zip.get()))
        self.config.set("manual_version", self.var_manual.get())
        self.config.set("backup_interval_minutes", int(self.var_interval.get()))

    def run_now(self):
        self._save_current_options()
        result = self.manager.run_backup(
            source=self.var_source.get(),
            destination=self.var_dest.get(),
            use_zip=self.var_zip.get(),
        )
        if result.success:
            messagebox.showinfo("Backup", f"Success!\n{result.message}")
        else:
            messagebox.showerror("Backup", f"Backup failed:\n{result.message}")

    def start_scheduler(self):
        self._save_current_options()
        interval = int(self.config.get("backup_interval_minutes", 0))
        if interval <= 0:
            messagebox.showwarning("Scheduler", "Please set a positive interval.")
            return

        if self.scheduler_thread and self.scheduler_thread.is_alive():
            messagebox.showinfo("Scheduler", "Scheduler is already running.")
            return

        self.scheduler_stop.clear()
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        messagebox.showinfo("Scheduler", "Scheduler started.")

    def stop_scheduler(self):
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_stop.set()
            messagebox.showinfo("Scheduler", "Scheduler stopped.")
        else:
            messagebox.showinfo("Scheduler", "No scheduler is running.")

    def _scheduler_loop(self):
        interval = int(self.config.get("backup_interval_minutes", 0))
        while not self.scheduler_stop.is_set():
            self.manager.run_backup()
            remaining = max(1, interval * 60)
            while remaining > 0 and not self.scheduler_stop.is_set():
                time.sleep(min(1, remaining))
                remaining -= 1
