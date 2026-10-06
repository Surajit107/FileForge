"""Archive conversion engines (zip / tar / tgz / 7z)."""

from __future__ import annotations

import shutil
import tarfile
import tempfile
import zipfile
from pathlib import Path

from engines.archive.seven_zip import create_7z, extract_7z
from engines.base import ConversionEngine
from engines.exceptions import ConversionFailedError

ARCHIVE_SOURCES: frozenset[str] = frozenset({"zip", "tar", "tgz", "7z"})
ARCHIVE_TARGETS: frozenset[str] = frozenset({"zip", "tar", "tgz", "7z"})

_TARGET_LABELS: dict[str, str] = {
    "zip": "ZIP",
    "tar": "TAR",
    "tgz": "TAR.GZ",
    "7z": "7Z",
}

# Zip-bomb / zip-slip guards for personal-scale uploads.
_MAX_MEMBERS = 5_000
_MAX_UNCOMPRESSED_BYTES = 500 * 1024 * 1024


def _is_safe_member_name(name: str) -> bool:
    cleaned = name.replace("\\", "/").strip()
    if not cleaned or cleaned.startswith("/") or cleaned.startswith("../"):
        return False
    parts = cleaned.split("/")
    return ".." not in parts and not Path(cleaned).is_absolute()


def _assert_within(root: Path, candidate: Path) -> Path:
    resolved_root = root.resolve()
    resolved = candidate.resolve()
    if not resolved.is_relative_to(resolved_root):
        raise ConversionFailedError("Archive contains an unsafe path (zip slip).")
    return resolved


def _extract_zip(archive_path: Path, destination_dir: Path) -> None:
    try:
        with zipfile.ZipFile(archive_path) as archive:
            infos = archive.infolist()
            if len(infos) > _MAX_MEMBERS:
                raise ConversionFailedError("ZIP has too many members.")
            total = 0
            for info in infos:
                if not _is_safe_member_name(info.filename):
                    raise ConversionFailedError(
                        f"ZIP contains an unsafe path: {info.filename!r}"
                    )
                total += max(info.file_size, 0)
                if total > _MAX_UNCOMPRESSED_BYTES:
                    raise ConversionFailedError("ZIP uncompressed size exceeds limit.")
                target = _assert_within(destination_dir, destination_dir / info.filename)
                if info.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info) as source, target.open("wb") as handle:
                    shutil.copyfileobj(source, handle)
    except ConversionFailedError:
        raise
    except zipfile.BadZipFile as exc:
        raise ConversionFailedError(f"Invalid ZIP archive: {exc}") from exc
    except OSError as exc:
        raise ConversionFailedError(f"Unable to extract ZIP: {exc}") from exc


def _extract_tar(archive_path: Path, destination_dir: Path, *, gzipped: bool) -> None:
    mode = "r:gz" if gzipped else "r:"
    try:
        with tarfile.open(archive_path, mode) as archive:
            members = archive.getmembers()
            if len(members) > _MAX_MEMBERS:
                raise ConversionFailedError("TAR has too many members.")
            total = 0
            for member in members:
                if not _is_safe_member_name(member.name):
                    raise ConversionFailedError(
                        f"TAR contains an unsafe path: {member.name!r}"
                    )
                total += max(member.size, 0)
                if total > _MAX_UNCOMPRESSED_BYTES:
                    raise ConversionFailedError("TAR uncompressed size exceeds limit.")
                target = _assert_within(destination_dir, destination_dir / member.name)
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                if not member.isfile():
                    # Skip links/devices — personal converter only packs regular files.
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                extracted = archive.extractfile(member)
                if extracted is None:
                    continue
                with extracted, target.open("wb") as handle:
                    shutil.copyfileobj(extracted, handle)
    except ConversionFailedError:
        raise
    except tarfile.TarError as exc:
        raise ConversionFailedError(f"Invalid TAR archive: {exc}") from exc
    except OSError as exc:
        raise ConversionFailedError(f"Unable to extract TAR: {exc}") from exc


def extract_archive(archive_path: Path, destination_dir: Path, fmt: str) -> None:
    destination_dir.mkdir(parents=True, exist_ok=True)
    if fmt == "zip":
        _extract_zip(archive_path, destination_dir)
    elif fmt == "tar":
        _extract_tar(archive_path, destination_dir, gzipped=False)
    elif fmt == "tgz":
        _extract_tar(archive_path, destination_dir, gzipped=True)
    elif fmt == "7z":
        extract_7z(archive_path, destination_dir)
        # Re-check extracted tree for zip-slip style escapes (7z may create links).
        for path in destination_dir.rglob("*"):
            _assert_within(destination_dir, path)
    else:
        raise ConversionFailedError(f"Unsupported archive format: {fmt}")


def _iter_files(root: Path) -> list[Path]:
    files = [path for path in root.rglob("*") if path.is_file()]
    if not files:
        raise ConversionFailedError("Archive is empty — nothing to convert.")
    return files


def _pack_zip(source_dir: Path, archive_path: Path) -> Path:
    files = _iter_files(source_dir)
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in files:
                arcname = path.relative_to(source_dir).as_posix()
                archive.write(path, arcname=arcname)
    except OSError as exc:
        raise ConversionFailedError(f"Unable to write ZIP: {exc}") from exc
    return archive_path


def _pack_tar(source_dir: Path, archive_path: Path, *, gzipped: bool) -> Path:
    files = _iter_files(source_dir)
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    mode = "w:gz" if gzipped else "w"
    try:
        with tarfile.open(archive_path, mode) as archive:
            for path in files:
                arcname = path.relative_to(source_dir).as_posix()
                archive.add(path, arcname=arcname)
    except (OSError, tarfile.TarError) as exc:
        raise ConversionFailedError(f"Unable to write TAR: {exc}") from exc
    return archive_path


def pack_archive(source_dir: Path, archive_path: Path, fmt: str) -> Path:
    if fmt == "zip":
        return _pack_zip(source_dir, archive_path)
    if fmt == "tar":
        return _pack_tar(source_dir, archive_path, gzipped=False)
    if fmt == "tgz":
        return _pack_tar(source_dir, archive_path, gzipped=True)
    if fmt == "7z":
        _iter_files(source_dir)  # fail fast on empty
        return create_7z(source_dir, archive_path)
    raise ConversionFailedError(f"Unsupported archive format: {fmt}")


def convert_archive(source_path: Path, destination_path: Path, source: str, target: str) -> Path:
    source = source.lower()
    target = target.lower()
    if source not in ARCHIVE_SOURCES or target not in ARCHIVE_TARGETS:
        raise ConversionFailedError(f"Unsupported archive pair: {source} → {target}")
    if source == target:
        raise ConversionFailedError("Identity archive conversions are not registered.")

    with tempfile.TemporaryDirectory(prefix="fileforge-archive-") as tmp:
        root = Path(tmp)
        extracted = root / "extracted"
        extracted.mkdir()
        extract_archive(source_path, extracted, source)
        return pack_archive(extracted, destination_path, target)


class ArchiveConversionEngine:
    """Parameterized engine for one archive source → target pair."""

    def __init__(self, source_format: str, target_format: str) -> None:
        self.source_format = source_format
        self.target_format = target_format

    def convert(self, source_path: Path, destination_path: Path) -> Path:
        try:
            return convert_archive(
                source_path,
                destination_path,
                self.source_format,
                self.target_format,
            )
        except ConversionFailedError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise ConversionFailedError(
                f"{self.source_format.upper()}→{self.target_format.upper()} failed: {exc}"
            ) from exc


def build_archive_engines() -> list[tuple[str, str, str, ConversionEngine]]:
    """Return (source, target, label, engine) for every non-identity archive pair."""
    entries: list[tuple[str, str, str, ConversionEngine]] = []
    for source in sorted(ARCHIVE_SOURCES):
        for target in sorted(ARCHIVE_TARGETS):
            if source == target:
                continue
            entries.append(
                (
                    source,
                    target,
                    _TARGET_LABELS[target],
                    ArchiveConversionEngine(source, target),
                )
            )
    return entries
