"""Simple cache-backed IP rate limiting for conversion POSTs."""

from __future__ import annotations

import time

from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest


class RateLimitExceeded(Exception):
    def __init__(self, retry_after: int) -> None:
        self.retry_after = max(1, int(retry_after))
        super().__init__(
            f"Too many conversions. Try again in {self.retry_after} seconds."
        )


def client_ip(request: HttpRequest) -> str:
    """Resolve client IP.

    Only honor ``X-Forwarded-For`` when the deployment explicitly trusts a
    reverse proxy (``USE_X_FORWARDED_FOR``). Otherwise REMOTE_ADDR alone —
    spoofable headers must not bypass rate limits on a direct expose.
    """
    if getattr(settings, "USE_X_FORWARDED_FOR", False):
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
        if forwarded:
            return forwarded.split(",")[0].strip() or "unknown"
    return request.META.get("REMOTE_ADDR") or "unknown"


def check_conversion_rate_limit(request: HttpRequest) -> None:
    """Increment the convert counter for this IP; raise if over limit."""
    limit = int(getattr(settings, "CONVERSION_RATE_LIMIT", 20))
    window = int(getattr(settings, "CONVERSION_RATE_WINDOW_SEC", 3600))
    if limit <= 0:
        return

    ip = client_ip(request)
    key = f"ff:convert-rate:{ip}"
    now = int(time.time())

    # Atomic-ish increment via cache.add + incr when backend supports it.
    added = cache.add(key, 1, timeout=window)
    if added:
        return

    try:
        count = cache.incr(key)
    except ValueError:
        # Key expired between add and incr, or backend without incr semantics.
        cache.set(key, 1, timeout=window)
        return

    if count > limit:
        # Approximate retry-after: full window (we don't store started_at with incr).
        ttl = cache.ttl(key) if hasattr(cache, "ttl") else None
        retry_after = int(ttl) if isinstance(ttl, int) and ttl > 0 else window
        raise RateLimitExceeded(retry_after)
