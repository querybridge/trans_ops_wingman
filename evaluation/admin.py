from django.contrib import admin

from .models import EvaluationRun


@admin.register(EvaluationRun)
class EvaluationRunAdmin(admin.ModelAdmin):
    list_display = ["run_at", "dataset_version", "prompt_version", "llm_model", "live_providers", "cases_passed", "cases_total"]
    list_filter = ["live_providers", "dataset_version"]
