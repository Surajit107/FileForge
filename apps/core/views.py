from __future__ import annotations

from django.http import JsonResponse


def healthcheck(_request):
    """Liveness probe for reverse proxies and container orchestration."""
    return JsonResponse({"status": "ok", "service": "fileforge"})
