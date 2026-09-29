"""Resolve mixed drag-drop input (files, folders, multi-select) into job inputs."""

from __future__ import annotations

import os

from uvr.utils.file_utils import is_supported_audio


class InputResolver:
    """Pure helpers; single funnel for drop zone, file picker, folder picker."""

    @staticmethod
    def resolve(paths: list[str]) -> tuple[list[str], list[str]]:
        """Split ``paths`` into ``(accepted, rejected)`` audio inputs.

        Directories are scanned recursively; only files passing
        ``is_supported_audio`` are accepted. Both lists are sorted and
        deduplicated; missing paths land in ``rejected``.
        """
        accepted: set[str] = set()
        rejected: set[str] = set()
        for path in paths:
            if os.path.isdir(path):
                for dirpath, _dirnames, filenames in os.walk(path):
                    for name in filenames:
                        full = os.path.abspath(os.path.join(dirpath, name))
                        if is_supported_audio(full):
                            accepted.add(full)
                        else:
                            rejected.add(full)
            elif os.path.isfile(path):
                if is_supported_audio(path):
                    accepted.add(os.path.abspath(path))
                else:
                    rejected.add(path)
            else:
                rejected.add(path)
        return sorted(accepted), sorted(rejected)
