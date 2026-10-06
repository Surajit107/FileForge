"""Audio / video conversion engines (ffmpeg)."""

from __future__ import annotations

from pathlib import Path

from engines.base import ConversionEngine
from engines.exceptions import ConversionFailedError
from engines.media.ffmpeg import convert_with_ffmpeg

AUDIO_SOURCES: frozenset[str] = frozenset({"mp3", "wav", "flac", "ogg"})
AUDIO_TARGETS: frozenset[str] = frozenset({"mp3", "wav", "flac", "ogg"})
VIDEO_SOURCES: frozenset[str] = frozenset({"mp4", "webm", "mkv"})
VIDEO_TARGETS: frozenset[str] = frozenset({"mp4", "webm", "mkv"})
# Extract soundtrack from video — common personal-converter need.
VIDEO_AUDIO_TARGETS: frozenset[str] = frozenset({"mp3", "wav"})

MEDIA_SOURCES: frozenset[str] = AUDIO_SOURCES | VIDEO_SOURCES

_TARGET_LABELS: dict[str, str] = {
    "mp3": "MP3",
    "wav": "WAV",
    "flac": "FLAC",
    "ogg": "OGG",
    "mp4": "MP4",
    "webm": "WEBM",
    "mkv": "MKV",
}

_MEDIA_MAX_BYTES = 100 * 1024 * 1024
_AUDIO_TIMEOUT_SEC = 180
_VIDEO_TIMEOUT_SEC = 600


class MediaConversionEngine:
    """Parameterized engine for one media source → target pair."""

    def __init__(
        self,
        source_format: str,
        target_format: str,
        *,
        timeout_sec: int,
    ) -> None:
        self.source_format = source_format
        self.target_format = target_format
        self.timeout_sec = timeout_sec

    def convert(self, source_path: Path, destination_path: Path) -> Path:
        try:
            return convert_with_ffmpeg(
                source_path,
                destination_path,
                self.target_format,
                timeout_sec=self.timeout_sec,
            )
        except ConversionFailedError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise ConversionFailedError(
                f"{self.source_format.upper()}→{self.target_format.upper()} failed: {exc}"
            ) from exc


def build_media_engines() -> list[tuple[str, str, str, ConversionEngine, int, int]]:
    """Return (source, target, label, engine, max_bytes, timeout_sec) tuples."""
    entries: list[tuple[str, str, str, ConversionEngine, int, int]] = []

    for source in sorted(AUDIO_SOURCES):
        for target in sorted(AUDIO_TARGETS):
            if source == target:
                continue
            entries.append(
                (
                    source,
                    target,
                    _TARGET_LABELS[target],
                    MediaConversionEngine(
                        source, target, timeout_sec=_AUDIO_TIMEOUT_SEC
                    ),
                    _MEDIA_MAX_BYTES,
                    _AUDIO_TIMEOUT_SEC,
                )
            )

    for source in sorted(VIDEO_SOURCES):
        for target in sorted(VIDEO_TARGETS):
            if source == target:
                continue
            entries.append(
                (
                    source,
                    target,
                    _TARGET_LABELS[target],
                    MediaConversionEngine(
                        source, target, timeout_sec=_VIDEO_TIMEOUT_SEC
                    ),
                    _MEDIA_MAX_BYTES,
                    _VIDEO_TIMEOUT_SEC,
                )
            )
        for target in sorted(VIDEO_AUDIO_TARGETS):
            entries.append(
                (
                    source,
                    target,
                    f"{_TARGET_LABELS[target]} (audio)",
                    MediaConversionEngine(
                        source, target, timeout_sec=_AUDIO_TIMEOUT_SEC
                    ),
                    _MEDIA_MAX_BYTES,
                    _AUDIO_TIMEOUT_SEC,
                )
            )

    return entries
