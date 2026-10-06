"""Persistence for conversion jobs and batches."""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.converter.services.filenames import storage_object_name


def upload_to_input(instance: ConversionJob, filename: str) -> str:
    object_name = storage_object_name(filename, format_hint=instance.source_format)
    return f"{settings.CONVERSION_UPLOAD_SUBDIR}/{instance.id}/{object_name}"


def upload_to_output(instance: ConversionJob, filename: str) -> str:
    object_name = storage_object_name(filename, format_hint=instance.target_format)
    return f"{settings.CONVERSION_OUTPUT_SUBDIR}/{instance.id}/{object_name}"


def upload_to_batch_zip(instance: ConversionBatch, filename: str) -> str:
    object_name = storage_object_name(filename, format_hint="zip")
    return f"{settings.CONVERSION_OUTPUT_SUBDIR}/batches/{instance.id}/{object_name}"


class ConversionBatch(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        DONE = "done", "Done"
        FAILED = "failed", "Failed"
        PARTIAL = "partial", "Partial"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner_session_key = models.CharField(max_length=40, blank=True, db_index=True)
    target_format = models.CharField(max_length=32, db_index=True)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    zip_file = models.FileField(upload_to=upload_to_batch_zip, blank=True)
    error_message = models.TextField(blank=True)
    file_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["status", "expires_at"]),
            models.Index(fields=["owner_session_key", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"Batch {self.id} → {self.target_format} ({self.file_count} files)"

    @property
    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    @property
    def is_downloadable(self) -> bool:
        return (
            self.status in {self.Status.DONE, self.Status.PARTIAL}
            and bool(self.zip_file)
            and not self.is_expired
        )


class ConversionJob(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        DONE = "done", "Done"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Binds the job to the creating browser session. UUID alone is not access control.
    owner_session_key = models.CharField(max_length=40, blank=True, db_index=True)
    batch = models.ForeignKey(
        ConversionBatch,
        null=True,
        blank=True,
        related_name="jobs",
        on_delete=models.CASCADE,
    )
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
