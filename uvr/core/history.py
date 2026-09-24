"""Processing history recording and CSV export service.
"""

from __future__ import annotations

import csv
import json
import logging
import os
import threading
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_HISTORY_FILE = os.path.join("gui_data", "processing_history.json")


class HistoryManager:
    """Thread-safe persistent tracker for audio processing batch runs."""

    def __init__(self, history_file: str = DEFAULT_HISTORY_FILE) -> None:
        self.history_file = history_file
        self._lock = threading.RLock()
        self._records: list[dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        with self._lock:
            if os.path.isfile(self.history_file):
                try:
                    with open(self.history_file, encoding="utf-8") as f:
                        self._records = json.load(f)
                except Exception as exc:
                    logger.warning("Failed loading history from %s: %s", self.history_file, exc)
                    self._records = []

    def _save(self) -> None:
        with self._lock:
            try:
                os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
                with open(self.history_file, "w", encoding="utf-8") as f:
                    json.dump(self._records, f, indent=2)
            except Exception as exc:
                logger.error("Failed writing history to %s: %s", self.history_file, exc)

    def add_entry(
        self,
        task_id: int,
        process_method: str,
        model_name: str,
        input_files: list[str],
        export_path: str,
        duration_seconds: float,
        status: str = "Completed",
        error: str | None = None,
    ) -> dict[str, Any]:
        """Record a completed or failed task run."""
        record = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "task_id": task_id,
            "process_method": process_method,
            "model_name": model_name,
            "input_files": input_files,
            "export_path": export_path,
            "duration_seconds": round(duration_seconds, 2),
            "status": status,
            "error": error or "",
        }
        with self._lock:
            self._records.append(record)
            self._save()
        return record

    def get_records(self) -> list[dict[str, Any]]:
        """Return a copy of all recorded history entries."""
        with self._lock:
            return list(self._records)

    def export_csv(self, csv_path: str) -> bool:
        """Export history entries to a standard CSV file."""
        with self._lock:
            if not self._records:
                return False
            try:
                fieldnames = [
                    "timestamp",
                    "task_id",
                    "process_method",
                    "model_name",
                    "input_files",
                    "export_path",
                    "duration_seconds",
                    "status",
                    "error",
                ]
                with open(csv_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for r in self._records:
                        row = dict(r)
                        row["input_files"] = "; ".join(row.get("input_files", []))
                        writer.writerow(row)
                return True
            except Exception as exc:
                logger.error("Failed exporting history CSV to %s: %s", csv_path, exc)
                return False

    def clear(self) -> None:
        """Clear all historical records."""
        with self._lock:
            self._records.clear()
            self._save()
