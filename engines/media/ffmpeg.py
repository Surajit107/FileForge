"""ffmpeg CLI helper for audio / video conversions."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from engines.exceptions import ConversionFailedError

_WINDOWS_CANDIDATES = (
    Path(r"C:\ffmpeg\bin\ffmpeg.exe"),
    Path(r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"),
)


def find_ffmpeg() -> str | None:
    """Return an ffmpeg executable path, or None if missing."""
    for candidate in ("ffmpeg", "ffmpeg.exe"):
        resolved = shutil.which(candidate)
        if resolved:
            return resolved

    extra = os.environ.get("FFMPEG_PATH", "").strip()
    if extra:
        path = Path(extra)
        if path.is_file():
            return str(path)

    if os.name == "nt":
        for path in _WINDOWS_CANDIDATES:
            if path.is_file():
                return str(path)
    return None


# Per-target encode args after `-i input`.
_TARGET_ARGS: dict[str, list[str]] = {
    "mp3": ["-vn", "-acodec", "libmp3lame", "-q:a", "2"],
    "wav": ["-vn", "-acodec", "pcm_s16le"],
    "flac": ["-vn", "-acodec", "flac"],
    "ogg": ["-vn", "-acodec", "libvorbis", "-q:a", "5"],
    "mp4": [
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "23",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-movflags",
        "+faststart",
    ],
    "webm": [
        "-c:v",
        "libvpx-vp9",
        "-b:v",
        "0",
        "-crf",
        "32",
        "-c:a",
        "libopus",
        "-b:a",
        "128k",
    ],
    "mkv": [
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "23",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
    ],
}


def convert_with_ffmpeg(
    source_path: Path,
    destination_path: Path,
    target: str,
    *,
    timeout_sec: int = 600,
) -> Path:
    binary = find_ffmpeg()
    if binary is None:
        raise ConversionFailedError(
            "ffmpeg is required for this conversion but was not found. "
            "Install ffmpeg and ensure it is on PATH, or set FFMPEG_PATH "
            "to the ffmpeg binary."
        )

    target = target.lower()
    args = _TARGET_ARGS.get(target)
    if args is None:
        raise ConversionFailedError(f"Unsupported media target: {target}")

    destination_path.parent.mkdir(parents=True, exist_ok=True)
    if destination_path.exists():
        destination_path.unlink()

    command = [
        binary,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(source_path.resolve()),
        *args,
        str(destination_path.resolve()),
    ]

    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
    except subprocess.TimeoutExpired as exc:
        raise ConversionFailedError("ffmpeg conversion timed out.") from exc
    except OSError as exc:
        raise ConversionFailedError(f"ffmpeg failed to start: {exc}") from exc

    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise ConversionFailedError(
            f"ffmpeg conversion failed (exit {completed.returncode})"
            + (f": {detail}" if detail else ".")
        )

    if not destination_path.exists() or destination_path.stat().st_size == 0:
        raise ConversionFailedError("ffmpeg produced an empty output file.")
    return destination_path
