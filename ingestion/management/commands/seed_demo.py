from django.conf import settings
from django.core.management.base import BaseCommand

from ingestion.seed import DATASET_VERSION, RANDOM_SEED, seed


class Command(BaseCommand):
    help = "Create or replace the deterministic synthetic demo dataset (idempotent)."

    def handle(self, *args, **options):
        as_of = settings.DEMO_AS_OF
        counts = seed(as_of)
        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded dataset {DATASET_VERSION} (seed {RANDOM_SEED}, as of {as_of.isoformat()}): "
                f"{counts['shipments']} shipments, {counts['events']} events, {counts['notes']} dispatch notes."
            )
        )
