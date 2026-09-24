"""Logging configuration module for UVR.

Configures structured logging across console and persistent log files.
"""

from __future__ import annotations

import logging
import os
import sys

from uvr.constants import BASE_PATH

DEFAULT_LOG_FILE = os.path.join(BASE_PATH, "uvr.log")


def setup_logging(
    log_file: str | None = DEFAULT_LOG_FILE,
    level: int = logging.INFO,
) -> None:
    """Initialize root logging configuration for UVR.

    Args:
        log_file: Optional path to log file. If None, file logging is disabled.
        level: Logging level (e.g. logging.INFO, logging.DEBUG).
    """
    handlers: list[logging.Handler] = []

    # Console stream handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%H:%M:%S",
    )
    console_handler.setFormatter(console_formatter)
    handlers.append(console_handler)

    # File handler
    if log_file:
        try:
            log_dir = os.path.dirname(os.path.abspath(log_file))
            os.makedirs(log_dir, exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_formatter = logging.Formatter(
                "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
            )
            file_handler.setFormatter(file_formatter)
            handlers.append(file_handler)
        except Exception as exc:
            print(f"Warning: Failed to setup file logger at {log_file}: {exc}")

    logging.basicConfig(level=level, handlers=handlers, force=True)


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger for the given module name."""
    return logging.getLogger(name)
