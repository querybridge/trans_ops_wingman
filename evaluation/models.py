from django.db import models


class EvaluationRun(models.Model):
    """Recorded results of one run of the versioned evaluation set."""

    run_at = models.DateTimeField(auto_now_add=True)
    dataset_version = models.CharField(max_length=32)
    prompt_version = models.CharField(max_length=32)
    llm_model = models.CharField(max_length=64, blank=True)
    embedding_model = models.CharField(max_length=128, blank=True)
    live_providers = models.BooleanField(
        default=False, help_text="False when the run used offline fixtures instead of live providers."
    )
    cases_total = models.PositiveIntegerField(default=0)
    cases_passed = models.PositiveIntegerField(default=0)
    metrics = models.JSONField(default=dict, blank=True)
    case_results = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["-run_at"]

    def __str__(self):
        return f"Eval {self.dataset_version} @ {self.run_at:%Y-%m-%d %H:%M}"
