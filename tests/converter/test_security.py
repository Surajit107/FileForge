"""Security checklist coverage: filenames, limits, signed downloads, sniff."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from PIL import Image

from apps.converter.exceptions import InvalidUploadError
from apps.converter.services.filenames import sanitize_display_name, storage_object_name
from apps.converter.services.limits import enforce_content_limits
from engines.sniff import sniff_format


class FilenameSanitizationTests(TestCase):
    def test_strips_path_and_controls(self):
        self.assertEqual(
            sanitize_display_name("../../evil\nname.pdf"),
            "evil_name.pdf",
        )

    def test_storage_name_is_opaque_uuid(self):
        name = storage_object_name("../../note.md", format_hint="md")
        self.assertTrue(name.endswith(".md"))
        self.assertNotIn("..", name)
        self.assertNotIn("note", name)
        self.assertEqual(len(Path(name).stem), 32)


class SniffAllowlistTests(TestCase):
    def test_extensionless_text_is_not_invented_as_md(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "blob"
            path.write_bytes(b"# Hello\n\nworld\n")
            self.assertIsNone(sniff_format(path, declared_filename="blob"))


@override_settings(CONVERSION_MAX_PDF_PAGES=1, CONVERSION_MAX_IMAGE_PIXELS=100)
class ContentLimitTests(TestCase):
    def test_image_pixel_cap(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "big.png"
            Image.new("RGB", (20, 20), (1, 2, 3)).save(path)
            with self.assertRaises(InvalidUploadError):
                enforce_content_limits(path, "png")

    def test_pdf_page_cap(self):
        # Minimal two-page-ish PDF via pypdf if available; otherwise skip structure.
        from pypdf import PdfWriter

        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "two.pdf"
            writer = PdfWriter()
            writer.add_blank_page(width=72, height=72)
            writer.add_blank_page(width=72, height=72)
            with path.open("wb") as handle:
                writer.write(handle)
            with self.assertRaises(InvalidUploadError):
                enforce_content_limits(path, "pdf")


@override_settings(CONVERSION_SYNC_ENABLED=True)
class SignedDownloadTests(TestCase):
    def setUp(self):
        self.client = Client()

    def _convert_md(self):
        payload = SimpleUploadedFile(
            "note.md",
            b"# Title\n\nHello",
            content_type="text/markdown",
        )
        return self.client.post(
            reverse("converter:home"),
            {"source_file": payload, "target_format": "pdf"},
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

    def test_download_requires_signed_token(self):
        response = self._convert_md()
        self.assertEqual(response.status_code, 200)
        body = response.json()
        job_id = body["job"]["id"]
        download_url = body["job"]["download_url"]
        self.assertIn("token=", download_url)

        self.assertEqual(
            self.client.get(reverse("converter:download", args=[job_id])).status_code,
            404,
        )
        ok = self.client.get(download_url)
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(ok["Content-Type"], "application/octet-stream")
