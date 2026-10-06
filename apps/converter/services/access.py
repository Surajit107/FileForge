"""Session ownership helpers for conversion jobs and batches.

History was previously a client-side list of UUIDs while detail/status/download
were world-readable. Ownership is enforced server-side via the creating session.
"""

from __future__ import annotations

import secrets

from django.http import Http404, HttpRequest
from django.shortcuts import get_object_or_404

from apps.converter.models import ConversionBatch, ConversionJob


def ensure_session_key(request: HttpRequest) -> str:
    """Force a durable session key before binding a job to this browser."""
    if not request.session.session_key:
        request.session.create()
    key = request.session.session_key
    if not key:
        raise RuntimeError("Unable to establish a session for job ownership.")
    return key


def owns_job(request: HttpRequest, job: ConversionJob) -> bool:
    session_key = request.session.session_key
    owner_key = job.owner_session_key
    if not session_key or not owner_key:
        return False
    return secrets.compare_digest(session_key, owner_key)


def owns_batch(request: HttpRequest, batch: ConversionBatch) -> bool:
    session_key = request.session.session_key
    owner_key = batch.owner_session_key
    if not session_key or not owner_key:
        return False
    return secrets.compare_digest(session_key, owner_key)


def get_owned_job_or_404(request: HttpRequest, job_id) -> ConversionJob:
    """Return the job only if the current session owns it.

    Always 404 on failure — do not leak whether a UUID exists.
    """
    job = get_object_or_404(ConversionJob, pk=job_id)
    if not owns_job(request, job):
        raise Http404("Conversion job not found.")
    return job


def get_owned_batch_or_404(request: HttpRequest, batch_id) -> ConversionBatch:
    batch = get_object_or_404(ConversionBatch, pk=batch_id)
    if not owns_batch(request, batch):
        raise Http404("Conversion batch not found.")
    return batch
