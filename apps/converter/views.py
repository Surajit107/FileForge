"""HTTP adapters for conversion — thin views, fat services."""

from __future__ import annotations

import logging

from django.conf import settings
from django.contrib import messages
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods

from apps.converter.exceptions import ConversionServiceError
from apps.converter.forms import ConversionForm
from apps.converter.models import ConversionBatch, ConversionJob
from apps.converter.services.access import (
    ensure_session_key,
    get_owned_batch_or_404,
    get_owned_job_or_404,
)
from apps.converter.services.batch import (
    batch_progress_label,
    create_and_run_batch,
    get_downloadable_batch,
)
from apps.converter.services.conversion import (
    create_and_run,
    get_downloadable_job,
    output_filename,
    progress_label,
)
from apps.converter.services.downloads import (
    signed_batch_download_url,
    signed_job_download_url,
    verify_download_token,
)
from apps.converter.services.history import history_page
from apps.converter.services.rate_limit import RateLimitExceeded, check_conversion_rate_limit
from engines.registry import detect_format_from_filename, list_pairs, targets_for

logger = logging.getLogger(__name__)


def _wants_json(request) -> bool:
    accept = request.headers.get("Accept", "")
    return (
        "application/json" in accept
        or request.headers.get("X-Requested-With") == "XMLHttpRequest"
    )


def _require_download_token(request, *, kind: str, object_id, expires_at) -> None:
    token = request.GET.get("token", "")
    if not verify_download_token(
        token,
        kind=kind,
        object_id=str(object_id),
        expires_at=expires_at,
    ):
        raise Http404("Download link is invalid or expired.")


def serialize_job(job: ConversionJob) -> dict:
    return {
        "kind": "job",
        "id": str(job.id),
        "status": job.status,
        "progress": progress_label(job.status),
        "error_message": job.error_message,
        "is_downloadable": job.is_downloadable,
        "source_format": job.source_format,
        "target_format": job.target_format,
        "original_name": job.original_name,
        "file_count": 1,
        "expires_at": timezone.localtime(job.expires_at).strftime("%Y-%m-%d %H:%M"),
        "status_url": reverse("converter:job_status", kwargs={"job_id": job.id}),
        "detail_url": reverse("converter:job_detail", kwargs={"job_id": job.id}),
        "download_url": signed_job_download_url(job),
    }


def serialize_batch(batch: ConversionBatch) -> dict:
    jobs = list(batch.jobs.order_by("created_at"))
    done = sum(1 for job in jobs if job.status == ConversionJob.Status.DONE)
    failed = sum(1 for job in jobs if job.status == ConversionJob.Status.FAILED)
    source = jobs[0].source_format if jobs else ""
    return {
        "kind": "batch",
        "id": str(batch.id),
        "status": batch.status,
        "progress": batch_progress_label(batch.status),
        "error_message": batch.error_message,
        "is_downloadable": batch.is_downloadable,
        "source_format": source,
        "target_format": batch.target_format,
        "original_name": f"{batch.file_count} files",
        "file_count": batch.file_count,
        "done_count": done,
        "failed_count": failed,
        "expires_at": timezone.localtime(batch.expires_at).strftime("%Y-%m-%d %H:%M"),
        "status_url": reverse("converter:batch_status", kwargs={"batch_id": batch.id}),
        "detail_url": reverse("converter:batch_detail", kwargs={"batch_id": batch.id}),
        "download_url": signed_batch_download_url(batch),
    }


def _rate_limit_response(request, exc: RateLimitExceeded):
    message = str(exc)
    if _wants_json(request):
        response = JsonResponse({"ok": False, "message": message}, status=429)
    else:
        messages.error(request, message)
        response = redirect("converter:home")
    response["Retry-After"] = str(exc.retry_after)
    return response


@require_http_methods(["GET", "POST"])
def convert_home(request):
    form = ConversionForm(request.POST or None, request.FILES or None)
    wants_json = _wants_json(request)

    if request.method == "POST" and form.is_valid():
        try:
            check_conversion_rate_limit(request)
            owner_session_key = ensure_session_key(request)
            uploads = form.cleaned_data["source_files"]
            target_format = form.cleaned_data["target_format"]

            if len(uploads) == 1:
                job = create_and_run(
                    uploaded=uploads[0],
                    target_format=target_format,
                    owner_session_key=owner_session_key,
                )
                payload = serialize_job(job)
                result_status = job.status
                detail_name = "converter:job_detail"
                detail_kw = {"job_id": job.id}
            else:
                batch = create_and_run_batch(
                    uploads=uploads,
                    target_format=target_format,
                    owner_session_key=owner_session_key,
                )
                payload = serialize_batch(batch)
                result_status = batch.status
                detail_name = "converter:batch_detail"
                detail_kw = {"batch_id": batch.id}
        except RateLimitExceeded as exc:
            return _rate_limit_response(request, exc)
        except ConversionServiceError as exc:
            if wants_json:
                return JsonResponse({"ok": False, "message": str(exc)}, status=400)
            messages.error(request, str(exc))
        else:
            if wants_json:
                return JsonResponse({"ok": True, "job": payload, "result": payload})

            if result_status in {
                ConversionJob.Status.DONE,
                ConversionBatch.Status.DONE,
                ConversionBatch.Status.PARTIAL,
            }:
                messages.success(request, "Conversion complete. Download below.")
            elif result_status in {
                ConversionJob.Status.FAILED,
                ConversionBatch.Status.FAILED,
            }:
                messages.error(
                    request,
                    payload.get("error_message") or "Conversion failed.",
                )
            else:
                messages.info(request, "Conversion queued.")
            return redirect(detail_name, **detail_kw)

    if request.method == "POST" and wants_json:
        return JsonResponse(
            {
                "ok": False,
                "message": "Check the form and try again.",
                "errors": form.errors.get_json_data(),
            },
            status=400,
        )

    return render(
        request,
        "converter/convert.html",
        {
            "form": form,
            "pairs": list_pairs(),
            "upload_max_mb": settings.CONVERSION_MAX_UPLOAD_BYTES // (1024 * 1024),
            "batch_max_files": settings.CONVERSION_MAX_BATCH_FILES,
            "job_ttl_hours": max(
                1, int(settings.CONVERSION_JOB_TTL.total_seconds() // 3600)
            ),
        },
    )


@require_GET
def job_detail(request, job_id):
    job = get_owned_job_or_404(request, job_id)
    return render(
        request,
        "converter/job_detail.html",
        {
            "job": job,
            "progress": progress_label(job.status),
            "download_url": signed_job_download_url(job),
        },
    )


@require_GET
def job_status(request, job_id):
    job = get_owned_job_or_404(request, job_id)
    return JsonResponse(serialize_job(job))


@require_GET
def download_result(request, job_id):
    job = get_owned_job_or_404(request, job_id)
    _require_download_token(
        request,
        kind="job",
        object_id=job.id,
        expires_at=job.expires_at,
    )
    try:
        job = get_downloadable_job(job)
    except ConversionServiceError as exc:
        raise Http404(str(exc)) from exc

    filename = output_filename(job.original_name, job.target_format)
    response = FileResponse(
        job.output_file.open("rb"),
        as_attachment=True,
        filename=filename,
        content_type="application/octet-stream",
    )
    response["X-Content-Type-Options"] = "nosniff"
    return response


@require_GET
def batch_detail(request, batch_id):
    batch = get_owned_batch_or_404(request, batch_id)
    return render(
        request,
        "converter/batch_detail.html",
        {
            "batch": batch,
            "jobs": batch.jobs.order_by("created_at"),
            "progress": batch_progress_label(batch.status),
            "download_url": signed_batch_download_url(batch),
        },
    )


@require_GET
def batch_status(request, batch_id):
    batch = get_owned_batch_or_404(request, batch_id)
    return JsonResponse(serialize_batch(batch))


@require_GET
def batch_download(request, batch_id):
    batch = get_owned_batch_or_404(request, batch_id)
    _require_download_token(
        request,
        kind="batch",
        object_id=batch.id,
        expires_at=batch.expires_at,
    )
    try:
        batch = get_downloadable_batch(batch)
    except ConversionServiceError as exc:
        raise Http404(str(exc)) from exc

    filename = f"fileforge-batch-{batch.id}.zip"
    response = FileResponse(
        batch.zip_file.open("rb"),
        as_attachment=True,
        filename=filename,
        content_type="application/octet-stream",
    )
    response["X-Content-Type-Options"] = "nosniff"
    return response


@require_GET
def history(request):
    page_obj = history_page(request, page=request.GET.get("page", 1))
    return render(
        request,
        "converter/history.html",
        {
            "page_obj": page_obj,
            "jobs": page_obj.object_list,
        },
    )


@require_GET
def formats_api(request):
    """Return available target formats for a source type or filename."""
    source = request.GET.get("source", "")
    if not source and request.GET.get("filename"):
        source = detect_format_from_filename(request.GET["filename"]) or ""

    pairs = targets_for(source) if source else []
    return JsonResponse(
        {
            "source": source,
            "targets": [
                {
                    "format": pair.target,
                    "label": pair.label,
                    "best_effort": pair.best_effort,
                    "category": pair.category,
                }
                for pair in pairs
            ],
        }
    )
