"""Local development settings."""

from __future__ import annotations

import os

from .base import *  # noqa: F403

DEBUG = True

ALLOWED_HOSTS = ["*"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Faster local static serving without manifest hashing pain during CSS iteration.
STORAGES["staticfiles"] = {  # noqa: F405
    "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
}

# Local default: sync convert unless Redis worker is running.
# Override with CONVERSION_SYNC_ENABLED=False in .env for true async.
if "CONVERSION_SYNC_ENABLED" not in os.environ:
    CONVERSION_SYNC_ENABLED = True
