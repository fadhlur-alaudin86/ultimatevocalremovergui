"""Cross-platform desktop notification service for audio processing events.
"""

from __future__ import annotations

import logging
import platform
import shutil
import subprocess

logger = logging.getLogger(__name__)


def send_notification(title: str, message: str) -> bool:
    """Deliver a non-blocking desktop notification to the operating system.

    Returns True if notification command was dispatched, False otherwise.
    """
    sys_name = platform.system()

    try:
        if sys_name == "Linux":
            if shutil.which("notify-send"):
                subprocess.Popen(
                    ["notify-send", title, message, "-a", "Ultimate Vocal Remover"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return True
        elif sys_name == "Darwin":
            script = f'display notification "{message}" with title "{title}"'
            subprocess.Popen(
                ["osascript", "-e", script],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        elif sys_name == "Windows":
            # Using PowerShell toast notification
            ps_script = (
                f'[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, '
                f'ContentType = WindowsRuntime] > $null; '
                f'$template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02); '
                f'$textNodes = $template.GetElementsByTagName("text"); '
                f'$textNodes.Item(0).AppendChild($template.CreateTextNode("{title}")) > $null; '
                f'$textNodes.Item(1).AppendChild($template.CreateTextNode("{message}")) > $null; '
                f'$toast = [Windows.UI.Notifications.ToastNotification]::new($template); '
                f'[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Ultimate Vocal Remover").Show($toast)'
            )
            subprocess.Popen(
                ["powershell", "-NoProfile", "-Command", ps_script],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
    except Exception as exc:
        logger.debug("Desktop notification dispatch skipped: %s", exc)

    return False
