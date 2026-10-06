"""Markdown conversion engines registered with the global registry."""

from __future__ import annotations

from pathlib import Path

from engines.exceptions import ConversionFailedError
from engines.markdown.pipeline import (
    build_docx,
    build_html,
    build_pdf,
    build_txt,
    parse_markdown,
)


class MarkdownToPdfEngine:
    source_format = "md"
    target_format = "pdf"

    def convert(self, source_path: Path, destination_path: Path) -> Path:
        try:
            document = parse_markdown(source_path.read_text(encoding="utf-8"))
            return build_pdf(document, destination_path)
        except Exception as exc:  # noqa: BLE001 - surface as engine failure
            raise ConversionFailedError(f"Markdown→PDF failed: {exc}") from exc


class MarkdownToDocxEngine:
    source_format = "md"
    target_format = "docx"

    def convert(self, source_path: Path, destination_path: Path) -> Path:
        try:
            document = parse_markdown(source_path.read_text(encoding="utf-8"))
            return build_docx(document, destination_path)
        except Exception as exc:  # noqa: BLE001 - surface as engine failure
            raise ConversionFailedError(f"Markdown→DOCX failed: {exc}") from exc


class MarkdownToHtmlEngine:
    source_format = "md"
    target_format = "html"

    def convert(self, source_path: Path, destination_path: Path) -> Path:
        try:
            document = parse_markdown(source_path.read_text(encoding="utf-8"))
            return build_html(document, destination_path)
        except Exception as exc:  # noqa: BLE001
            raise ConversionFailedError(f"Markdown→HTML failed: {exc}") from exc


class MarkdownToTxtEngine:
    source_format = "md"
    target_format = "txt"

    def convert(self, source_path: Path, destination_path: Path) -> Path:
        try:
            document = parse_markdown(source_path.read_text(encoding="utf-8"))
            return build_txt(document, destination_path)
        except Exception as exc:  # noqa: BLE001
            raise ConversionFailedError(f"Markdown→TXT failed: {exc}") from exc
