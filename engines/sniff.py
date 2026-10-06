"""Lightweight content sniffing without libmagic (Windows-friendly)."""

from __future__ import annotations

from pathlib import Path


# Magic signatures we accept for registered document sources.
_PDF_MAGIC = b"%PDF"
_ZIP_MAGIC = b"PK\x03\x04"  # DOCX is a ZIP package
_DOCX_REQUIRED_MEMBER = b"word/"


def sniff_format(path: Path, declared_filename: str | None = None) -> str | None:
    """Return normalized format from file bytes, or None if unrecognized.

    Extension is used only as a disambiguation hint for plain-text Markdown.
    """
    data = path.read_bytes()[:8192]
    if not data:
        return None

    if data.startswith(_PDF_MAGIC):
        return "pdf"

    if data.startswith(_ZIP_MAGIC) and _looks_like_docx(path, data):
        return "docx"

    if _looks_like_text(data):
        suffix = Path(declared_filename or path.name).suffix.lower().lstrip(".")
        if suffix in {"md", "markdown", "mdown", "mkd", "txt"}:
            return "md"
        # Allow extensionless / odd Markdown uploads that are clearly text.
        if b"#" in data or b"\n" in data:
            return "md"

    return None


def _looks_like_docx(path: Path, head: bytes) -> bool:
    # Fast path: local part names often appear early in the ZIP central/local headers.
    if _DOCX_REQUIRED_MEMBER in head or b"[Content_Types].xml" in head:
        return True
    import zipfile

    try:
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
        return any(name.startswith("word/") for name in names)
    except (OSError, zipfile.BadZipFile):
        return False


def _looks_like_text(data: bytes) -> bool:
    if b"\x00" in data:
        return False
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True
