from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase
from docx import Document

from engines.exceptions import UnsupportedConversionError
from engines.registry import convert_file, get_pair, list_pairs, targets_for


class RegistryTests(SimpleTestCase):
    def test_md_pairs_registered(self):
        targets = {pair.target for pair in targets_for("md")}
        self.assertEqual(targets, {"pdf", "docx", "html", "txt"})
        self.assertGreaterEqual(len(list_pairs()), 20)

    def test_docx_and_pdf_pairs_registered(self):
        self.assertEqual(
            {pair.target for pair in targets_for("docx")},
            {"pdf", "txt", "md"},
        )
        self.assertEqual(
            {pair.target for pair in targets_for("pdf")},
            {"txt", "md", "docx"},
        )
        self.assertTrue(get_pair("pdf", "md").best_effort)
        self.assertTrue(get_pair("docx", "pdf").best_effort)

    def test_unknown_pair_raises(self):
        with self.assertRaises(UnsupportedConversionError):
            get_pair("md", "mp4")

    def test_markdown_to_pdf(self):
        with TemporaryDirectory() as tmp:
            source = Path(tmp) / "sample.md"
            source.write_text("# Hello\n\nWorld", encoding="utf-8")
            destination = Path(tmp) / "sample.pdf"
            result = convert_file(source, "md", "pdf", destination)
            self.assertTrue(result.exists())
            self.assertGreater(result.stat().st_size, 0)

    def test_markdown_to_html_and_txt(self):
        with TemporaryDirectory() as tmp:
            source = Path(tmp) / "sample.md"
            source.write_text("# Hello\n\nWorld", encoding="utf-8")
            html = convert_file(source, "md", "html", Path(tmp) / "sample.html")
            txt = convert_file(source, "md", "txt", Path(tmp) / "sample.txt")
            self.assertIn("<h1>Hello</h1>", html.read_text(encoding="utf-8"))
            self.assertIn("Hello", txt.read_text(encoding="utf-8"))

    def test_docx_to_txt(self):
        with TemporaryDirectory() as tmp:
            source = Path(tmp) / "sample.docx"
            document = Document()
            document.add_heading("Title", level=1)
            document.add_paragraph("Body text")
            document.save(str(source))
            destination = Path(tmp) / "sample.txt"
            result = convert_file(source, "docx", "txt", destination)
            text = result.read_text(encoding="utf-8")
            self.assertIn("Title", text)
            self.assertIn("Body text", text)
