from django.contrib import admin

from apps.converter.models import ConversionBatch, ConversionJob


@admin.register(ConversionBatch)
class ConversionBatchAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "target_format",
        "status",
        "file_count",
        "owner_session_key",
        "created_at",
        "expires_at",
    )
    list_filter = ("status", "target_format")
    search_fields = ("id", "owner_session_key")
    readonly_fields = ("id", "owner_session_key", "created_at", "updated_at", "completed_at")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"


@admin.register(ConversionJob)
class ConversionJobAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "original_name",
        "source_format",
        "target_format",
        "status",
        "batch",
        "owner_session_key",
        "created_at",
        "expires_at",
    )
    list_filter = ("status", "source_format", "target_format")
    search_fields = ("original_name", "id", "owner_session_key")
    readonly_fields = ("id", "owner_session_key", "created_at", "updated_at", "completed_at")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    list_select_related = ("batch",)
