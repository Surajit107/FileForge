"""PDF source conversion engines (lossy / best-effort where noted)."""

from __future__ import annotations

import re
from pathlib import Path

from pypdf import PdfReader

from engines.exceptions import ConversionFailedError

_HEADING_RE = re.compile(r"^[A-Z0-9][A-Z0-9 \-_/:]{2,80}$")
_MULTI_SPACE = re.compile(r"[ \t]{2,}")


def _extract_pages(source_path: Path) -> list[str]:
    reader = PdfReader(str(source_path))
    pages: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(text.replace("\r\n", "\n").replace("\r", "\n"))
    return pages


def pdf_to_plain_text(source_path: Path) -> str:
    pages = _extract_pages(source_path)
    chunks = [page.strip() for page in pages if page.strip()]
    return ("\n\n".join(chunks).strip() + "\n") if chunks else "\n"


def pdf_to_markdown(source_path: Path) -> str:
    """Heuristic structure mapping — not a perfect reverse of md→pdf."""
    pages = _extract_pages(source_path)
    lines_out: list[str] = []
    for page_index, page in enumerate(pages):
        if page_index:
            lines_out.append("\n---\n")
        for raw_line in page.splitlines():
            line = _MULTI_SPACE.sub(" ", raw_line).strip()
            if not line:
                if lines_out and lines_out[-1] != "":
                    lines_out.append("")
                continue
            if _HEADING_RE.match(line) and len(line.split()) <= 12:
                lines_out.append(f"## {line.title()}")
            else:
                lines_out.append(line)
    body = "\n".join(lines_out).strip()
    return (body + "\n") if body else "# Extracted PDF\n\n_(No extractable text)_\n"


class PdfToTxtEngine:
    source_format = "pdf"
    target_format = "txt"

    def convert(self, source_path: Path, destination_path: Path) -> Path:
        try:
            destination_path.write_text(pdf_to_plain_text(source_path), encoding="utf-8")
            return destination_path
        except Exception as exc:  # noqa: BLE001
            raise ConversionFailedError(f"PDF→TXT failed: {exc}") from exc


class PdfToMarkdownEngine:
    source_format = "pdf"
    target_format = "md"

    def convert(self, source_path: Path, destination_path: Path) -> Path:
        try:
            destination_path.write_text(pdf_to_markdown(source_path), encoding="utf-8")
            return destination_path
        except Exception as exc:  # noqa: BLE001
            raise ConversionFailedError(f"PDF→MD failed: {exc}") from exc


class PdfToDocxEngine:
    source_format = "pdf"
    target_format = "docx"

    def convert(self, source_path: Path, destination_path: Path) -> Path:
        try:
            from pdf2docx import Converter

            converter = Converter(str(source_path))
            try:
                converter.convert(str(destination_path))
            finally:
                converter.close()
            if not destination_path.exists() or destination_path.stat().st_size == 0:
                raise ConversionFailedError("pdf2docx produced an empty file.")
            return destination_path
        except ConversionFailedError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise ConversionFailedError(f"PDF→DOCX failed: {exc}") from exc
