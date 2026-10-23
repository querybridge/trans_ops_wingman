from django.core.management.base import BaseCommand

from ingestion.procedures import ingest_procedures


class Command(BaseCommand):
    help = "Load SOP documents from procedures/ into the database (idempotent; stable chunk IDs)."

    def handle(self, *args, **options):
        counts = ingest_procedures()
        self.stdout.write(self.style.SUCCESS(
            f"Ingested {counts['documents']} procedure documents ({counts['chunks']} chunks); removed {counts['removed']} stale rows."))
