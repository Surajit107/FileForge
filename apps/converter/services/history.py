"""Session-scoped conversion history helpers."""

from __future__ import annotations

from django.conf import settings
from django.core.paginator import EmptyPage, Page, PageNotAnInteger, Paginator
from django.db.models import QuerySet
from django.http import HttpRequest

from apps.converter.models import ConversionJob
from apps.converter.services.access import ensure_session_key


def owned_jobs_queryset(request: HttpRequest) -> QuerySet[ConversionJob]:
    session_key = request.session.session_key
    if not session_key:
        return ConversionJob.objects.none()
    return ConversionJob.objects.filter(owner_session_key=session_key)


def history_page(request: HttpRequest, *, page: int | str | None = 1) -> Page:
    """Paginated history for the current browser session only."""
    # Touch the session so empty browsers still get a stable key for later creates.
    if request.session.session_key is None:
        ensure_session_key(request)

    per_page = max(1, int(getattr(settings, "HISTORY_PAGE_SIZE", 10)))
    paginator = Paginator(owned_jobs_queryset(request), per_page)
    try:
        return paginator.page(page)
    except PageNotAnInteger:
        return paginator.page(1)
    except EmptyPage:
        return paginator.page(paginator.num_pages or 1)
