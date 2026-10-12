"""Diagonal watermark overlay for readable visual conversion outputs."""

from __future__ import annotations

import tempfile
from io import BytesIO
from pathlib import Path

from engines.exceptions import ConversionFailedError

WATERMARKABLE_TARGETS: frozenset[str] = frozenset(
    {"pdf", "png", "jpg", "webp", "html", "docx"}
)

_IMAGE_TARGETS: frozenset[str] = frozenset({"png", "jpg", "webp"})

# Helvetica-Bold / similar: average glyph width ≈ 0.55 × font size.
_CHAR_WIDTH_RATIO = 0.55


def _watermark_font_size(
    width: float,
    height: float,
    text: str,
    *,
    min_size: float = 36.0,
) -> float:
    """Pick a font size that scales with page area and text length.

    - Short labels grow with the page (capped at ~22% of the shorter edge).
    - Long labels shrink so the string still spans a useful portion of the page.
    """
    page_w = max(float(width), 1.0)
    page_h = max(float(height), 1.0)
    shorter = min(page_w, page_h)
    longer = max(page_w, page_h)
    diagonal = (page_w**2 + page_h**2) ** 0.5

    # Aim for the watermark string to cover ~55% of the page diagonal.
    target_text_width = diagonal * 0.55
    fitted = target_text_width / (max(len(text), 1) * _CHAR_WIDTH_RATIO)

    # Keep short words from swallowing the whole page.
    page_cap = shorter * 0.24
    # Floor scales gently with page size so tiny pages stay readable.
    dynamic_min = max(min_size, shorter * 0.06)

    return max(dynamic_min, min(fitted, page_cap, longer * 0.28))


def apply_output_watermark(
    path: Path,
    target_format: str,
    text: str,
) -> Path:
    """Stamp a translucent diagonal watermark when the target supports it."""
    normalized = target_format.lower().lstrip(".")
    mark = (text or "").strip()
    if not mark or normalized not in WATERMARKABLE_TARGETS:
        return path
    if not path.is_file() or path.stat().st_size == 0:
        raise ConversionFailedError("Cannot watermark an empty or missing output file.")

    try:
        if normalized == "pdf":
            _watermark_pdf(path, mark)
        elif normalized in _IMAGE_TARGETS:
            _watermark_image(path, mark, normalized)
        elif normalized == "html":
            _watermark_html(path, mark)
        elif normalized == "docx":
            _watermark_docx(path, mark)
    except ConversionFailedError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise ConversionFailedError(f"Output watermark failed: {exc}") from exc

    return path


def _replace_via_temp(path: Path, suffix: str, write_fn) -> None:
    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix,
        dir=path.parent,
    ) as tmp:
        tmp_path = Path(tmp.name)
        write_fn(tmp_path)
    tmp_path.replace(path)


def _watermark_pdf(path: Path, text: str) -> None:
    from pypdf import PdfReader, PdfWriter
    from reportlab.lib.colors import Color
    from reportlab.pdfgen import canvas as pdf_canvas

    reader = PdfReader(str(path))
    if not reader.pages:
        raise ConversionFailedError("PDF watermark failed: empty document.")

    writer = PdfWriter()
    label = text[:80]
    for page in reader.pages:
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        font_size = _watermark_font_size(width, height, label)
        packet = BytesIO()
        overlay = pdf_canvas.Canvas(packet, pagesize=(width, height))
        overlay.saveState()
        overlay.setFillColor(Color(0.55, 0.55, 0.58, alpha=0.16))
        overlay.setFont("Helvetica-Bold", font_size)
        overlay.translate(width / 2, height / 2)
        overlay.rotate(35)
        overlay.drawCentredString(0, 0, label)
        overlay.restoreState()
        overlay.save()
        packet.seek(0)
        stamp = PdfReader(packet)
        page.merge_page(stamp.pages[0])
        writer.add_page(page)

    def _write(tmp_path: Path) -> None:
        with tmp_path.open("wb") as handle:
            writer.write(handle)

    _replace_via_temp(path, ".pdf", _write)


def _load_font(size: int):
    from PIL import ImageFont

    for name in ("DejaVuSans-Bold.ttf", "DejaVuSans.ttf", "arialbd.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _watermark_image(path: Path, text: str, target: str) -> None:
    from PIL import Image, ImageDraw

    with Image.open(path) as image:
        image.load()
        working = image.convert("RGBA")

    width, height = working.size
    label = text[:80]
    font_size = int(round(_watermark_font_size(width, height, label, min_size=28.0)))
    font = _load_font(max(font_size, 12))

    # Draw on a transparent layer, then rotate around the image center.
    layer = Image.new("RGBA", working.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    bbox = draw.textbbox((0, 0), label, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (width - text_w) / 2 - bbox[0]
    y = (height - text_h) / 2 - bbox[1]
    draw.text((x, y), label, font=font, fill=(180, 180, 185, 48))

    rotated = layer.rotate(35, expand=False, resample=Image.Resampling.BICUBIC)
    branded = Image.alpha_composite(working, rotated)

    save_kwargs: dict[str, object] = {}
    if target == "jpg":
        branded = branded.convert("RGB")
        save_kwargs["quality"] = 90
        save_kwargs["optimize"] = True
        save_format = "JPEG"
    elif target == "webp":
        save_kwargs["quality"] = 90
        save_format = "WEBP"
    else:
        save_format = "PNG"

    def _write(tmp_path: Path) -> None:
        branded.save(tmp_path, format=save_format, **save_kwargs)

    _replace_via_temp(path, f".{target}", _write)


def _watermark_html(path: Path, text: str) -> None:
    from html import escape

    marker = 'data-asteriq-watermark="1"'
    content = path.read_text(encoding="utf-8")
    if marker in content:
        return

    label = escape(text[:80])
    # vmin tracks the smaller viewport edge so the mark scales with the page.
    badge = (
        f'<div {marker} aria-hidden="true" style="position:fixed;inset:0;'
        "pointer-events:none;z-index:9998;display:grid;place-items:center;"
        'overflow:hidden">'
        f'<span style="transform:rotate(-35deg);font:700 clamp(2.75rem,14vmin,18vmin) '
        "system-ui,Segoe UI,sans-serif;color:#9ca3af;opacity:.15;"
        "letter-spacing:0.02em;white-space:nowrap;user-select:none;"
        f'max-width:90vw;overflow:hidden;text-overflow:ellipsis">{label}</span></div>'
    )
    lower = content.lower()
    body_close = lower.rfind("</body>")
    if body_close != -1:
        branded = content[:body_close] + badge + "\n" + content[body_close:]
    else:
        branded = content.rstrip() + "\n" + badge + "\n"
    path.write_text(branded, encoding="utf-8")


def _watermark_docx(path: Path, text: str) -> None:
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Pt, RGBColor

    document = Document(str(path))
    label = text[:80]
    for section in document.sections:
        # python-docx exposes page size in EMUs (914400 EMU = 1 inch).
        page_w_pt = float(section.page_width) / 12700.0
        page_h_pt = float(section.page_height) / 12700.0
        font_size = _watermark_font_size(page_w_pt, page_h_pt, label, min_size=28.0)

        header = section.header
        header.is_linked_to_previous = False
        paragraph = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
        if paragraph.text.strip():
            paragraph = header.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = paragraph.add_run(label)
        run.font.size = Pt(font_size)
        run.font.color.rgb = RGBColor(0xC0, 0xC4, 0xCC)
        run.font.bold = True

    def _write(tmp_path: Path) -> None:
        document.save(str(tmp_path))

    _replace_via_temp(path, ".docx", _write)
