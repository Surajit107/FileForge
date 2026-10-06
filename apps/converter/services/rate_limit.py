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
    entry = cache.get(key)

    if not entry or not isinstance(entry, dict):
        cache.set(key, {"count": 1, "started": now}, timeout=window)
        return

    started = int(entry.get("started", now))
    count = int(entry.get("count", 0))
    elapsed = now - started
    if elapsed >= window:
        cache.set(key, {"count": 1, "started": now}, timeout=window)
        return

    if count >= limit:
        raise RateLimitExceeded(window - elapsed)

    entry["count"] = count + 1
    cache.set(key, entry, timeout=max(1, window - elapsed))
