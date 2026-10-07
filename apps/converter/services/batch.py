"""Batch conversion orchestration + ZIP packaging."""

from __future__ import annotations

import logging
import tempfile
import zipfile
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from django.utils import timezone

from apps.converter.exceptions import InvalidUploadError, JobNotReadyError
from apps.converter.models import ConversionBatch, ConversionJob
from apps.converter.services.conversion import create_job, enqueue_job, run_job
from apps.converter.services.filenames import sanitize_display_name
from engines.archive import pack_archive
from engines.exceptions import ConversionFailedError
from engines.registry import PACKABLE_TARGETS, normalize_format

logger = logging.getLogger(__name__)

_ARCHIVE_EXTENSIONS: dict[str, str] = {
    "zip": "zip",
    "tar": "tar",
    "tgz": "tar.gz",
    "7z": "7z",
}


def create_batch(
    uploads: list[UploadedFile],
    target_format: str,
    *,
    owner_session_key: str,
) -> ConversionBatch:
    if not uploads:
        raise InvalidUploadError("Choose at least one file to convert.")
    if len(uploads) > settings.CONVERSION_MAX_BATCH_FILES:
        raise InvalidUploadError(
            f"Too many files. Maximum batch size is {settings.CONVERSION_MAX_BATCH_FILES}."
        )
    if not owner_session_key:
        raise InvalidUploadError("Missing session ownership for conversion batch.")

    total = sum(upload.size for upload in uploads)
    if total > settings.CONVERSION_MAX_BATCH_BYTES:
        max_mb = settings.CONVERSION_MAX_BATCH_BYTES // (1024 * 1024)
        raise InvalidUploadError(f"Batch exceeds the {max_mb} MB total upload limit.")

    expires_at = timezone.now() + settings.CONVERSION_JOB_TTL
    batch = ConversionBatch.objects.create(
        owner_session_key=owner_session_key,
        target_format=target_format,
        status=ConversionBatch.Status.PENDING,
        file_count=len(uploads),
        expires_at=expires_at,
    )

    try:
        for uploaded in uploads:
            create_job(
                uploaded,
                target_format,
                owner_session_key=owner_session_key,
                batch=batch,
            )
    except Exception:
        batch.delete()
        raise

    logger.info(
        "conversion_batch_created batch_id=%s files=%s target=%s",
        batch.id,
        batch.file_count,
        batch.target_format,
    )
    return batch


def run_batch(batch: ConversionBatch) -> ConversionBatch:
    batch.status = ConversionBatch.Status.PROCESSING
    batch.save(update_fields=["status", "updated_at"])
    for job in batch.jobs.order_by("created_at"):
        run_job(job)
    return finalize_batch(batch)


def enqueue_batch(batch: ConversionBatch) -> ConversionBatch:
    batch.status = ConversionBatch.Status.PROCESSING
    batch.save(update_fields=["status", "updated_at"])
    for job in batch.jobs.order_by("created_at"):
        enqueue_job(job)
    return batch


@transaction.atomic
def create_and_run_batch(
    uploads: list[UploadedFile],
    target_format: str,
    *,
    owner_session_key: str,
) -> ConversionBatch:
    batch = create_batch(
        uploads,
        target_format,
        owner_session_key=owner_session_key,
    )
    if settings.CONVERSION_SYNC_ENABLED:
        return run_batch(batch)
    transaction.on_commit(lambda: enqueue_batch(batch))
    return batch


def _unique_member_path(directory: Path, display_name: str) -> Path:
    """Avoid collisions when two uploads share the same basename."""
    safe = sanitize_display_name(display_name)
    candidate = directory / safe
    if not candidate.exists():
        return candidate

    lower = safe.lower()
    if lower.endswith(".tar.gz"):
        stem, suffix = safe[: -len(".tar.gz")], ".tar.gz"
    else:
        path = Path(safe)
        stem, suffix = path.stem, path.suffix

    index = 2
    while True:
        candidate = directory / f"{stem}-{index}{suffix}"
        if not candidate.exists():
            return candidate
        index += 1


@transaction.atomic
def create_and_run_pack(
    uploads: list[UploadedFile],
    target_format: str,
    *,
    owner_session_key: str,
) -> ConversionBatch:
    """Pack multiple uploads into one archive (ZIP/TAR/TGZ/7Z) without converting."""
    if len(uploads) < 2:
        raise InvalidUploadError("Select at least two files to pack into an archive.")

    target = normalize_format(target_format)
    if target not in PACKABLE_TARGETS:
        raise InvalidUploadError(f"Unsupported pack format: {target_format}.")

    if not owner_session_key:
        raise InvalidUploadError("Missing session ownership for conversion batch.")

    if len(uploads) > settings.CONVERSION_MAX_BATCH_FILES:
        raise InvalidUploadError(
            f"Too many files. Maximum batch size is {settings.CONVERSION_MAX_BATCH_FILES}."
        )

    total = sum(upload.size for upload in uploads)
    if total > settings.CONVERSION_MAX_BATCH_BYTES:
        max_mb = settings.CONVERSION_MAX_BATCH_BYTES // (1024 * 1024)
        raise InvalidUploadError(f"Batch exceeds the {max_mb} MB total upload limit.")

    expires_at = timezone.now() + settings.CONVERSION_JOB_TTL
    batch = ConversionBatch.objects.create(
        owner_session_key=owner_session_key,
        target_format=target,
        status=ConversionBatch.Status.PROCESSING,
        file_count=len(uploads),
        expires_at=expires_at,
    )

    extension = _ARCHIVE_EXTENSIONS[target]
    try:
        with tempfile.TemporaryDirectory(prefix="fileforge-pack-") as tmp:
            root = Path(tmp)
            staging = root / "files"
            staging.mkdir()
            for upload in uploads:
                destination = _unique_member_path(staging, upload.name or "upload.bin")
                with destination.open("wb") as handle:
                    for chunk in upload.chunks():
                        handle.write(chunk)

            archive_path = root / f"fileforge-pack.{extension}"
            pack_archive(staging, archive_path, target)
            with archive_path.open("rb") as handle:
                batch.zip_file.save(
                    f"fileforge-batch-{batch.id}.{extension}",
                    File(handle),
                    save=False,
                )
    except ConversionFailedError as exc:
        batch.status = ConversionBatch.Status.FAILED
        batch.error_message = str(exc)
        batch.completed_at = timezone.now()
        batch.save(
            update_fields=["status", "error_message", "completed_at", "updated_at"]
        )
        raise InvalidUploadError(str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        batch.status = ConversionBatch.Status.FAILED
        batch.error_message = f"Packing failed: {exc}"
        batch.completed_at = timezone.now()
        batch.save(
            update_fields=["status", "error_message", "completed_at", "updated_at"]
        )
        raise InvalidUploadError(f"Packing failed: {exc}") from exc

    batch.status = ConversionBatch.Status.DONE
    batch.error_message = ""
    batch.completed_at = timezone.now()
    batch.save(
        update_fields=[
            "zip_file",
            "status",
            "error_message",
            "completed_at",
            "updated_at",
        ]
    )
    logger.info(
        "conversion_pack_done batch_id=%s files=%s target=%s",
        batch.id,
        batch.file_count,
        batch.target_format,
    )
    return batch


def finalize_batch(batch: ConversionBatch) -> ConversionBatch:
    """Build ZIP when all child jobs are terminal. Safe to call repeatedly."""
    jobs = list(batch.jobs.all())
    if not jobs:
        batch.status = ConversionBatch.Status.FAILED
        batch.error_message = "Batch has no jobs."
        batch.completed_at = timezone.now()
        batch.save(
            update_fields=["status", "error_message", "completed_at", "updated_at"]
        )
        return batch

    pending = {
        ConversionJob.Status.PENDING,
        ConversionJob.Status.PROCESSING,
    }
    if any(job.status in pending for job in jobs):
        return batch

    done = [
        job
        for job in jobs
        if job.status == ConversionJob.Status.DONE and job.output_file
    ]
    failed = [job for job in jobs if job.status == ConversionJob.Status.FAILED]

    if done:
        _write_batch_zip(batch, done)

    if done and not failed:
        batch.status = ConversionBatch.Status.DONE
        batch.error_message = ""
    elif done and failed:
        batch.status = ConversionBatch.Status.PARTIAL
        batch.error_message = f"{len(failed)} of {len(jobs)} file(s) failed."
    else:
        batch.status = ConversionBatch.Status.FAILED
        batch.error_message = failed[0].error_message if failed else "Batch failed."

    batch.completed_at = timezone.now()
    batch.save(
        update_fields=[
            "zip_file",
            "status",
            "error_message",
            "completed_at",
            "updated_at",
        ]
    )
    logger.info(
        "conversion_batch_finalized batch_id=%s status=%s done=%s failed=%s",
        batch.id,
        batch.status,
        len(done),
        len(failed),
    )
    return batch


def maybe_finalize_batch_for_job(job: ConversionJob) -> None:
    if not job.batch_id:
        return
    finalize_batch(job.batch)


def _write_batch_zip(batch: ConversionBatch, jobs: list[ConversionJob]) -> None:
    zip_dir = (
        Path(settings.MEDIA_ROOT)
        / settings.CONVERSION_OUTPUT_SUBDIR
        / "batches"
        / str(batch.id)
    )
    zip_dir.mkdir(parents=True, exist_ok=True)
    zip_path = zip_dir / f"fileforge-batch-{batch.id}.zip"

    used_names: set[str] = set()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for job in jobs:
            stem = Path(job.original_name).stem
            member = f"{stem}.{job.target_format}"
            if member in used_names:
                member = f"{stem}-{job.id}.{job.target_format}"
            used_names.add(member)
            archive.write(job.output_file.path, arcname=member)

    with zip_path.open("rb") as handle:
        batch.zip_file.save(zip_path.name, File(handle), save=False)


def get_downloadable_batch(batch: ConversionBatch) -> ConversionBatch:
    if batch.is_expired:
        raise JobNotReadyError("This conversion batch has expired.")
    if batch.status == ConversionBatch.Status.FAILED:
        raise JobNotReadyError(batch.error_message or "Batch conversion failed.")
    if not batch.is_downloadable:
        raise JobNotReadyError("Batch is not ready for download.")
    return batch


def batch_progress_label(status: str) -> str:
    return {
        ConversionBatch.Status.PENDING: "Queued",
        ConversionBatch.Status.PROCESSING: "Converting",
        ConversionBatch.Status.DONE: "Ready",
        ConversionBatch.Status.PARTIAL: "Partial",
        ConversionBatch.Status.FAILED: "Failed",
    }.get(status, status.title())
