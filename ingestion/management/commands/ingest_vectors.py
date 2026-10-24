from django.core.management.base import BaseCommand, CommandError

from ai.vectorstore import VectorUnavailable, sync_procedures, vector_configured
from ingestion.models import IngestionRecord


class Command(BaseCommand):
    help = "Embed procedure sections with Hugging Face and upsert them to Pinecone (idempotent; stable IDs)."

    def add_arguments(self, parser):
        parser.add_argument("--create-index", action="store_true", help="Create the Pinecone index if it doesn't exist.")

    def handle(self, *args, create_index, **options):
        if not vector_configured():
            raise CommandError("Set PINECONE_API_KEY, HF_TOKEN, HF_EMBEDDING_MODEL and EMBEDDING_DIMENSIONS in .env first.")
        try:
            counts = sync_procedures(create_index=create_index)
        except VectorUnavailable as exc:
            raise CommandError(str(exc)) from exc
        IngestionRecord.objects.create(
            kind=IngestionRecord.Kind.VECTOR_INGEST, source_name="procedures → Pinecone", rows_accepted=counts["upserted"])
        self.stdout.write(self.style.SUCCESS(
            f"Upserted {counts['upserted']} procedure sections to Pinecone; removed {counts['removed']} stale vectors."))
