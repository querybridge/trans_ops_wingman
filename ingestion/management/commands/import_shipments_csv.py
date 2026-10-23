from django.conf import settings
from django.core.management.base import BaseCommand

from ingestion.csv_adapter import import_csv


class Command(BaseCommand):
    help = "Validate a regional TMS CSV export and upsert valid shipments (idempotent by source record)."

    def add_arguments(self, parser):
        parser.add_argument("path")
        parser.add_argument("--source-system", default="regional_tms_csv")
        parser.add_argument("--dry-run", action="store_true", help="Validate only; write nothing.")

    def handle(self, path, source_system, dry_run, **options):
        result = import_csv(path, source_system, imported_at=settings.DEMO_AS_OF, dry_run=dry_run)
        verb = "Would import" if dry_run else "Imported"
        self.stdout.write(f"{verb} {len(result.accepted)} rows; rejected {result.rejected_rows} rows.")
        for e in result.errors:
            self.stdout.write(self.style.WARNING(f"  row {e['row']} {e['field']}: {e['error']}"))
