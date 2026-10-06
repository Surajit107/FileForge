"""Lightweight content sniffing without libmagic (Windows-friendly)."""

from __future__ import annotations

import tarfile
import zipfile
from pathlib import Path

# Magic signatures we accept for registered document / image / office / media sources.
_PDF_MAGIC = b"%PDF"
_ZIP_MAGIC = b"PK\x03\x04"  # DOCX / XLSX / PPTX / ZIP
_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
_JPEG_MAGIC = b"\xff\xd8\xff"
_GIF_MAGIC_PREFIXES = (b"GIF87a", b"GIF89a")
_BMP_MAGIC = b"BM"
_WEBP_RIFF = b"RIFF"
_WEBP_WEBP = b"WEBP"
_WAV_WAVE = b"WAVE"
_GZIP_MAGIC = b"\x1f\x8b"
_SEVEN_ZIP_MAGIC = b"7z\xbc\xaf'\x1c"
_FLAC_MAGIC = b"fLaC"
_OGG_MAGIC = b"OggS"
_ID3_MAGIC = b"ID3"
_EBML_MAGIC = b"\x1a\x45\xdf\xa3"


def sniff_format(path: Path, declared_filename: str | None = None) -> str | None:
    """Return normalized format from file bytes, or None if unrecognized.

    Extension is used as a disambiguation hint for plain-text Markdown / CSV
    and for EBML containers (webm vs mkv).
    """
    data = path.read_bytes()[:8192]
    if not data:
        return None

    suffix = Path(declared_filename or path.name).suffix.lower().lstrip(".")
    name = Path(declared_filename or path.name).name.lower()

    if data.startswith(_PDF_MAGIC):
        return "pdf"

    if data.startswith(_SEVEN_ZIP_MAGIC):
        return "7z"

    if data.startswith(_GZIP_MAGIC):
        if _is_gzipped_tar(path):
            return "tgz"
        return None

    if data.startswith(_ZIP_MAGIC):
        office = _sniff_ooxml(path)
        if office:
            return office
        return "zip"

    if _looks_like_tar(data, path):
        return "tar"

    image_format = _sniff_image(data, path)
    if image_format:
        return image_format

    audio_format = _sniff_audio(data, suffix)
    if audio_format:
        return audio_format

    video_format = _sniff_video(data, path, suffix=suffix, name=name)
    if video_format:
        return video_format

    if _looks_like_text(data):
        # Text formats require a declared extension — never invent md/csv
        # from arbitrary UTF-8 bytes (extension spoofing / polyglot risk).
        if suffix == "csv":
            return "csv"
        if suffix in {"md", "markdown", "mdown", "mkd"}:
            return "md"

    return None


def _is_gzipped_tar(path: Path) -> bool:
    try:
        with tarfile.open(path, "r:gz") as archive:
            # Force header read; empty archive is still a valid tgz container.
            archive.getmembers()
        return True
    except (OSError, tarfile.TarError):
        return False


def _looks_like_tar(data: bytes, path: Path) -> bool:
    # POSIX ustar magic at offset 257.
    if len(data) >= 262 and data[257:262] == b"ustar":
        return True
    try:
        with tarfile.open(path, "r:") as archive:
            archive.getmembers()
        return True
    except (OSError, tarfile.TarError):
        return False


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


def _sniff_audio(data: bytes, suffix: str) -> str | None:
    if data.startswith(_FLAC_MAGIC):
        return "flac"
    if data.startswith(_OGG_MAGIC):
        # Ogg may wrap Vorbis, Opus, or Theora — treat as audio ogg for our matrix.
        return "ogg"
    if (
        len(data) >= 12
        and data.startswith(_WEBP_RIFF)
        and data[8:12] == _WAV_WAVE
    ):
        return "wav"
    if data.startswith(_ID3_MAGIC) or _looks_like_mp3_frame(data):
        return "mp3"
    if suffix in {"mp3", "wav", "flac", "ogg"} and _looks_like_mp3_frame(data):
        return "mp3"
    return None


def _looks_like_mp3_frame(data: bytes) -> bool:
    # MPEG audio frame sync: 11 set bits.
    if len(data) < 2:
        return False
    return data[0] == 0xFF and (data[1] & 0xE0) == 0xE0


def _sniff_video(
    data: bytes,
    path: Path,
    *,
    suffix: str,
    name: str,
) -> str | None:
    if _looks_like_mp4(data):
        return "mp4"

    if data.startswith(_EBML_MAGIC):
        # webm and mkv share EBML; prefer declared extension, else probe DocType.
        if suffix == "webm" or name.endswith(".webm"):
            return "webm"
        if suffix == "mkv" or name.endswith(".mkv"):
            return "mkv"
        doctype = _ebml_doctype(data)
        if doctype == "webm":
            return "webm"
        if doctype in {"matroska", "mkv"}:
            return "mkv"
        return "mkv"

    return None


def _looks_like_mp4(data: bytes) -> bool:
    # ISO BMFF: size(4) + 'ftyp'(4) at start, or free/mdat before ftyp in rare cases.
    if len(data) >= 8 and data[4:8] == b"ftyp":
        return True
    return b"ftyp" in data[:64]


def _ebml_doctype(data: bytes) -> str | None:
    marker = b"\x42\x82"  # EBML DocType element id (simplified search)
    index = data.find(marker)
    if index < 0 or index + 3 >= len(data):
        return None
    # VINT size is usually one byte for short DocType strings.
    size = data[index + 2]
    if size & 0x80:
        length = size & 0x7F
        start = index + 3
        end = start + length
        if end <= len(data):
            try:
                return data[start:end].decode("ascii").lower()
            except UnicodeDecodeError:
                return None
    return None


def _sniff_ooxml(path: Path) -> str | None:
    """Disambiguate DOCX / XLSX / PPTX ZIP packages by internal member prefixes."""
    try:
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
    except (OSError, zipfile.BadZipFile):
        return None

    if any(name.startswith("word/") for name in names):
        return "docx"
    if any(name.startswith("xl/") for name in names):
        return "xlsx"
    if any(name.startswith("ppt/") for name in names):
        return "pptx"
    return None


def _looks_like_text(data: bytes) -> bool:
    if b"\x00" in data:
        return False
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True
