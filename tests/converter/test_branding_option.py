from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from apps.converter.forms import ConversionForm
from apps.converter.models import ConversionJob


@override_settings(CONVERSION_SYNC_ENABLED=True, OUTPUT_BRANDING_ENABLED=True)
class OptionalBrandingTests(TestCase):
    def setUp(self):
        self.client = Client()

    def _md_upload(self, **extra):
        payload = SimpleUploadedFile(
            "note.md",
            b"# Title\n\nHello **world**",
            content_type="text/markdown",
        )
        data = {"source_file": payload, "target_format": "pdf", **extra}
        return self.client.post(reverse("converter:home"), data)

    def test_home_shows_branding_and_watermark_options(self):
        response = self.client.get(reverse("converter:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Add branding")
        self.assertContains(response, "Brand name")
        self.assertContains(response, "Add watermark")
        self.assertContains(response, "Use brand name")
        self.assertContains(response, "Custom text")

    def test_default_conversion_has_no_branding(self):
        response = self._md_upload()
        self.assertEqual(response.status_code, 302)
        job = ConversionJob.objects.get()
        self.assertFalse(job.branding_enabled)
        self.assertFalse(job.watermark_enabled)
        self.assertEqual(job.brand_name, "")
        raw = job.output_file.read()
        self.assertNotIn(b"Acme Corp", raw)

    def test_opt_in_stamps_brand_name(self):
        response = self._md_upload(add_branding="on", brand_name="Acme Corp")
        self.assertEqual(response.status_code, 302)
        job = ConversionJob.objects.get()
        self.assertTrue(job.branding_enabled)
        self.assertEqual(job.brand_name, "Acme Corp")
        raw = job.output_file.read()
        self.assertIn(b"Acme Corp", raw)

    def test_checked_without_name_is_invalid(self):
        payload = SimpleUploadedFile(
            "note.md",
            b"# Title\n\nHello",
            content_type="text/markdown",
        )
        response = self.client.post(
            reverse("converter:home"),
            {
                "source_file": payload,
                "target_format": "pdf",
                "add_branding": "on",
                "brand_name": "",
            },
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 400)
        body = response.json()
        self.assertFalse(body["ok"])
        self.assertIn("brand_name", body["errors"])
        self.assertEqual(ConversionJob.objects.count(), 0)

    def test_form_requires_brand_name_when_enabled(self):
        from django.http import QueryDict
        from django.utils.datastructures import MultiValueDict

        payload = SimpleUploadedFile(
            "note.md",
            b"# Title\n",
            content_type="text/markdown",
        )
        data = QueryDict(mutable=True)
        data.update({"target_format": "pdf", "add_branding": "on", "brand_name": ""})
        form = ConversionForm(
            data=data,
            files=MultiValueDict({"source_file": [payload]}),
        )
        self.assertFalse(form.is_valid())
        self.assertIn("brand_name", form.errors)

    def test_watermark_follows_brand_name(self):
        response = self._md_upload(
            add_watermark="on",
            watermark_source="brand",
            brand_name="Acme Corp",
        )
        self.assertEqual(response.status_code, 302)
        job = ConversionJob.objects.get()
        self.assertFalse(job.branding_enabled)
        self.assertTrue(job.watermark_enabled)
        self.assertTrue(job.watermark_follow_brand)
        self.assertEqual(job.brand_name, "Acme Corp")
        self.assertEqual(job.watermark_text, "")
        raw = job.output_file.read()
        self.assertIn(b"Acme Corp", raw)

    def test_watermark_custom_text(self):
        response = self._md_upload(
            add_watermark="on",
            watermark_source="custom",
            watermark_text="Confidential",
        )
        self.assertEqual(response.status_code, 302)
        job = ConversionJob.objects.get()
        self.assertTrue(job.watermark_enabled)
        self.assertFalse(job.watermark_follow_brand)
        self.assertEqual(job.watermark_text, "Confidential")
        raw = job.output_file.read()
        self.assertIn(b"Confidential", raw)

    def test_branding_and_watermark_together(self):
        response = self._md_upload(
            add_branding="on",
            brand_name="Acme Corp",
            add_watermark="on",
            watermark_source="custom",
            watermark_text="Draft",
        )
        self.assertEqual(response.status_code, 302)
        job = ConversionJob.objects.get()
        self.assertTrue(job.branding_enabled)
        self.assertTrue(job.watermark_enabled)
        self.assertEqual(job.brand_name, "Acme Corp")
        self.assertEqual(job.watermark_text, "Draft")
        raw = job.output_file.read()
        self.assertIn(b"Acme Corp", raw)
        self.assertIn(b"Draft", raw)

    def test_custom_watermark_requires_text(self):
        payload = SimpleUploadedFile(
            "note.md",
            b"# Title\n\nHello",
            content_type="text/markdown",
        )
        response = self.client.post(
            reverse("converter:home"),
            {
                "source_file": payload,
                "target_format": "pdf",
                "add_watermark": "on",
                "watermark_source": "custom",
                "watermark_text": "",
            },
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 400)
        body = response.json()
        self.assertIn("watermark_text", body["errors"])
        self.assertEqual(ConversionJob.objects.count(), 0)
