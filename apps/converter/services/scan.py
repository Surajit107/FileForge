"""Optional malware scanning hook for uploaded files.

Disabled by default. When ``CLAMAV_ENABLED`` is true, shells out to the
configured scanner binary (typically ``clamdscan`` / ``clamscan``).
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

from django.conf import settings

from apps.converter.exceptions import InvalidUploadError

logger = logging.getLogger(__name__)


def scan_upload(path: Path) -> None:
    """Raise ``InvalidUploadError`` if the file is rejected by the scanner."""
    if not getattr(settings, "CLAMAV_ENABLED", False):
        return

    binary = getattr(settings, "CLAMAV_BINARY", "clamscan")
    timeout = int(getattr(settings, "CLAMAV_TIMEOUT_SEC", 30))
    try:
        completed = subprocess.run(
            [binary, "--no-summary", str(path)],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        logger.error("clamav_binary_missing binary=%s", binary)
        raise InvalidUploadError(
            "Malware scanning is enabled but the scanner binary was not found."
        ) from exc
    except subprocess.TimeoutExpired as exc:
        logger.error("clamav_timeout path=%s", path)
        raise InvalidUploadError("Malware scan timed out.") from exc

    # clamscan: 0 clean, 1 infected, 2 error
    if completed.returncode == 0:
        return
    if completed.returncode == 1:
        logger.warning("clamav_infected path=%s", path)
        raise InvalidUploadError("Upload rejected by malware scan.")

    detail = (completed.stderr or completed.stdout or "unknown scanner error").strip()
    logger.error("clamav_error code=%s detail=%s", completed.returncode, detail)
    raise InvalidUploadError("Malware scan failed. Try again later.")
