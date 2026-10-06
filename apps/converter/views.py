"""HTTP adapters for conversion — thin views, fat services."""

from __future__ import annotations

import logging
from pathlib import Path

from django.contrib import messages
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods

from apps.converter.exceptions import ConversionServiceError
from apps.converter.forms import ConversionForm
from apps.converter.models import ConversionJob
from apps.converter.services.access import ensure_session_key, get_owned_job_or_404
from apps.converter.services.conversion import (
    create_and_run,
    get_downloadable_job,
    progress_label,
)
from apps.converter.services.history import history_page
from engines.registry import detect_format_from_filename, list_pairs, targets_for

logger = logging.getLogger(__name__)


def _wants_json(request) -> bool:
    accept = request.headers.get("Accept", "")
    return (
        "application/json" in accept
        or request.headers.get("X-Requested-With") == "XMLHttpRequest"
    )


def serialize_job(job: ConversionJob) -> dict:
    return {
        "id": str(job.id),
        "status": job.status,
        "progress": progress_label(job.status),
        "error_message": job.error_message,
        "is_downloadable": job.is_downloadable,
        "source_format": job.source_format,
        "target_format": job.target_format,
        "original_name": job.original_name,
        "expires_at": timezone.localtime(job.expires_at).strftime("%Y-%m-%d %H:%M"),
        "status_url": reverse("converter:job_status", kwargs={"job_id": job.id}),
        "detail_url": reverse("converter:job_detail", kwargs={"job_id": job.id}),
        "download_url": (
            reverse("converter:download", kwargs={"job_id": job.id})
            if job.is_downloadable
            else None
        ),
    }


@require_http_methods(["GET", "POST"])
def convert_home(request):
    form = ConversionForm(request.POST or None, request.FILES or None)
    wants_json = _wants_json(request)

    if request.method == "POST" and form.is_valid():
        try:
            owner_session_key = ensure_session_key(request)
            job = create_and_run(
                uploaded=form.cleaned_data["source_file"],
                target_format=form.cleaned_data["target_format"],
                owner_session_key=owner_session_key,
            )
        except ConversionServiceError as exc:
            if wants_json:
                return JsonResponse({"ok": False, "message": str(exc)}, status=400)
            messages.error(request, str(exc))
        else:
            if wants_json:
                return JsonResponse({"ok": True, "job": serialize_job(job)})

            if job.status == ConversionJob.Status.DONE:
                messages.success(request, "Conversion complete. Download below.")
            elif job.status == ConversionJob.Status.FAILED:
                messages.error(request, job.error_message or "Conversion failed.")
            else:
                messages.info(request, "Conversion queued.")
            return redirect("converter:job_detail", job_id=job.id)

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
        },
    )


@require_GET
def job_status(request, job_id):
    job = get_owned_job_or_404(request, job_id)
    return JsonResponse(serialize_job(job))


@require_GET
def download_result(request, job_id):
    job = get_owned_job_or_404(request, job_id)
    try:
        job = get_downloadable_job(job)
    except ConversionServiceError as exc:
        raise Http404(str(exc)) from exc

    filename = f"{Path(job.original_name).stem}.{job.target_format}"
    return FileResponse(
        job.output_file.open("rb"),
        as_attachment=True,
        filename=filename,
    )


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
