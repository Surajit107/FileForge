"""Central conversion pair registry.

Views/services never branch on format strings — they ask the registry.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from engines.archive import build_archive_engines
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
from engines.image import build_image_engines
from engines.markdown import (
    MarkdownToDocxEngine,
    MarkdownToHtmlEngine,
    MarkdownToPdfEngine,
    MarkdownToTxtEngine,
)
from engines.media import build_media_engines
from engines.slides import PptxToPdfEngine
from engines.spreadsheet import build_spreadsheet_engines

_ENGINES: dict[tuple[str, str], ConversionEngine] = {}
_PAIRS: dict[tuple[str, str], ConversionPair] = {}

DOCUMENT_SOURCES: frozenset[str] = frozenset({"md", "docx", "pdf"})
IMAGE_SOURCES: frozenset[str] = frozenset({"png", "jpg", "webp", "gif", "bmp"})
SPREADSHEET_SOURCES: frozenset[str] = frozenset({"csv", "xlsx"})
SLIDE_SOURCES: frozenset[str] = frozenset({"pptx"})
ARCHIVE_SOURCES: frozenset[str] = frozenset({"zip", "tar", "tgz", "7z"})
AUDIO_SOURCES: frozenset[str] = frozenset({"mp3", "wav", "flac", "ogg"})
VIDEO_SOURCES: frozenset[str] = frozenset({"mp4", "webm", "mkv"})
MEDIA_SOURCES: frozenset[str] = AUDIO_SOURCES | VIDEO_SOURCES
REGISTERED_SOURCES: frozenset[str] = (
    DOCUMENT_SOURCES
    | IMAGE_SOURCES
    | SPREADSHEET_SOURCES
    | SLIDE_SOURCES
    | ARCHIVE_SOURCES
    | MEDIA_SOURCES
)

ALLOWED_SOURCE_EXTENSIONS: frozenset[str] = frozenset(
    {
        "md",
        "markdown",
        "mdown",
        "mkd",
        "docx",
        "pdf",
        "png",
        "jpg",
        "jpeg",
        "webp",
        "gif",
        "bmp",
        "csv",
        "xlsx",
        "pptx",
        "zip",
        "tar",
        "tgz",
        "gz",
        "7z",
        "mp3",
        "wav",
        "flac",
        "ogg",
        "mp4",
        "webm",
        "mkv",
    }
)

_ACCEPT_EXTENSIONS: tuple[str, ...] = (
    ".md",
    ".markdown",
    ".docx",
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
    ".bmp",
    ".csv",
    ".xlsx",
    ".pptx",
    ".zip",
    ".tar",
    ".tgz",
    ".tar.gz",
    ".7z",
    ".mp3",
    ".wav",
    ".flac",
    ".ogg",
    ".mp4",
    ".webm",
    ".mkv",
)


def accept_attribute() -> str:
    """Comma-separated accept list for the upload input."""
    return ",".join(_ACCEPT_EXTENSIONS)


def supported_upload_message() -> str:
    return (
        "Unsupported file type. Currently accepts Markdown (.md), DOCX, PDF, "
        "images (PNG, JPG, WEBP, GIF, BMP), CSV, XLSX, PPTX, archives "
        "(ZIP, TAR, TAR.GZ, 7Z), audio (MP3, WAV, FLAC, OGG), or video "
        "(MP4, WEBM, MKV)."
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

    for source, target, label, engine in build_image_engines():
        _register(
            ConversionPair(
                source=source,
                target=target,
                label=label,
                category="images",
            ),
            engine,
        )

    for source, target, label, engine in build_spreadsheet_engines():
        _register(
            ConversionPair(
                source=source,
                target=target,
                label=label,
                category="spreadsheets",
                best_effort=target == "pdf",
            ),
            engine,
        )

    _register(
        ConversionPair(
            source="pptx",
            target="pdf",
            label="PDF",
            category="slides",
            best_effort=True,
        ),
        PptxToPdfEngine(),
    )

    for source, target, label, engine in build_archive_engines():
        _register(
            ConversionPair(
                source=source,
                target=target,
                label=label,
                category="archives",
                best_effort=source == "7z" or target == "7z",
                max_bytes=50 * 1024 * 1024,
                timeout_sec=180,
            ),
            engine,
        )

    for source, target, label, engine, max_bytes, timeout_sec in build_media_engines():
        category = "audio" if source in AUDIO_SOURCES else "video"
        _register(
            ConversionPair(
                source=source,
                target=target,
                label=label,
                category=category,
                best_effort=True,
                max_bytes=max_bytes,
                timeout_sec=timeout_sec,
            ),
            engine,
        )


def list_pairs() -> list[ConversionPair]:
    _bootstrap()
    return list(_PAIRS.values())


def list_sources() -> list[str]:
    _bootstrap()
    return sorted({pair.source for pair in _PAIRS.values()})


_CATEGORY_ORDER: dict[str, int] = {
    "documents": 0,
    "images": 1,
    "spreadsheets": 2,
    "slides": 3,
    "archives": 4,
    "audio": 5,
    "video": 6,
}


def list_unique_targets() -> list[ConversionPair]:
    """Distinct target formats for the empty-state Convert-to catalog.

    Source-agnostic: ``best_effort`` is always False because that flag depends
    on the uploaded source. Used before a file is selected; after upload
    ``targets_for`` filters to the real pairs.
    """
    _bootstrap()
    by_target: dict[str, ConversionPair] = {}
    for pair in _PAIRS.values():
        existing = by_target.get(pair.target)
        if existing is None:
            by_target[pair.target] = ConversionPair(
                source="*",
                target=pair.target,
                label=pair.label,
                category=pair.category,
                best_effort=False,
            )
            continue
        # Prefer a more specific / earlier category if labels collide.
        if _CATEGORY_ORDER.get(pair.category, 99) < _CATEGORY_ORDER.get(
            existing.category, 99
        ):
            by_target[pair.target] = ConversionPair(
                source="*",
                target=pair.target,
                label=pair.label,
                category=pair.category,
                best_effort=False,
            )

    return sorted(
        by_target.values(),
        key=lambda p: (_CATEGORY_ORDER.get(p.category, 99), p.label.lower(), p.target),
    )


def targets_for(source: str) -> list[ConversionPair]:
    _bootstrap()
    normalized = normalize_format(source)
    return [pair for pair in _PAIRS.values() if pair.source == normalized]


# Archive formats offered as "pack these uploads" when 2+ files are selected.
PACKABLE_TARGETS: frozenset[str] = frozenset({"zip", "tar", "tgz", "7z"})

_PACK_TARGET_META: tuple[tuple[str, str, bool], ...] = (
    ("zip", "ZIP", False),
    ("tar", "TAR", False),
    ("tgz", "TAR.GZ", False),
    ("7z", "7Z", True),
)


def pack_target_pairs() -> list[ConversionPair]:
    """Synthetic pairs for multi-file archive packing (not per-file conversion)."""
    return [
        ConversionPair(
            source="*",
            target=target,
            label=label,
            category="archives",
            best_effort=best_effort,
        )
        for target, label, best_effort in _PACK_TARGET_META
    ]


def has_pair(source: str, target: str) -> bool:
    _bootstrap()
    return (normalize_format(source), normalize_format(target)) in _PAIRS


def is_pack_operation(sources: Sequence[str], target: str) -> bool:
    """Multi-file archive pack when the target is not a valid per-file conversion."""
    normalized_sources = [normalize_format(source) for source in sources if source]
    if len(normalized_sources) < 2:
        return False
    normalized_target = normalize_format(target)
    if normalized_target not in PACKABLE_TARGETS:
        return False
    return not all(has_pair(source, normalized_target) for source in normalized_sources)


def targets_for_selection(sources: Sequence[str]) -> list[ConversionPair]:
    """Resolve Convert-to options for zero, one, or many detected sources.

    - No sources → full catalog
    - One source → that source's pairs
    - Many sources → intersection of pairs, plus pack targets (ZIP/TAR/…)
    """
    normalized = [normalize_format(source) for source in sources if source]
    if not normalized:
        return list_unique_targets()
    if len(normalized) == 1:
        return targets_for(normalized[0])

    per_source = [
        {pair.target: pair for pair in targets_for(source)} for source in normalized
    ]
    common = set(per_source[0])
    for mapping in per_source[1:]:
        common &= set(mapping)

    by_target: dict[str, ConversionPair] = {}
    for target in common:
        matched = [mapping[target] for mapping in per_source]
        base = matched[0]
        by_target[target] = ConversionPair(
            source="*",
            target=target,
            label=base.label,
            category=base.category,
            best_effort=any(pair.best_effort for pair in matched),
        )

    for pack in pack_target_pairs():
        by_target.setdefault(pack.target, pack)

    return sorted(
        by_target.values(),
        key=lambda pair: (
            _CATEGORY_ORDER.get(pair.category, 99),
            pair.label.lower(),
            pair.target,
        ),
    )


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


def convert_file(
    source_path: Path, source: str, target: str, destination_path: Path
) -> Path:
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
        "tar.gz": "tgz",
        "gz": "tgz",
    }
    return aliases.get(cleaned, cleaned)


def detect_format_from_filename(filename: str) -> str | None:
    name = Path(filename).name.lower()
    if name.endswith((".tar.gz", ".tgz")):
        return "tgz"

    suffix = Path(filename).suffix.lower().lstrip(".")
    if not suffix:
        return None
    normalized = normalize_format(suffix)
    if normalized in REGISTERED_SOURCES:
        return normalized
    return None
