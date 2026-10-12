"""In-browser preview support for readable conversion outputs."""

from __future__ import annotations

PREVIEWABLE_TARGETS: frozenset[str] = frozenset(
    {
        "pdf",
        "png",
        "jpg",
        "webp",
        "html",
        "txt",
        "md",
        "csv",
    }
)

_CONTENT_TYPES: dict[str, str] = {
    "pdf": "application/pdf",
    "png": "image/png",
    "jpg": "image/jpeg",
    "webp": "image/webp",
    "html": "text/html; charset=utf-8",
    "txt": "text/plain; charset=utf-8",
    "md": "text/plain; charset=utf-8",
    "csv": "text/csv; charset=utf-8",
}

_IMAGE_TARGETS: frozenset[str] = frozenset({"png", "jpg", "webp"})
_TEXT_TARGETS: frozenset[str] = frozenset({"txt", "md", "csv"})


def is_previewable(target_format: str) -> bool:
    return target_format.lower().lstrip(".") in PREVIEWABLE_TARGETS


def preview_content_type(target_format: str) -> str:
    normalized = target_format.lower().lstrip(".")
    try:
        return _CONTENT_TYPES[normalized]
    except KeyError as exc:
        raise ValueError(f"No preview content type for {target_format}") from exc


def preview_mode(target_format: str) -> str:
    """How the frontend should render: pdf | html | image | text."""
    normalized = target_format.lower().lstrip(".")
    if normalized in _IMAGE_TARGETS:
        return "image"
    if normalized in _TEXT_TARGETS:
        return "text"
    if normalized == "html":
        return "html"
    if normalized == "pdf":
        return "pdf"
    raise ValueError(f"No preview mode for {target_format}")
