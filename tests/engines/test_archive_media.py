"""Tests for archive (F5) and media (F6) conversion pairs."""

from __future__ import annotations

import tarfile
import unittest
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
from wave import open as wave_open

from django.test import SimpleTestCase

from engines.archive import find_7z
from engines.media import find_ffmpeg
from engines.registry import (
    convert_file,
    detect_format_from_filename,
    get_pair,
    targets_for,
)
from engines.sniff import sniff_format


def _write_zip(path: Path, files: dict[str, bytes]) -> Path:
    with zipfile.ZipFile(path, "w") as archive:
        for name, payload in files.items():
            archive.writestr(name, payload)
    return path


def _write_tar(path: Path, files: dict[str, bytes], *, gzipped: bool = False) -> Path:
    mode = "w:gz" if gzipped else "w"
    with tarfile.open(path, mode) as archive:
        for name, payload in files.items():
            member = tarfile.TarInfo(name=name)
            member.size = len(payload)
            from io import BytesIO

            archive.addfile(member, BytesIO(payload))
    return path


def _write_wav(path: Path, *, frames: int = 2400) -> Path:
    with wave_open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(8000)
        handle.writeframes(b"\x00\x00" * frames)
    return path


class ArchiveRegistryTests(SimpleTestCase):
    def test_archive_pairs_registered(self):
        self.assertEqual(
            {pair.target for pair in targets_for("zip")},
            {"tar", "tgz", "7z"},
        )
        self.assertEqual(get_pair("zip", "tar").category, "archives")
        self.assertTrue(get_pair("zip", "7z").best_effort)
        self.assertFalse(get_pair("zip", "tar").best_effort)

    def test_detect_tarball_filename(self):
        self.assertEqual(detect_format_from_filename("bundle.tar.gz"), "tgz")
        self.assertEqual(detect_format_from_filename("bundle.tgz"), "tgz")
        self.assertEqual(detect_format_from_filename("bundle.zip"), "zip")


class ArchiveConversionTests(SimpleTestCase):
    def test_zip_tar_tgz_roundtrip(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            zip_path = _write_zip(root / "a.zip", {"readme.txt": b"hello archive"})
            tar_path = root / "a.tar"
            convert_file(zip_path, "zip", "tar", tar_path)
            self.assertTrue(tar_path.exists())
            self.assertGreater(tar_path.stat().st_size, 0)

            tgz_path = root / "a.tar.gz"
            convert_file(tar_path, "tar", "tgz", tgz_path)
            out_zip = root / "roundtrip.zip"
            convert_file(tgz_path, "tgz", "zip", out_zip)

            with zipfile.ZipFile(out_zip) as archive:
                self.assertEqual(archive.read("readme.txt"), b"hello archive")

    def test_sniff_archive_formats(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            zip_path = _write_zip(root / "plain.zip", {"a.txt": b"x"})
            tar_path = _write_tar(root / "plain.tar", {"a.txt": b"x"})
            tgz_path = _write_tar(root / "plain.tar.gz", {"a.txt": b"x"}, gzipped=True)
            self.assertEqual(sniff_format(zip_path), "zip")
            self.assertEqual(sniff_format(tar_path), "tar")
            self.assertEqual(sniff_format(tgz_path, declared_filename="plain.tar.gz"), "tgz")

    def test_zip_slip_rejected(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            evil = root / "evil.zip"
            with zipfile.ZipFile(evil, "w") as archive:
                archive.writestr("../escape.txt", b"nope")
            with self.assertRaises(Exception):
                convert_file(evil, "zip", "tar", root / "out.tar")


@unittest.skipUnless(find_7z() is not None, "7-Zip not installed")
class SevenZipConversionTests(SimpleTestCase):
    def test_zip_to_7z_and_back(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            zip_path = _write_zip(root / "a.zip", {"data.bin": b"\x01\x02\x03"})
            seven = root / "a.7z"
            convert_file(zip_path, "zip", "7z", seven)
            self.assertTrue(seven.exists())
            back = root / "back.zip"
            convert_file(seven, "7z", "zip", back)
            with zipfile.ZipFile(back) as archive:
                self.assertEqual(archive.read("data.bin"), b"\x01\x02\x03")


class MediaRegistryTests(SimpleTestCase):
    def test_audio_pairs_registered(self):
        self.assertEqual(
            {pair.target for pair in targets_for("wav")},
            {"mp3", "flac", "ogg"},
        )
        self.assertEqual(get_pair("wav", "mp3").category, "audio")
        self.assertTrue(get_pair("wav", "mp3").best_effort)

    def test_video_pairs_registered(self):
        targets = {pair.target for pair in targets_for("mp4")}
        self.assertEqual(targets, {"webm", "mkv", "mp3", "wav"})
        self.assertEqual(get_pair("mp4", "webm").category, "video")
        self.assertIn("(audio)", get_pair("mp4", "mp3").label)


class MediaSniffTests(SimpleTestCase):
    def test_sniff_wav(self):
        with TemporaryDirectory() as tmp:
            path = _write_wav(Path(tmp) / "tone.wav")
            self.assertEqual(sniff_format(path), "wav")


@unittest.skipUnless(find_ffmpeg() is not None, "ffmpeg not installed")
class FfmpegConversionTests(SimpleTestCase):
    def test_wav_to_mp3(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            wav_path = _write_wav(root / "tone.wav")
            mp3_path = root / "tone.mp3"
            result = convert_file(wav_path, "wav", "mp3", mp3_path)
            self.assertTrue(result.exists())
            self.assertGreater(result.stat().st_size, 0)
