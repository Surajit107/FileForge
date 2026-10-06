"""Filename sanitization and opaque on-disk storage names.

Client-supplied names are display metadata only. Disk keys are UUID-based so
path traversal, reserved Windows names, and Content-Disposition injection
cannot ride on the stored object path.
"""

from __future__ import annotations

import re
import unicodedata
import uuid
from pathlib import Path

_UNSAFE = re.compile(r"[^A-Za-z0-9._-]+")
_WINDOWS_RESERVED = frozenset(
    {
        "con",
        "prn",
        "aux",
        "nul",
        *(f"com{i}" for i in range(1, 10)),
        *(f"lpt{i}" for i in range(1, 10)),
    }
)
_MAX_DISPLAY_NAME = 200


def sanitize_display_name(filename: str, *, fallback: str = "upload.bin") -> str:
    """Return a safe basename for DB display / Content-Disposition."""
    raw = Path(filename or "").name
    normalized = unicodedata.normalize("NFKC", raw)
    chars: list[str] = []
    for ch in normalized:
        if ch in {"\r", "\n", "\t"} or not ch.isprintable():
            chars.append("_")
        else:
            chars.append(ch)
    printable = "".join(chars)
    cleaned = _UNSAFE.sub("_", printable).strip("._")
    if not cleaned:
        return fallback

    stem = Path(cleaned).stem[:160] or "upload"
    suffix = Path(cleaned).suffix.lower()[:20]
    if stem.lower() in _WINDOWS_RESERVED:
        stem = f"_{stem}"

    result = f"{stem}{suffix}"
    return result[:_MAX_DISPLAY_NAME] or fallback


def storage_object_name(original_name: str, *, format_hint: str | None = None) -> str:
    """Opaque on-disk filename: ``{uuid}{ext}``."""
    display = sanitize_display_name(original_name)
    suffix = Path(display).suffix.lower()
    if not suffix and format_hint:
        hint = format_hint.lower().lstrip(".")
        if hint == "tgz":
            suffix = ".tar.gz"
        elif hint:
            suffix = f".{hint}"
    return f"{uuid.uuid4().hex}{suffix}"
