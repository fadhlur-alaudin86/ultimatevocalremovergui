"""Shared UI state: event bus and versioned config store."""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable

logger = logging.getLogger(__name__)


class EventBus:
    """Minimal thread-safe pub/sub for service -> view updates."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._subs: dict[str, list[Callable]] = {}

    def subscribe(self, topic: str, fn: Callable) -> None:
        with self._lock:
            self._subs.setdefault(topic, []).append(fn)

    def publish(self, topic: str, payload=None) -> None:
        with self._lock:
            fns = list(self._subs.get(topic, []))
        for fn in fns:
            try:
                fn(payload)
            except Exception:
                logger.exception("event subscriber failed for topic %s", topic)


class ConfigStore:
    """Versioned key/value settings holder (settings schema v2)."""

    VERSION = 2

    def __init__(self, initial: dict | None = None) -> None:
        self._lock = threading.Lock()
        self._data: dict = {"version": self.VERSION}
        if initial:
            self._data.update(initial)

    def get(self, key: str, default=None):
        with self._lock:
            return self._data.get(key, default)

    def set(self, key: str, value) -> None:
        with self._lock:
            self._data[key] = value

    def as_dict(self) -> dict:
        with self._lock:
            return dict(self._data)
