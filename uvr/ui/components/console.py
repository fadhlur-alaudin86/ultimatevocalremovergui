"""Thread-safe Tkinter text console for asynchronous log streaming.
"""

from __future__ import annotations

import queue
import tkinter as tk
from typing import Any


class ThreadSafeConsole(tk.Text):
    """Text Widget which is thread-safe for background worker log output."""

    def __init__(self, master: Any, **options: Any):
        super().__init__(master, **options)
        self.queue: queue.Queue = queue.Queue()
        self.update_me()

    def write(self, line: str) -> None:
        """Enqueue line to be safely displayed on next GUI event tick."""
        self.queue.put(line)

    def clear(self) -> None:
        """Enqueue command to clear console text."""
        self.queue.put(None)

    def update_me(self) -> None:
        """Drain background message queue onto the Tk text widget."""
        self.configure(state=tk.NORMAL)
        try:
            while True:
                line = self.queue.get_nowait()
                if line is None:
                    self.delete(1.0, tk.END)
                else:
                    self.insert(tk.END, str(line))
                self.see(tk.END)
                self.update_idletasks()
        except queue.Empty:
            pass
        self.configure(state=tk.DISABLED)
        self.after(100, self.update_me)

    def copy_text(self) -> None:
        """Copy currently highlighted console text to clipboard."""
        try:
            highlighted = self.selection_get()
            self.clipboard_clear()
            self.clipboard_append(highlighted)
        except Exception:
            pass

    def select_all_text(self) -> None:
        """Select all text in console."""
        self.tag_add("sel", "1.0", "end")
