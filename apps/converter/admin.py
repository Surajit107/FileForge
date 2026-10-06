from django.contrib import admin

from apps.converter.models import ConversionJob


@admin.register(ConversionJob)
class ConversionJobAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "original_name",
        "source_format",
        "target_format",
        "status",
        "owner_session_key",
        "created_at",
        "expires_at",
    )
    list_filter = ("status", "source_format", "target_format")
    search_fields = ("original_name", "id", "owner_session_key")
    readonly_fields = ("id", "owner_session_key", "created_at", "updated_at", "completed_at")
    ordering = ("-created_at",)
