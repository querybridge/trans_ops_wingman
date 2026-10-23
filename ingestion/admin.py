from django.contrib import admin

from .models import IngestionRecord


@admin.register(IngestionRecord)
class IngestionRecordAdmin(admin.ModelAdmin):
    list_display = ["kind", "source_name", "started_at", "rows_accepted", "rows_rejected"]
    list_filter = ["kind"]
