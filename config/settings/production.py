"""Production settings. Fail closed on insecure configuration."""

from __future__ import annotations

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403
from .base import env

DEBUG = False

SECRET_KEY = env("SECRET_KEY")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")


def _csrf_origins(*groups: list[str]) -> list[str]:
    """Normalize bare hosts / origins into a deduped CSRF_TRUSTED_ORIGINS list."""
    origins: list[str] = []
    for group in groups:
        for raw in group:
            value = (raw or "").strip().rstrip("/")
            if not value or value == "*":
                continue
            if value.startswith("."):
                continue
            if "://" not in value:
                # Local-only hosts stay on http; everything else is https.
                scheme = (
                    "http"
                    if value in {"localhost", "127.0.0.1", "web"}
                    or value.startswith("localhost:")
                    or value.startswith("127.0.0.1:")
                    else "https"
                )
                value = f"{scheme}://{value}"
            origins.append(value)
    return list(dict.fromkeys(origins))


# Django 4+ Origin check for HTTPS POSTs.
# Merge explicit env + origins derived from ALLOWED_HOSTS so a custom domain
# still works when CSRF_TRUSTED_ORIGINS was forgotten or ALLOWED_HOSTS is "*".
_csrf_explicit = env.list("CSRF_TRUSTED_ORIGINS", default=[])
_csrf_from_hosts = [
    host
    for host in ALLOWED_HOSTS
    if host and host != "*" and not host.startswith(".")
]
# Local docker / runserver against production settings.
_csrf_local_ports: list[str] = []
if any(host in {"localhost", "127.0.0.1"} for host in ALLOWED_HOSTS):
    _csrf_local_ports = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

CSRF_TRUSTED_ORIGINS = _csrf_origins(
    _csrf_explicit,
    _csrf_from_hosts,
    _csrf_local_ports,
)

if not CSRF_TRUSTED_ORIGINS:
    raise ImproperlyConfigured(
        "CSRF_TRUSTED_ORIGINS is empty. Set CSRF_TRUSTED_ORIGINS="
        "https://your.domain (recommended) and/or put that host in ALLOWED_HOSTS."
    )

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
# Must stay False so JS can send the token; form field still works either way,
# but HttpOnly has bitten AJAX CSRF setups and is not required here.
CSRF_COOKIE_HTTPONLY = False
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=60 * 60 * 24 * 30)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"
SESSION_COOKIE_HTTPONLY = True

CONVERSION_SYNC_ENABLED = env.bool("CONVERSION_SYNC_ENABLED", default=False)
