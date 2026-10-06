"""Shared Django settings for all environments."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
    CONVERSION_MAX_UPLOAD_MB=(int, 100),
    CONVERSION_JOB_TTL_HOURS=(int, 24),
    CONVERSION_SYNC_ENABLED=(bool, False),
    CONVERSION_MAX_BATCH_FILES=(int, 10),
    CONVERSION_MAX_BATCH_MB=(int, 100),
    CONVERSION_RATE_LIMIT=(int, 20),
    CONVERSION_RATE_WINDOW_SEC=(int, 3600),
    CONVERSION_MAX_PDF_PAGES=(int, 200),
    CONVERSION_MAX_IMAGE_PIXELS=(int, 40_000_000),
    CONVERSION_DOWNLOAD_TOKEN_MAX_AGE_SEC=(int, 0),
    CLAMAV_ENABLED=(bool, False),
    HISTORY_PAGE_SIZE=(int, 10),
    USE_X_FORWARDED_FOR=(bool, False),
)

environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY", default="django-insecure-change-me-in-production")

DEBUG = env("DEBUG")

ALLOWED_HOSTS = env("ALLOWED_HOSTS")

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "whitenoise.runserver_nostatic",
]

LOCAL_APPS = [
    "apps.core",
    "apps.converter",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.site_meta",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
# Ship only built/runtime assets. Tailwind SOURCE lives in static/src/ and must
# NOT be collectstatic'd — WhiteNoise Manifest storage dies on `@import "tailwindcss"`.
STATICFILES_DIRS = [
    ("css", BASE_DIR / "static" / "css"),
    ("js", BASE_DIR / "static" / "js"),
    ("img", BASE_DIR / "static" / "img"),
]
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MEDIA_URL = env("MEDIA_URL", default="")
MEDIA_ROOT = Path(env("MEDIA_ROOT", default=str(BASE_DIR / "media")))

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# FileForge domain settings
# ---------------------------------------------------------------------------
SITE_NAME = env("SITE_NAME", default="FileForge")
CONVERSION_MAX_UPLOAD_BYTES = env("CONVERSION_MAX_UPLOAD_MB") * 1024 * 1024
CONVERSION_JOB_TTL = timedelta(hours=env("CONVERSION_JOB_TTL_HOURS"))
CONVERSION_SYNC_ENABLED = env("CONVERSION_SYNC_ENABLED")
CONVERSION_MAX_BATCH_FILES = env("CONVERSION_MAX_BATCH_FILES")
CONVERSION_MAX_BATCH_BYTES = env("CONVERSION_MAX_BATCH_MB") * 1024 * 1024
CONVERSION_RATE_LIMIT = env("CONVERSION_RATE_LIMIT")
CONVERSION_RATE_WINDOW_SEC = env("CONVERSION_RATE_WINDOW_SEC")
CONVERSION_MAX_PDF_PAGES = env("CONVERSION_MAX_PDF_PAGES")
CONVERSION_MAX_IMAGE_PIXELS = env("CONVERSION_MAX_IMAGE_PIXELS")
# 0 = token lives until job expires_at; otherwise min(job TTL, this cap).
CONVERSION_DOWNLOAD_TOKEN_MAX_AGE_SEC = env("CONVERSION_DOWNLOAD_TOKEN_MAX_AGE_SEC")
CONVERSION_UPLOAD_SUBDIR = "uploads"
CONVERSION_OUTPUT_SUBDIR = "outputs"
HISTORY_PAGE_SIZE = env("HISTORY_PAGE_SIZE")
USE_X_FORWARDED_FOR = env("USE_X_FORWARDED_FOR")

CLAMAV_ENABLED = env("CLAMAV_ENABLED")
CLAMAV_BINARY = env("CLAMAV_BINARY", default="clamscan")
CLAMAV_TIMEOUT_SEC = env.int("CLAMAV_TIMEOUT_SEC", default=30)

FILE_UPLOAD_MAX_MEMORY_SIZE = CONVERSION_MAX_UPLOAD_BYTES
# Allow multipart batches without rejecting the whole request early.
DATA_UPLOAD_MAX_MEMORY_SIZE = max(
    CONVERSION_MAX_UPLOAD_BYTES,
    CONVERSION_MAX_BATCH_BYTES,
)
DATA_UPLOAD_MAX_NUMBER_FILES = CONVERSION_MAX_BATCH_FILES

# Celery / Redis (F2). Sync fallback remains available via CONVERSION_SYNC_ENABLED.
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://127.0.0.1:6379/0")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default=CELERY_BROKER_URL)
CELERY_TASK_TRACK_STARTED = True
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULE = {
    "purge-expired-conversion-jobs": {
        "task": "converter.purge_expired_jobs",
        "schedule": 3600.0,  # hourly
    },
}

# Rate-limit / session cache. Prefer Redis when available (shared across workers).
_CACHE_URL = env("CACHE_URL", default="")
if _CACHE_URL:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": _CACHE_URL,
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "fileforge-local",
        }
    }

# Pillow decompression-bomb ceiling (also enforced at upload time).
try:
    from PIL import Image

    Image.MAX_IMAGE_PIXELS = CONVERSION_MAX_IMAGE_PIXELS
except ImportError:
    pass


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": env("LOG_LEVEL", default="INFO"),
    },
    "loggers": {
        "apps": {"level": "DEBUG" if DEBUG else "INFO", "propagate": True},
        "engines": {"level": "DEBUG" if DEBUG else "INFO", "propagate": True},
        "django.request": {"level": "WARNING", "propagate": True},
    },
}
