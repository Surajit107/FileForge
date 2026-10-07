from io import BytesIO

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from PIL import Image

from apps.converter.models import ConversionBatch, ConversionJob
from engines.sniff import sniff_format


def _png_bytes(color=(30, 140, 220), size=(24, 18)) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", size, color).save(buffer, format="PNG")
    return buffer.getvalue()


def _png_upload(name: str = "shot.png", color=(30, 140, 220)) -> SimpleUploadedFile:
    return SimpleUploadedFile(name, _png_bytes(color), content_type="image/png")


@override_settings(CONVERSION_SYNC_ENABLED=True, CONVERSION_RATE_LIMIT=20)
class ImageAndBatchTests(TestCase):
    def setUp(self):
        self.client = Client()
        cache.clear()

    def test_formats_api_for_png(self):
        response = self.client.get(reverse("converter:formats_api"), {"source": "png"})
        self.assertEqual(response.status_code, 200)
        targets = {item["format"] for item in response.json()["targets"]}
        self.assertEqual(targets, {"jpg", "webp", "pdf"})

    def test_single_image_conversion_json(self):
        response = self.client.post(
            reverse("converter:home"),
            {"source_file": _png_upload(), "target_format": "jpg"},
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["ok"])
        self.assertEqual(body["job"]["kind"], "job")
        self.assertEqual(body["job"]["status"], ConversionJob.Status.DONE)
        self.assertTrue(body["job"]["is_downloadable"])

        job = ConversionJob.objects.get()
        self.assertEqual(job.source_format, "png")
        self.assertEqual(job.target_format, "jpg")
        self.assertTrue(body["job"]["download_url"])
        self.assertIn("token=", body["job"]["download_url"])
        # Unsigned path must fail even for the owner.
        self.assertEqual(
            self.client.get(reverse("converter:download", args=[job.id])).status_code,
            404,
        )
        download = self.client.get(body["job"]["download_url"])
        self.assertEqual(download.status_code, 200)
        self.assertTrue(download.headers["Content-Disposition"].endswith('.jpg"'))

    def test_extension_content_mismatch_rejected(self):
        lied = SimpleUploadedFile(
            "fake.jpg",
            _png_bytes(),
            content_type="image/jpeg",
        )
        response = self.client.post(
            reverse("converter:home"),
            {"source_file": lied, "target_format": "png"},
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 400)
        body = response.json()
        self.assertFalse(body["ok"])
        self.assertIn("content looks like", body["message"].lower())

    def test_batch_image_conversion_zip(self):
        response = self.client.post(
            reverse("converter:home"),
            {
                "source_file": [
                    _png_upload("one.png", (10, 20, 30)),
                    _png_upload("two.png", (200, 100, 50)),
                ],
                "target_format": "webp",
            },
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200, response.content)
        body = response.json()
        self.assertTrue(body["ok"])
        self.assertEqual(body["job"]["kind"], "batch")
        self.assertEqual(body["job"]["status"], ConversionBatch.Status.DONE)
        self.assertEqual(body["job"]["file_count"], 2)
        self.assertTrue(body["job"]["is_downloadable"])

        batch = ConversionBatch.objects.get()
        self.assertEqual(batch.jobs.count(), 2)
        self.assertTrue(batch.zip_file)
        download_url = body["job"]["download_url"]
        self.assertTrue(download_url)
        self.assertIn("token=", download_url)
        download = self.client.get(download_url)
        self.assertEqual(download.status_code, 200)
        self.assertIn(".zip", download.headers["Content-Disposition"])

        stranger = Client()
        self.assertEqual(
            stranger.get(download_url).status_code,
            404,
        )
        self.assertEqual(
            stranger.get(reverse("converter:batch_download", args=[batch.id])).status_code,
            404,
        )

    def test_multi_file_pack_to_zip(self):
        import zipfile
        from io import BytesIO

        response = self.client.post(
            reverse("converter:home"),
            {
                "source_file": [
                    _png_upload("alpha.png", (10, 20, 30)),
                    _png_upload("beta.png", (200, 100, 50)),
                ],
                "target_format": "zip",
            },
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200, response.content)
        body = response.json()
        self.assertTrue(body["ok"])
        self.assertEqual(body["job"]["kind"], "batch")
        self.assertEqual(body["job"]["target_format"], "zip")
        self.assertEqual(body["job"]["status"], ConversionBatch.Status.DONE)
        self.assertEqual(body["job"]["file_count"], 2)
        self.assertEqual(body["job"]["done_count"], 2)
        self.assertTrue(body["job"]["is_downloadable"])

        batch = ConversionBatch.objects.get()
        self.assertEqual(batch.jobs.count(), 0)
        self.assertTrue(batch.zip_file)

        download = self.client.get(body["job"]["download_url"])
        self.assertEqual(download.status_code, 200)
        with zipfile.ZipFile(BytesIO(b"".join(download.streaming_content))) as archive:
            names = set(archive.namelist())
            self.assertEqual(names, {"alpha.png", "beta.png"})

    @override_settings(CONVERSION_RATE_LIMIT=2, CONVERSION_RATE_WINDOW_SEC=3600)
    def test_rate_limit_returns_429(self):
        cache.clear()
        for _ in range(2):
            ok = self.client.post(
                reverse("converter:home"),
                {"source_file": _png_upload(), "target_format": "jpg"},
                HTTP_ACCEPT="application/json",
                HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            )
            self.assertEqual(ok.status_code, 200)

        blocked = self.client.post(
            reverse("converter:home"),
            {"source_file": _png_upload("third.png"), "target_format": "jpg"},
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(blocked.status_code, 429)
        self.assertIn("Retry-After", blocked.headers)
        self.assertFalse(blocked.json()["ok"])

    def test_sniff_png_helper(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "x.png"
            path.write_bytes(_png_bytes())
            self.assertEqual(sniff_format(path), "png")
