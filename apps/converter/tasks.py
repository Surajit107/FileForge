"""Celery tasks for conversion jobs and retention cleanup."""

from __future__ import annotations

import logging

from celery import shared_task
from django.core.management import call_command

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="converter.run_conversion_job", max_retries=1)
def run_conversion_job(self, job_id: str) -> str:
    from apps.converter.models import ConversionJob
    from apps.converter.services.conversion import run_job

    try:
        job = ConversionJob.objects.get(pk=job_id)
    except ConversionJob.DoesNotExist:
        logger.error("conversion_job_missing job_id=%s", job_id)
        return "missing"

    run_job(job)
    logger.info(
        "conversion_job_finished job_id=%s status=%s",
        job_id,
        job.status,
    )
    return job.status


@shared_task(name="converter.purge_expired_jobs")
def purge_expired_jobs() -> str:
    call_command("purge_expired_jobs")
    return "purged"
