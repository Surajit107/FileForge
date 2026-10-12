from __future__ import annotations

from django.conf import settings


def site_meta(request):
    return {
        "SITE_NAME": settings.SITE_NAME,
        "PRODUCT_ORG_NAME": settings.PRODUCT_ORG_NAME,
        "PRODUCT_MARK": settings.PRODUCT_MARK,
    }
