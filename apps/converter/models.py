"""Persistence for conversion jobs."""

from __future__ import annotations

import uuid
from pathlib import Path

from django.conf import settings
from django.db import models
from django.utils import timezone


def upload_to_input(instance: ConversionJob, filename: str) -> str:
    safe_name = Path(filename).name
    return f"{settings.CONVERSION_UPLOAD_SUBDIR}/{instance.id}/{safe_name}"


def upload_to_output(instance: ConversionJob, filename: str) -> str:
    safe_name = Path(filename).name
    return f"{settings.CONVERSION_OUTPUT_SUBDIR}/{instance.id}/{safe_name}"


class ConversionJob(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        DONE = "done", "Done"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Binds the job to the creating browser session. UUID alone is not access control.
    owner_session_key = models.CharField(max_length=40, blank=True, db_index=True)
    original_name = models.CharField(max_length=255)
    source_format = models.CharField(max_length=32, db_index=True)
    target_format = models.CharField(max_length=32, db_index=True)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    input_file = models.FileField(upload_to=upload_to_input)
    output_file = models.FileField(upload_to=upload_to_output, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["status", "expires_at"]),
            models.Index(fields=["source_format", "target_format"]),
            models.Index(fields=["owner_session_key", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.original_name} ({self.source_format}→{self.target_format})"

    @property
    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    @property
    def is_downloadable(self) -> bool:
        return (
            self.status == self.Status.DONE
            and bool(self.output_file)
            and not self.is_expired
        )
