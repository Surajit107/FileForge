"""FileForge project configuration package."""

from __future__ import annotations

# Eager Celery app import so `shared_task` binds correctly when workers start.
try:
    from .celery import app as celery_app
except ImportError:  # pragma: no cover - Celery optional until installed
    celery_app = None

__all__ = ("celery_app",)
