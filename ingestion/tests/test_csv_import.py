from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from django.conf import settings
from django.test import TestCase

from ingestion.csv_adapter import import_csv
from ingestion.models import IngestionRecord
from ingestion.seed import CUSTOMERS
from operations.models import Customer, Shipment

SAMPLE = Path(settings.BASE_DIR) / "ingestion/samples/regional_tms_export.csv"
AS_OF = datetime.fromisoformat("2026-10-21T15:00:00-04:00")


class CsvImportTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        for cid, name in CUSTOMERS:
            Customer.objects.create(customer_id=cid, name=name)

    def test_valid_rows_import_and_invalid_rows_are_reported(self):
        result = import_csv(SAMPLE, "regional_tms_csv", AS_OF)
        self.assertEqual(len(result.accepted), 3)
        self.assertEqual(result.rejected_rows, 4)
        errors = {(e["row"], e["field"]) for e in result.errors}
        self.assertIn((5, "WindowOpen"), errors)  # no timezone offset
        self.assertIn((6, "Market"), errors)  # unknown region
        self.assertIn((7, "StatusCode"), errors)  # unknown status code
        self.assertIn((7, "WindowClose"), errors)  # window closes before it opens
        self.assertIn((8, "Client"), errors)  # unknown customer
        self.assertIn((8, "DeliveredTs"), errors)  # delivered without timestamp
        record = IngestionRecord.objects.get()
        self.assertEqual((record.rows_accepted, record.rows_rejected), (3, 4))

    def test_maps_source_codes_to_canonical_fields(self):
        import_csv(SAMPLE, "regional_tms_csv", AS_OF)
        s = Shipment.objects.get(source_record_id="RT-CKS-50003")
        self.assertEqual((s.shipment_id, s.region, s.status), ("SHP-20003", "jacksonville", "delivered"))
        self.assertIsNone(s.eta)  # blank ETA stays unknown
        self.assertIsNotNone(s.delivery_window_end.tzinfo)

    def test_reimport_is_idempotent(self):
        import_csv(SAMPLE, "regional_tms_csv", AS_OF)
        import_csv(SAMPLE, "regional_tms_csv", AS_OF)
        self.assertEqual(Shipment.objects.filter(source_system="regional_tms_csv").count(), 3)

    def test_dry_run_writes_nothing(self):
        import_csv(SAMPLE, "regional_tms_csv", AS_OF, dry_run=True)
        self.assertFalse(Shipment.objects.exists())
        self.assertFalse(IngestionRecord.objects.exists())

    def test_missing_required_column_rejects_file(self):
        with TemporaryDirectory() as d:
            tmp = Path(d) / "partial.csv"
            tmp.write_text("ShipmentNo,Client\nSHP-1,CUST-HHG\n")
            result = import_csv(tmp, "x", AS_OF, dry_run=True)
        self.assertFalse(result.accepted)
        self.assertIn("OrderRef", {e["field"] for e in result.errors})
