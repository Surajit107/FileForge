from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase
from PIL import Image

from engines.markdown.pipeline import build_html, build_pdf, parse_markdown
from engines.watermark import (
    WATERMARKABLE_TARGETS,
    _watermark_font_size,
    apply_output_watermark,
)


def _write_png(path: Path, size=(160, 120)) -> Path:
    Image.new("RGB", size, (40, 120, 200)).save(path, format="PNG")
    return path


class OutputWatermarkTests(SimpleTestCase):
    def test_watermarkable_targets(self):
        self.assertEqual(
            WATERMARKABLE_TARGETS,
            frozenset({"pdf", "png", "jpg", "webp", "html", "docx"}),
        )

    def test_font_size_scales_with_page(self):
        small = _watermark_font_size(400, 300, "Acme")
        large = _watermark_font_size(1600, 1200, "Acme")
        self.assertGreater(large, small * 2)
        # Long labels must shrink relative to short ones on the same page.
        short = _watermark_font_size(800, 600, "OK")
        long = _watermark_font_size(800, 600, "Confidential Internal Draft Copy")
        self.assertGreater(short, long)

    def test_skips_empty_text(self):
        with TemporaryDirectory() as tmp:
            path = _write_png(Path(tmp) / "shot.png")
            before = path.read_bytes()
            apply_output_watermark(path, "png", "  ")
            self.assertEqual(path.read_bytes(), before)

    def test_watermarks_pdf(self):
        with TemporaryDirectory() as tmp:
            document = parse_markdown("# Hello\n\nBody text.\n")
            out = Path(tmp) / "out.pdf"
            build_pdf(document, out)
            apply_output_watermark(out, "pdf", "Confidential")
            raw = out.read_bytes()
            self.assertTrue(raw.startswith(b"%PDF"))
            self.assertIn(b"Confidential", raw)

    def test_watermarks_html(self):
        with TemporaryDirectory() as tmp:
            document = parse_markdown("# Hello\n\nBody text.\n")
            out = Path(tmp) / "out.html"
            build_html(document, out)
            apply_output_watermark(out, "html", "Draft")
            html = out.read_text(encoding="utf-8")
            self.assertIn('data-asteriq-watermark="1"', html)
            self.assertIn("Draft", html)
