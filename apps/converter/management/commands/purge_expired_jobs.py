"""Delete expired conversion jobs/batches and their files."""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.converter.models import ConversionBatch, ConversionJob


class Command(BaseCommand):
    help = "Purge expired ConversionJob/ConversionBatch rows and associated media files."

    def handle(self, *args, **options):
        now = timezone.now()
        job_qs = ConversionJob.objects.filter(expires_at__lte=now, batch__isnull=True)
        job_count = 0
        for job in job_qs.iterator():
            if job.input_file:
                job.input_file.delete(save=False)
            if job.output_file:
                job.output_file.delete(save=False)
            job.delete()
            job_count += 1

        batch_qs = ConversionBatch.objects.filter(expires_at__lte=now)
        batch_count = 0
        for batch in batch_qs.iterator():
            for job in batch.jobs.all():
                if job.input_file:
                    job.input_file.delete(save=False)
                if job.output_file:
                    job.output_file.delete(save=False)
            if batch.zip_file:
                batch.zip_file.delete(save=False)
            batch.delete()
            batch_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Purged {job_count} expired job(s) and {batch_count} expired batch(es)."
            )
        )
