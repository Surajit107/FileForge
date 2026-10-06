"""Slide conversion engines (LibreOffice Impress)."""

from __future__ import annotations

from pathlib import Path

from engines.document.libreoffice import convert_with_libreoffice
from engines.exceptions import ConversionFailedError


class PptxToPdfEngine:
    source_format = "pptx"
    target_format = "pdf"

    def convert(self, source_path: Path, destination_path: Path) -> Path:
        try:
            return convert_with_libreoffice(source_path, destination_path)
        except ConversionFailedError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise ConversionFailedError(f"PPTX→PDF failed: {exc}") from exc
