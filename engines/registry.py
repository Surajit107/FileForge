"""Central conversion pair registry.

Views/services never branch on format strings — they ask the registry.
"""

from __future__ import annotations

from pathlib import Path

from engines.base import ConversionEngine, ConversionPair
from engines.document import (
    DocxToMarkdownEngine,
    DocxToPdfEngine,
    DocxToTxtEngine,
    PdfToDocxEngine,
    PdfToMarkdownEngine,
    PdfToTxtEngine,
)
from engines.exceptions import UnsupportedConversionError
from engines.markdown import (
    MarkdownToDocxEngine,
    MarkdownToHtmlEngine,
    MarkdownToPdfEngine,
    MarkdownToTxtEngine,
)

_ENGINES: dict[tuple[str, str], ConversionEngine] = {}
_PAIRS: dict[tuple[str, str], ConversionPair] = {}

ALLOWED_SOURCE_EXTENSIONS: frozenset[str] = frozenset(
    {
        "md",
        "markdown",
        "mdown",
        "mkd",
        "docx",
        "pdf",
    }
)


def _register(pair: ConversionPair, engine: ConversionEngine) -> None:
    key = (pair.source, pair.target)
    _PAIRS[key] = pair
    _ENGINES[key] = engine


def _bootstrap() -> None:
    if _PAIRS:
        return

    _register(
        ConversionPair(source="md", target="pdf", label="PDF", category="documents"),
        MarkdownToPdfEngine(),
    )
    _register(
        ConversionPair(source="md", target="docx", label="DOCX", category="documents"),
        MarkdownToDocxEngine(),
    )
    _register(
        ConversionPair(source="md", target="html", label="HTML", category="documents"),
        MarkdownToHtmlEngine(),
    )
    _register(
        ConversionPair(source="md", target="txt", label="TXT", category="documents"),
        MarkdownToTxtEngine(),
    )
    _register(
        ConversionPair(
            source="docx",
            target="pdf",
            label="PDF",
            category="documents",
            best_effort=True,
        ),
        DocxToPdfEngine(),
    )
    _register(
        ConversionPair(source="docx", target="txt", label="TXT", category="documents"),
        DocxToTxtEngine(),
    )
    _register(
        ConversionPair(
            source="docx",
            target="md",
            label="Markdown",
            category="documents",
            best_effort=True,
        ),
        DocxToMarkdownEngine(),
    )
    _register(
        ConversionPair(source="pdf", target="txt", label="TXT", category="documents"),
        PdfToTxtEngine(),
    )
    _register(
        ConversionPair(
            source="pdf",
            target="md",
            label="Markdown",
            category="documents",
            best_effort=True,
        ),
        PdfToMarkdownEngine(),
    )
    _register(
        ConversionPair(
            source="pdf",
            target="docx",
            label="DOCX",
            category="documents",
            best_effort=True,
        ),
        PdfToDocxEngine(),
    )


def list_pairs() -> list[ConversionPair]:
    _bootstrap()
    return list(_PAIRS.values())


def list_sources() -> list[str]:
    _bootstrap()
    return sorted({pair.source for pair in _PAIRS.values()})


def targets_for(source: str) -> list[ConversionPair]:
    _bootstrap()
    normalized = normalize_format(source)
    return [pair for pair in _PAIRS.values() if pair.source == normalized]


def get_pair(source: str, target: str) -> ConversionPair:
    _bootstrap()
    key = (normalize_format(source), normalize_format(target))
    try:
        return _PAIRS[key]
    except KeyError as exc:
        raise UnsupportedConversionError(
            f"Unsupported conversion: {key[0]} → {key[1]}"
        ) from exc


def get_engine(source: str, target: str) -> ConversionEngine:
    _bootstrap()
    key = (normalize_format(source), normalize_format(target))
    try:
        return _ENGINES[key]
    except KeyError as exc:
        raise UnsupportedConversionError(
            f"No engine registered for {key[0]} → {key[1]}"
        ) from exc


def convert_file(source_path: Path, source: str, target: str, destination_path: Path) -> Path:
    """Run the registered engine for the given pair."""
    engine = get_engine(source, target)
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    return engine.convert(source_path, destination_path)


def normalize_format(value: str) -> str:
    cleaned = value.lower().lstrip(".")
    aliases = {
        "markdown": "md",
        "mdown": "md",
        "mkd": "md",
        "text": "txt",
        "jpeg": "jpg",
        "htm": "html",
    }
    return aliases.get(cleaned, cleaned)


def detect_format_from_filename(filename: str) -> str | None:
    suffix = Path(filename).suffix.lower().lstrip(".")
    if not suffix:
        return None
    normalized = normalize_format(suffix)
    if normalized in {"md", "docx", "pdf"}:
        return normalized
    return None
