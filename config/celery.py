"""Celery application for async conversion workers."""

from __future__ import annotations

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

from celery import Celery

app = Celery("fileforge")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
