"""Delete expired conversion jobs and their files."""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.converter.models import ConversionJob


class Command(BaseCommand):
    help = "Purge expired ConversionJob rows and associated media files."

    def handle(self, *args, **options):
        qs = ConversionJob.objects.filter(expires_at__lte=timezone.now())
        count = qs.count()
        for job in qs.iterator():
            if job.input_file:
                job.input_file.delete(save=False)
            if job.output_file:
                job.output_file.delete(save=False)
            job.delete()
        self.stdout.write(self.style.SUCCESS(f"Purged {count} expired job(s)."))
