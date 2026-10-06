from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase
from PIL import Image

from engines.exceptions import UnsupportedConversionError
from engines.image.engine import IMAGE_SOURCES, IMAGE_TARGETS, convert_image
from engines.registry import convert_file, get_pair, targets_for
from engines.sniff import sniff_format


def _write_image(path: Path, fmt: str, *, mode: str = "RGB", size=(32, 24)) -> Path:
    color = (40, 120, 200) if mode == "RGB" else (40, 120, 200, 255)
    image = Image.new(mode, size, color)
    save_format = {"jpg": "JPEG", "png": "PNG", "webp": "WEBP", "gif": "GIF", "bmp": "BMP"}[
        fmt
    ]
    kwargs = {}
    if fmt == "jpg":
        image = image.convert("RGB")
    image.save(path, format=save_format, **kwargs)
    return path


class ImageEngineTests(SimpleTestCase):
    def test_image_targets_registered(self):
        for source in IMAGE_SOURCES:
            targets = {pair.target for pair in targets_for(source)}
            expected = set(IMAGE_TARGETS) - {source}
            self.assertEqual(targets, expected)
            for target in expected:
                self.assertEqual(get_pair(source, target).category, "images")

    def test_identity_pairs_not_registered(self):
        for fmt in ("png", "jpg", "webp"):
            with self.assertRaises(UnsupportedConversionError):
                get_pair(fmt, fmt)

    def test_all_image_pairs_convert(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixtures = {
                "png": _write_image(root / "a.png", "png", mode="RGBA"),
                "jpg": _write_image(root / "a.jpg", "jpg"),
                "webp": _write_image(root / "a.webp", "webp"),
                "gif": _write_image(root / "a.gif", "gif"),
                "bmp": _write_image(root / "a.bmp", "bmp"),
            }
            for source, source_path in fixtures.items():
                for target in IMAGE_TARGETS:
                    if source == target:
                        continue
                    destination = root / f"{source}_to_{target}.{target}"
                    result = convert_file(source_path, source, target, destination)
                    self.assertTrue(result.exists())
                    self.assertGreater(result.stat().st_size, 0)

    def test_sniff_detects_image_bytes(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            png = _write_image(root / "x.png", "png")
            jpg = _write_image(root / "x.jpg", "jpg")
            self.assertEqual(sniff_format(png), "png")
            self.assertEqual(sniff_format(jpg), "jpg")

    def test_sniff_rejects_extension_mismatch_bytes(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            real_png = _write_image(root / "real.png", "png")
            lied = root / "lied.jpg"
            lied.write_bytes(real_png.read_bytes())
            self.assertEqual(sniff_format(lied, declared_filename="lied.jpg"), "png")

    def test_convert_image_helper_pdf(self):
        with TemporaryDirectory() as tmp:
            source = _write_image(Path(tmp) / "s.png", "png")
            destination = Path(tmp) / "out.pdf"
            convert_image(source, destination, "pdf")
            self.assertTrue(destination.read_bytes().startswith(b"%PDF"))
