from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

from evaluation.models import EvaluationRun
from ingestion.models import IngestionRecord
from operations.models import Customer, Shipment


class Command(BaseCommand):
    help = "Delete all operational data, ingestion records, and evaluation runs, then reseed. Users are kept."

    def add_arguments(self, parser):
        parser.add_argument("--yes", action="store_true", help="Skip the confirmation prompt.")

    def handle(self, *args, **options):
        if not options["yes"] and input("This deletes all shipments and evaluation runs. Continue? [y/N] ").lower() != "y":
            self.stdout.write("Cancelled.")
            return
        with transaction.atomic():
            Shipment.objects.all().delete()
            Customer.objects.all().delete()
            IngestionRecord.objects.all().delete()
            EvaluationRun.objects.all().delete()
        call_command("seed_demo", stdout=self.stdout)
