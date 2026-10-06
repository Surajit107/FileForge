"""Lightweight content sniffing without libmagic (Windows-friendly)."""

from __future__ import annotations

from pathlib import Path

# Magic signatures we accept for registered document / image sources.
_PDF_MAGIC = b"%PDF"
_ZIP_MAGIC = b"PK\x03\x04"  # DOCX is a ZIP package
_DOCX_REQUIRED_MEMBER = b"word/"
_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
_JPEG_MAGIC = b"\xff\xd8\xff"
_GIF_MAGIC_PREFIXES = (b"GIF87a", b"GIF89a")
_BMP_MAGIC = b"BM"
_WEBP_RIFF = b"RIFF"
_WEBP_WEBP = b"WEBP"


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

    image_format = _sniff_image(data, path)
    if image_format:
        return image_format

    if _looks_like_text(data):
        suffix = Path(declared_filename or path.name).suffix.lower().lstrip(".")
        if suffix in {"md", "markdown", "mdown", "mkd", "txt"}:
            return "md"
        # Allow extensionless / odd Markdown uploads that are clearly text.
        if b"#" in data or b"\n" in data:
            return "md"

    return None


def _sniff_image(data: bytes, path: Path) -> str | None:
    if data.startswith(_PNG_MAGIC):
        return "png"
    if data.startswith(_JPEG_MAGIC):
        return "jpg"
    if data.startswith(_GIF_MAGIC_PREFIXES):
        return "gif"
    if data.startswith(_BMP_MAGIC):
        return "bmp"
    if (
        len(data) >= 12
        and data.startswith(_WEBP_RIFF)
        and data[8:12] == _WEBP_WEBP
    ):
        return "webp"

    # Fallback: ask Pillow when magic is ambiguous but the file is a real image.
    try:
        from PIL import Image, UnidentifiedImageError

        with Image.open(path) as image:
            fmt = (image.format or "").upper()
    except (OSError, UnidentifiedImageError, ValueError):
        return None

    mapping = {
        "PNG": "png",
        "JPEG": "jpg",
        "JPG": "jpg",
        "WEBP": "webp",
        "GIF": "gif",
        "BMP": "bmp",
    }
    return mapping.get(fmt)


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
