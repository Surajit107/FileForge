"""Optional 7-Zip CLI helper for .7z archive conversions."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from engines.exceptions import ConversionFailedError

_WINDOWS_CANDIDATES = (
    Path(r"C:\Program Files\7-Zip\7z.exe"),
    Path(r"C:\Program Files (x86)\7-Zip\7z.exe"),
)


def find_7z() -> str | None:
    """Return a 7z/7za executable path, or None if missing."""
    for candidate in ("7z", "7za", "7z.exe", "7za.exe"):
        resolved = shutil.which(candidate)
        if resolved:
            return resolved

    extra = os.environ.get("SEVEN_ZIP_PATH", "").strip()
    if extra:
        path = Path(extra)
        if path.is_file():
            return str(path)

    if os.name == "nt":
        for path in _WINDOWS_CANDIDATES:
            if path.is_file():
                return str(path)
    return None


def extract_7z(archive_path: Path, destination_dir: Path) -> None:
    binary = find_7z()
    if binary is None:
        raise ConversionFailedError(
            "7-Zip is required for this conversion but was not found. "
            "Install 7-Zip / p7zip and ensure `7z` is on PATH, or set "
            "SEVEN_ZIP_PATH to the 7z binary."
        )

    destination_dir.mkdir(parents=True, exist_ok=True)
    try:
        completed = subprocess.run(
            [
                binary,
                "x",
                str(archive_path.resolve()),
                f"-o{destination_dir.resolve()}",
                "-y",
                "-bso0",
                "-bsp0",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=180,
        )
    except subprocess.TimeoutExpired as exc:
        raise ConversionFailedError("7-Zip extraction timed out.") from exc
    except OSError as exc:
        raise ConversionFailedError(f"7-Zip failed to start: {exc}") from exc

    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise ConversionFailedError(
            f"7-Zip extraction failed (exit {completed.returncode})"
            + (f": {detail}" if detail else ".")
        )


def create_7z(source_dir: Path, archive_path: Path) -> Path:
    binary = find_7z()
    if binary is None:
        raise ConversionFailedError(
            "7-Zip is required for this conversion but was not found. "
            "Install 7-Zip / p7zip and ensure `7z` is on PATH, or set "
            "SEVEN_ZIP_PATH to the 7z binary."
        )

    archive_path.parent.mkdir(parents=True, exist_ok=True)
    if archive_path.exists():
        archive_path.unlink()

    # Archive contents of source_dir (not the directory itself).
    try:
        completed = subprocess.run(
            [
                binary,
                "a",
                "-t7z",
                str(archive_path.resolve()),
                ".",
                "-y",
                "-bso0",
                "-bsp0",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=180,
            cwd=str(source_dir.resolve()),
        )
    except subprocess.TimeoutExpired as exc:
        raise ConversionFailedError("7-Zip compression timed out.") from exc
    except OSError as exc:
        raise ConversionFailedError(f"7-Zip failed to start: {exc}") from exc

    if completed.returncode != 0 or not archive_path.exists():
        detail = (completed.stderr or completed.stdout or "").strip()
        raise ConversionFailedError(
            f"7-Zip compression failed (exit {completed.returncode})"
            + (f": {detail}" if detail else ".")
        )
    return archive_path
