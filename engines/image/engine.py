"""Pillow-based image conversion engines."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

from engines.exceptions import ConversionFailedError

IMAGE_SOURCES: frozenset[str] = frozenset({"png", "jpg", "webp", "gif", "bmp"})
IMAGE_TARGETS: frozenset[str] = frozenset({"png", "jpg", "webp", "pdf"})

_TARGET_LABELS: dict[str, str] = {
    "png": "PNG",
    "jpg": "JPG",
    "webp": "WEBP",
    "pdf": "PDF",
}

_PIL_SAVE_FORMAT: dict[str, str] = {
    "png": "PNG",
    "jpg": "JPEG",
    "webp": "WEBP",
    "pdf": "PDF",
}


def open_image(source_path: Path) -> Image.Image:
    """Open an image, apply EXIF orientation, and take the first frame."""
    try:
        image = Image.open(source_path)
        image.load()
    except (OSError, UnidentifiedImageError, ValueError) as exc:
        raise ConversionFailedError(f"Unable to open image: {exc}") from exc

    image = ImageOps.exif_transpose(image) or image

    # Animated GIF/WEBP: convert the first frame only.
    if getattr(image, "is_animated", False) or getattr(image, "n_frames", 1) > 1:
        try:
            image.seek(0)
        except EOFError:
            pass
        image = image.copy()

    return image


def prepare_for_target(image: Image.Image, target: str) -> Image.Image:
    """Normalize color mode for the destination format."""
    if target == "jpg" or target == "pdf":
        if image.mode in {"RGBA", "LA"}:
            background = Image.new("RGB", image.size, (255, 255, 255))
            alpha = image.getchannel("A") if "A" in image.getbands() else None
            rgb = image.convert("RGBA")
            background.paste(rgb, mask=alpha)
            return background
        if image.mode == "P":
            converted = image.convert("RGBA")
            background = Image.new("RGB", converted.size, (255, 255, 255))
            background.paste(converted, mask=converted.getchannel("A"))
            return background
        if image.mode != "RGB":
            return image.convert("RGB")
        return image

    if target == "png":
        if image.mode in {"P", "LA"}:
            return image.convert("RGBA")
        if image.mode == "CMYK":
            return image.convert("RGB")
        return image

    if target == "webp":
        if image.mode == "P":
            return image.convert("RGBA")
        if image.mode == "CMYK":
            return image.convert("RGB")
        return image

    return image


def convert_image(source_path: Path, destination_path: Path, target: str) -> Path:
    target = target.lower()
    if target not in IMAGE_TARGETS:
        raise ConversionFailedError(f"Unsupported image target: {target}")

    image = open_image(source_path)
    try:
        prepared = prepare_for_target(image, target)
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        save_kwargs: dict = {}
        if target == "jpg":
            save_kwargs["quality"] = 90
            save_kwargs["optimize"] = True
        elif target == "webp":
            save_kwargs["quality"] = 90
        prepared.save(destination_path, format=_PIL_SAVE_FORMAT[target], **save_kwargs)
    except ConversionFailedError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise ConversionFailedError(f"Image→{target.upper()} failed: {exc}") from exc
    finally:
        image.close()

    if not destination_path.exists() or destination_path.stat().st_size == 0:
        raise ConversionFailedError(f"Image→{target.upper()} produced an empty file.")
    return destination_path


class ImageConversionEngine:
    """Parameterized engine for one image source → target pair."""

    def __init__(self, source_format: str, target_format: str) -> None:
        self.source_format = source_format
        self.target_format = target_format

    def convert(self, source_path: Path, destination_path: Path) -> Path:
        return convert_image(source_path, destination_path, self.target_format)


def build_image_engines() -> list[tuple[str, str, str, ImageConversionEngine]]:
    """Return (source, target, label, engine) for every non-identity image pair."""
    entries: list[tuple[str, str, str, ImageConversionEngine]] = []
    for source in sorted(IMAGE_SOURCES):
        for target in sorted(IMAGE_TARGETS):
            if source == target:
                continue
            # bmp/gif are sources only — never targets in the F3 matrix.
            label = _TARGET_LABELS[target]
            entries.append(
                (
                    source,
                    target,
                    label,
                    ImageConversionEngine(source, target),
                )
            )
    return entries
