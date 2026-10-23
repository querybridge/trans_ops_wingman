from django.db import models


class IngestionRecord(models.Model):
    """One run of an import or ingest command, kept for auditability."""

    class Kind(models.TextChoices):
        SHIPMENT_CSV = "shipment_csv", "Shipment CSV import"
        SEED = "seed", "Synthetic seed"
        VECTOR_INGEST = "vector_ingest", "Vector ingest"

    kind = models.CharField(max_length=24, choices=Kind.choices)
    source_name = models.CharField(max_length=255)
    started_at = models.DateTimeField(auto_now_add=True)
    rows_accepted = models.PositiveIntegerField(default=0)
    rows_rejected = models.PositiveIntegerField(default=0)
    errors = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.get_kind_display()} {self.source_name}"
