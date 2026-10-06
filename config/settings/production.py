"""Production settings. Fail closed on insecure configuration."""

from .base import *  # noqa: F403
from .base import env

DEBUG = False

SECRET_KEY = env("SECRET_KEY")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# Django 4+ Origin check for HTTPS POSTs. Prefer explicit env; otherwise
# derive https://<host> from ALLOWED_HOSTS (covers Railway custom domains).
_csrf_trusted = env.list("CSRF_TRUSTED_ORIGINS", default=[])
if _csrf_trusted:
    CSRF_TRUSTED_ORIGINS = _csrf_trusted
else:
    CSRF_TRUSTED_ORIGINS = [
        f"https://{host}"
        for host in ALLOWED_HOSTS
        if host and host != "*" and not host.startswith(".")
    ]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=60 * 60 * 24 * 30)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

CONVERSION_SYNC_ENABLED = env.bool("CONVERSION_SYNC_ENABLED", default=False)
