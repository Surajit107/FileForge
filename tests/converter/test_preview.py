from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from apps.converter.services.preview import is_previewable, preview_mode


@override_settings(CONVERSION_SYNC_ENABLED=True, OUTPUT_BRANDING_ENABLED=True)
class PreviewResultTests(TestCase):
    def setUp(self):
        self.client = Client()

    def _convert(self, *, name="note.md", content=b"# Title\n\nHello", target="pdf"):
        payload = SimpleUploadedFile(name, content, content_type="text/markdown")
        return self.client.post(
            reverse("converter:home"),
            {"source_file": payload, "target_format": target},
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

    def test_previewable_formats(self):
        self.assertTrue(is_previewable("pdf"))
        self.assertTrue(is_previewable("png"))
        self.assertTrue(is_previewable("html"))
        self.assertTrue(is_previewable("txt"))
        self.assertFalse(is_previewable("docx"))
        self.assertFalse(is_previewable("zip"))
        self.assertEqual(preview_mode("pdf"), "pdf")
        self.assertEqual(preview_mode("html"), "html")
        self.assertEqual(preview_mode("png"), "image")

    def test_pdf_job_exposes_preview_url(self):
        response = self._convert(target="pdf")
        self.assertEqual(response.status_code, 200)
        job = response.json()["job"]
        self.assertTrue(job["is_downloadable"])
        self.assertTrue(job["preview_url"])
        self.assertIn("/preview/", job["preview_url"])
        self.assertIn("token=", job["preview_url"])
        self.assertEqual(job["preview_mode"], "pdf")

    def test_preview_requires_signed_token(self):
        response = self._convert(target="pdf")
        job = response.json()["job"]
        job_id = job["id"]
        preview_url = job["preview_url"]

        self.assertEqual(
            self.client.get(reverse("converter:preview", args=[job_id])).status_code,
            404,
        )
        ok = self.client.get(preview_url)
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(ok["Content-Type"], "application/pdf")
        self.assertIn("inline", ok["Content-Disposition"])
        payload = b"".join(ok.streaming_content)
        self.assertTrue(payload.startswith(b"%PDF"))

    def test_html_preview_is_inline(self):
        response = self._convert(target="html")
        self.assertEqual(response.status_code, 200)
        job = response.json()["job"]
        self.assertEqual(job["preview_mode"], "html")
        ok = self.client.get(job["preview_url"])
        self.assertEqual(ok.status_code, 200)
        self.assertIn("text/html", ok["Content-Type"])
        payload = b"".join(ok.streaming_content)
        self.assertIn(b"<", payload)

    def test_docx_has_no_preview(self):
        response = self._convert(target="docx")
        self.assertEqual(response.status_code, 200)
        job = response.json()["job"]
        self.assertIsNone(job["preview_url"])
        self.assertIsNone(job["preview_mode"])
