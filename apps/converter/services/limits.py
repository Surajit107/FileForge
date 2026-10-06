"""Content-size guards beyond byte caps (pages / pixels)."""

from __future__ import annotations

from pathlib import Path

from django.conf import settings

from apps.converter.exceptions import InvalidUploadError
from engines.registry import IMAGE_SOURCES


def enforce_content_limits(path: Path, source_format: str) -> None:
    """Reject uploads that exceed configured page or pixel budgets."""
    if source_format == "pdf":
        _enforce_pdf_pages(path)
    elif source_format in IMAGE_SOURCES:
        _enforce_image_pixels(path)


def _enforce_pdf_pages(path: Path) -> None:
    max_pages = int(getattr(settings, "CONVERSION_MAX_PDF_PAGES", 0) or 0)
    if max_pages <= 0:
        return
    try:
        from pypdf import PdfReader

        page_count = len(PdfReader(str(path)).pages)
    except Exception as exc:  # noqa: BLE001 - treat unreadable PDF as invalid upload
        raise InvalidUploadError(f"Unable to read PDF: {exc}") from exc

    if page_count > max_pages:
        raise InvalidUploadError(
            f"PDF has {page_count} pages; maximum allowed is {max_pages}."
        )


def _enforce_image_pixels(path: Path) -> None:
    max_pixels = int(getattr(settings, "CONVERSION_MAX_IMAGE_PIXELS", 0) or 0)
    if max_pixels <= 0:
        return

    try:
        from PIL import Image, ImageFile, UnidentifiedImageError

        # Decompression-bomb backstop used by Pillow itself.
        Image.MAX_IMAGE_PIXELS = max_pixels
        ImageFile.LOAD_TRUNCATED_IMAGES = False

        with Image.open(path) as image:
            width, height = image.size
            # Force header decode without fully loading pixels when possible.
            image.load()
    except UnidentifiedImageError as exc:
        raise InvalidUploadError("Unable to read image.") from exc
    except Image.DecompressionBombError as exc:
        raise InvalidUploadError(
            f"Image exceeds the {max_pixels:,} pixel limit."
        ) from exc
    except (OSError, ValueError) as exc:
        raise InvalidUploadError(f"Unable to read image: {exc}") from exc

    pixels = width * height
    if pixels > max_pixels:
        raise InvalidUploadError(
            f"Image is {width}×{height} ({pixels:,} pixels); "
            f"maximum allowed is {max_pixels:,}."
        )
