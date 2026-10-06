from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from apps.converter.models import ConversionJob


@override_settings(CONVERSION_SYNC_ENABLED=True, HISTORY_PAGE_SIZE=2)
class ConvertViewTests(TestCase):
    def setUp(self):
        self.client = Client()

    def _upload(self, name: str = "note.md", client: Client | None = None):
        active = client or self.client
        payload = SimpleUploadedFile(
            name,
            b"# Title\n\nHello **world**",
            content_type="text/markdown",
        )
        return active.post(
            reverse("converter:home"),
            {"source_file": payload, "target_format": "pdf"},
        )

    def test_home_renders(self):
        response = self.client.get(reverse("converter:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Convert a file")

    def test_markdown_conversion_flow(self):
        response = self._upload()
        self.assertEqual(response.status_code, 302)
        self.assertIn("/jobs/", response["Location"])

        job = ConversionJob.objects.get()
        self.assertEqual(job.status, ConversionJob.Status.DONE)
        self.assertTrue(job.owner_session_key)

        status = self.client.get(reverse("converter:job_status", args=[job.id]))
        self.assertEqual(status.status_code, 200)
        self.assertEqual(status.json()["progress"], "Ready")

        history = self.client.get(reverse("converter:history"))
        self.assertEqual(history.status_code, 200)
        self.assertContains(history, "note.md")

    def test_markdown_conversion_json_same_page(self):
        payload = SimpleUploadedFile(
            "note.md",
            b"# Title\n\nHello **world**",
            content_type="text/markdown",
        )
        response = self.client.post(
            reverse("converter:home"),
            {"source_file": payload, "target_format": "pdf"},
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["ok"])
        self.assertEqual(body["job"]["status"], ConversionJob.Status.DONE)
        self.assertEqual(body["job"]["progress"], "Ready")
        self.assertTrue(body["job"]["is_downloadable"])
        self.assertIn("/jobs/", body["job"]["detail_url"])

    def test_foreign_session_cannot_access_job(self):
        self._upload("owner.md")
        job = ConversionJob.objects.get()

        stranger = Client()
        self.assertEqual(
            stranger.get(reverse("converter:job_detail", args=[job.id])).status_code,
            404,
        )
        self.assertEqual(
            stranger.get(reverse("converter:job_status", args=[job.id])).status_code,
            404,
        )
        self.assertEqual(
            stranger.get(reverse("converter:download", args=[job.id])).status_code,
            404,
        )

        history = stranger.get(reverse("converter:history"))
        self.assertEqual(history.status_code, 200)
        self.assertNotContains(history, "owner.md")

    def test_history_is_session_isolated(self):
        self._upload("mine.md")

        other = Client()
        self._upload("theirs.md", client=other)

        mine = self.client.get(reverse("converter:history"))
        theirs = other.get(reverse("converter:history"))

        self.assertContains(mine, "mine.md")
        self.assertNotContains(mine, "theirs.md")
        self.assertContains(theirs, "theirs.md")
        self.assertNotContains(theirs, "mine.md")

    def test_history_pagination(self):
        for index in range(5):
            self._upload(f"page-{index}.md")

        page1 = self.client.get(reverse("converter:history"))
        self.assertEqual(page1.status_code, 200)
        self.assertContains(page1, "Page 1 of 3")
        self.assertContains(page1, "page-4.md")
        self.assertContains(page1, "page-3.md")
        self.assertNotContains(page1, "page-0.md")

        page2 = self.client.get(reverse("converter:history"), {"page": 2})
        self.assertContains(page2, "Page 2 of 3")
        self.assertContains(page2, "page-2.md")
        self.assertContains(page2, "page-1.md")

        page3 = self.client.get(reverse("converter:history"), {"page": 3})
        self.assertContains(page3, "Page 3 of 3")
        self.assertContains(page3, "page-0.md")

    def test_formats_api_for_pdf(self):
        response = self.client.get(reverse("converter:formats_api"), {"source": "pdf"})
        self.assertEqual(response.status_code, 200)
        targets = {item["format"] for item in response.json()["targets"]}
        self.assertEqual(targets, {"txt", "md", "docx"})

    def test_healthcheck(self):
        response = self.client.get(reverse("healthcheck"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
