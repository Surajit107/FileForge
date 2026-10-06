"""Application service for creating and executing conversion jobs.

Keeps Django views thin (Single Responsibility) and isolates engine I/O.
"""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from django.utils import timezone

from apps.converter.exceptions import InvalidUploadError, JobNotReadyError
from apps.converter.models import ConversionBatch, ConversionJob
from apps.converter.services.filenames import sanitize_display_name, storage_object_name
from apps.converter.services.limits import enforce_content_limits
from apps.converter.services.scan import scan_upload
from engines.exceptions import EngineError, UnsupportedConversionError
from engines.registry import (
    ALLOWED_SOURCE_EXTENSIONS,
    convert_file,
    detect_format_from_filename,
    get_pair,
    supported_upload_message,
)
from engines.sniff import sniff_format

logger = logging.getLogger(__name__)

_OUTPUT_EXTENSIONS: dict[str, str] = {
    "tgz": "tar.gz",
}


def output_filename(original_name: str, target_format: str) -> str:
    """Build a download filename, preserving compound stems like ``archive.tar.gz``."""
    name = sanitize_display_name(original_name)
    lower = name.lower()
    stem = name
    for suffix in (".tar.gz", ".tgz"):
        if lower.endswith(suffix):
            stem = name[: -len(suffix)]
            break
    else:
        stem = Path(name).stem
    extension = _OUTPUT_EXTENSIONS.get(target_format, target_format)
    return sanitize_display_name(f"{stem}.{extension}")


def _extension_allowed(filename: str) -> bool:
    name = Path(filename).name.lower()
    if name.endswith(".tar.gz"):
        return "gz" in ALLOWED_SOURCE_EXTENSIONS or "tgz" in ALLOWED_SOURCE_EXTENSIONS
    suffix = Path(name).suffix.lstrip(".")
    return bool(suffix) and suffix in ALLOWED_SOURCE_EXTENSIONS


def _detect_source_format(uploaded: UploadedFile) -> str:
    if not _extension_allowed(uploaded.name or ""):
        raise InvalidUploadError(supported_upload_message())

    declared = detect_format_from_filename(uploaded.name)
    if not declared:
        raise InvalidUploadError(supported_upload_message())

    # Persist a temp copy for sniffing (UploadedFile may be in-memory).
    suffix = Path(sanitize_display_name(uploaded.name)).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix or ".bin") as tmp:
        for chunk in uploaded.chunks():
            tmp.write(chunk)
        tmp_path = Path(tmp.name)

    try:
        sniffed = sniff_format(tmp_path, declared_filename=uploaded.name)
        if sniffed is None:
            raise InvalidUploadError(
                "File content does not match a supported type."
            )
        if sniffed != declared:
            raise InvalidUploadError(
                f"File extension suggests {declared}, but content looks like {sniffed}."
            )
        enforce_content_limits(tmp_path, sniffed)
        scan_upload(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)
        uploaded.seek(0)

    return sniffed


def create_job(
    uploaded: UploadedFile,
    target_format: str,
    *,
    owner_session_key: str,
    batch: ConversionBatch | None = None,
) -> ConversionJob:
    # Byte cap before sniff / archive member enumeration (zip-bomb DoS).
    if uploaded.size > settings.CONVERSION_MAX_UPLOAD_BYTES:
        max_mb = settings.CONVERSION_MAX_UPLOAD_BYTES // (1024 * 1024)
        raise InvalidUploadError(f"File exceeds the {max_mb} MB upload limit.")

    source_format = _detect_source_format(uploaded)

    try:
        pair = get_pair(source_format, target_format)
    except UnsupportedConversionError as exc:
        raise InvalidUploadError(str(exc)) from exc

    # Per-pair limit (media/archives may allow more) capped by global setting.
    limit_bytes = min(pair.max_bytes, settings.CONVERSION_MAX_UPLOAD_BYTES)
    if uploaded.size > limit_bytes:
        max_mb = limit_bytes // (1024 * 1024)
        raise InvalidUploadError(f"File exceeds the {max_mb} MB upload limit.")

    if not owner_session_key:
        raise InvalidUploadError("Missing session ownership for conversion job.")

    expires_at = (
        batch.expires_at
        if batch is not None
        else timezone.now() + settings.CONVERSION_JOB_TTL
    )

    display_name = sanitize_display_name(uploaded.name or "upload.bin")
    job = ConversionJob(
        owner_session_key=owner_session_key,
        batch=batch,
        original_name=display_name,
        source_format=source_format,
        target_format=target_format,
        status=ConversionJob.Status.PENDING,
        expires_at=expires_at,
    )
    job.input_file.save(
        storage_object_name(display_name, format_hint=source_format),
        uploaded,
        save=False,
    )
    job.save()
    logger.info(
        "conversion_job_created job_id=%s source=%s target=%s batch_id=%s",
        job.id,
        source_format,
        target_format,
        batch.id if batch else "",
    )
    return job


def run_job(job: ConversionJob) -> ConversionJob:
    """Execute a conversion job synchronously and persist the result."""
    job.status = ConversionJob.Status.PROCESSING
    job.error_message = ""
    job.save(update_fields=["status", "error_message", "updated_at"])
    logger.info("conversion_job_processing job_id=%s", job.id)

    source_path = Path(job.input_file.path)
    output_name = output_filename(job.original_name, job.target_format)
    temp_output = (
        Path(settings.MEDIA_ROOT)
        / settings.CONVERSION_OUTPUT_SUBDIR
        / str(job.id)
        / output_name
    )

    try:
        convert_file(
            source_path=source_path,
            source=job.source_format,
            target=job.target_format,
            destination_path=temp_output,
        )
        with temp_output.open("rb") as handle:
            job.output_file.save(output_name, File(handle), save=False)
        job.status = ConversionJob.Status.DONE
        job.completed_at = timezone.now()
        job.save(
            update_fields=[
                "output_file",
                "status",
                "completed_at",
                "updated_at",
            ]
        )
        logger.info("conversion_job_done job_id=%s output=%s", job.id, job.output_file.name)
    except (EngineError, OSError, ValueError) as exc:
        logger.exception("conversion_job_failed job_id=%s", job.id)
        job.status = ConversionJob.Status.FAILED
        job.error_message = str(exc)
        job.completed_at = timezone.now()
        job.save(
            update_fields=[
                "status",
                "error_message",
                "completed_at",
                "updated_at",
            ]
        )

    if job.batch_id:
        from apps.converter.services.batch import maybe_finalize_batch_for_job

        maybe_finalize_batch_for_job(job)

    return job


def enqueue_job(job: ConversionJob) -> ConversionJob:
    """Queue job on Celery, or fall back to sync if the broker is unavailable."""
    from apps.converter.tasks import run_conversion_job

    try:
        run_conversion_job.delay(str(job.id))
        logger.info("conversion_job_enqueued job_id=%s", job.id)
        return job
    except Exception:  # noqa: BLE001 - personal/dev resilience
        logger.warning(
            "conversion_job_enqueue_failed job_id=%s; falling back to sync",
            job.id,
            exc_info=True,
        )
        return run_job(job)


@transaction.atomic
def create_and_run(
    uploaded: UploadedFile,
    target_format: str,
    *,
    owner_session_key: str,
) -> ConversionJob:
    job = create_job(
        uploaded,
        target_format,
        owner_session_key=owner_session_key,
    )
    if settings.CONVERSION_SYNC_ENABLED:
        return run_job(job)
    # Ensure the job row is committed before the worker picks it up.
    transaction.on_commit(lambda: enqueue_job(job))
    return job


def get_downloadable_job(job: ConversionJob) -> ConversionJob:
    if job.is_expired:
        raise JobNotReadyError("This conversion has expired.")

    if job.status == ConversionJob.Status.FAILED:
        raise JobNotReadyError(job.error_message or "Conversion failed.")

    if not job.is_downloadable:
        raise JobNotReadyError("Conversion is not ready for download.")

    return job


def progress_label(status: str) -> str:
    return {
        ConversionJob.Status.PENDING: "Queued",
        ConversionJob.Status.PROCESSING: "Converting",
        ConversionJob.Status.DONE: "Ready",
        ConversionJob.Status.FAILED: "Failed",
    }.get(status, status.title())
