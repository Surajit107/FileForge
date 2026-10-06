"""Time-limited signed download tokens.

Session ownership remains the access-control gate. The signature binds the
URL to a short TTL so a leaked path alone is not enough after expiry, and
stable UUID URLs without a fresh token stop working.
"""

from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.core import signing
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlencode

from apps.converter.models import ConversionBatch, ConversionJob

_SALT = "fileforge.download.v1"
_MIN_TOKEN_AGE_SEC = 60


def _signer() -> signing.TimestampSigner:
    return signing.TimestampSigner(salt=_SALT)


def _max_age_seconds(expires_at) -> int:
    remaining = int((expires_at - timezone.now()).total_seconds())
    configured = int(getattr(settings, "CONVERSION_DOWNLOAD_TOKEN_MAX_AGE_SEC", 0) or 0)
    if configured > 0:
        remaining = min(remaining, configured)
    return max(_MIN_TOKEN_AGE_SEC, remaining)


def make_download_token(kind: str, object_id: str, *, expires_at) -> str:
    return _signer().sign(f"{kind}:{object_id}")


def verify_download_token(
    token: str,
    *,
    kind: str,
    object_id: str,
    expires_at,
) -> bool:
    if not token:
        return False
    try:
        value = _signer().unsign(token, max_age=_max_age_seconds(expires_at))
    except signing.BadSignature:
        return False
    return value == f"{kind}:{object_id}"


def signed_job_download_url(job: ConversionJob) -> str | None:
    if not job.is_downloadable:
        return None
    token = make_download_token("job", str(job.id), expires_at=job.expires_at)
    base = reverse("converter:download", kwargs={"job_id": job.id})
    return f"{base}?{urlencode({'token': token})}"


def signed_batch_download_url(batch: ConversionBatch) -> str | None:
    if not batch.is_downloadable:
        return None
    token = make_download_token("batch", str(batch.id), expires_at=batch.expires_at)
    base = reverse("converter:batch_download", kwargs={"batch_id": batch.id})
    return f"{base}?{urlencode({'token': token})}"


def download_token_max_age(expires_at) -> timedelta:
    return timedelta(seconds=_max_age_seconds(expires_at))
