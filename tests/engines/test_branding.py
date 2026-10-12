from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase
from PIL import Image

from engines.branding import BRANDABLE_TARGETS, apply_output_branding
from engines.markdown.pipeline import build_html, build_pdf, parse_markdown


def _write_png(path: Path, size=(120, 80)) -> Path:
    Image.new("RGB", size, (40, 120, 200)).save(path, format="PNG")
    return path


class OutputBrandingTests(SimpleTestCase):
    def test_brandable_targets(self):
        self.assertEqual(
            BRANDABLE_TARGETS,
            frozenset({"pdf", "png", "jpg", "webp", "html", "docx"}),
        )

    def test_skips_empty_brand_text(self):
        with TemporaryDirectory() as tmp:
            path = _write_png(Path(tmp) / "shot.png")
            before = path.read_bytes()
            apply_output_branding(path, "png", "   ")
            self.assertEqual(path.read_bytes(), before)

    def test_skips_non_visual_targets(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "notes.txt"
            path.write_text("hello\n", encoding="utf-8")
            before = path.read_bytes()
            apply_output_branding(path, "txt", "Acme Corp")
            self.assertEqual(path.read_bytes(), before)

    def test_stamps_png_bottom_right(self):
        with TemporaryDirectory() as tmp:
            path = _write_png(Path(tmp) / "shot.png")
            apply_output_branding(path, "png", "Acme Corp")
            self.assertGreater(path.stat().st_size, 0)
            with Image.open(path) as image:
                self.assertEqual(image.size, (120, 80))

    def test_stamps_pdf(self):
        with TemporaryDirectory() as tmp:
            source = Path(tmp) / "doc.md"
            source.write_text("# Hello\n\nBody text.\n", encoding="utf-8")
            document = parse_markdown(source.read_text(encoding="utf-8"))
            out = Path(tmp) / "out.pdf"
            build_pdf(document, out)
            apply_output_branding(out, "pdf", "Acme Corp")
            raw = out.read_bytes()
            self.assertTrue(raw.startswith(b"%PDF"))
            self.assertIn(b"Acme Corp", raw)

    def test_stamps_html(self):
        with TemporaryDirectory() as tmp:
            source = Path(tmp) / "doc.md"
            source.write_text("# Hello\n\nBody text.\n", encoding="utf-8")
            document = parse_markdown(source.read_text(encoding="utf-8"))
            out = Path(tmp) / "out.html"
            build_html(document, out)
            apply_output_branding(out, "html", "Acme Corp")
            html = out.read_text(encoding="utf-8")
            self.assertIn('data-asteriq-brand="1"', html)
            self.assertIn("Acme Corp", html)
            apply_output_branding(out, "html", "Acme Corp")
            self.assertEqual(html.count('data-asteriq-brand="1"'), 1)
