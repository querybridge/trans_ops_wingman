from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import TestCase

from ingestion.procedures import ProcedureFormatError, ingest_procedures, parse_procedure
from ingestion.seed import CUSTOMERS
from operations.models import Customer, ProcedureChunk, ProcedureDocument
from operations.services import retrieve_procedures

AS_OF = datetime.fromisoformat("2026-10-21T15:00:00-04:00")


class ProcedureIngestTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        for cid, name in CUSTOMERS:
            Customer.objects.create(customer_id=cid, name=name)
        ingest_procedures()

    def test_all_documents_loaded_with_stable_chunk_ids(self):
        self.assertEqual(ProcedureDocument.objects.count(), 6)
        self.assertTrue(ProcedureChunk.objects.filter(chunk_id="SOP-MW@v2#customer-notification").exists())
        before = sorted(ProcedureChunk.objects.values_list("chunk_id", flat=True))
        ingest_procedures()
        self.assertEqual(sorted(ProcedureChunk.objects.values_list("chunk_id", flat=True)), before)

    def test_bad_front_matter_is_rejected(self):
        with TemporaryDirectory() as d:
            bad = Path(d) / "bad.md"
            bad.write_text("---\ndocument_id: X\n---\n## A\ntext\n")
            with self.assertRaises(ProcedureFormatError):
                parse_procedure(bad)


class ProcedureRetrievalTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        for cid, name in CUSTOMERS:
            Customer.objects.create(customer_id=cid, name=name)
        ingest_procedures()

    def ids(self, customer, issue, as_of=AS_OF):
        docs, match = retrieve_procedures(customer, issue, "tampa", as_of)
        return [f"{d.document_id}@{d.version}" for d in docs], match

    def test_customer_specific_procedure_preferred(self):
        self.assertEqual(self.ids("CUST-HHG", "failed_attempt"), (["SOP-FA-HHG@v1"], "customer"))

    def test_no_cross_customer_leakage(self):
        # Coastal Kitchen has no failed-attempt SOP; Harborview's must not be used.
        self.assertEqual(self.ids("CUST-CKS", "failed_attempt"), ([], "none"))
        self.assertEqual(self.ids("CUST-SLO", "failed_attempt"), ([], "none"))

    def test_shared_procedure_applies_when_no_customer_version(self):
        self.assertEqual(self.ids("CUST-CKS", "missing_pod"), (["SOP-POD@v1"], "shared"))

    def test_superseded_version_excluded_on_demo_date(self):
        self.assertEqual(self.ids("CUST-SLO", "missed_window"), (["SOP-MW@v2"], "shared"))

    def test_older_date_selects_older_version(self):
        old = datetime.fromisoformat("2026-06-30T12:00:00-04:00")
        self.assertEqual(self.ids("CUST-SLO", "missed_window", old), (["SOP-MW@v1"], "shared"))
        self.assertEqual(self.ids("CUST-SLO", "missed_window", datetime.fromisoformat("2026-07-01T08:00:00-04:00")), (["SOP-MW@v2"], "shared"))

    def test_not_yet_effective_procedure_excluded(self):
        before = datetime.fromisoformat("2026-02-15T12:00:00-05:00")
        self.assertEqual(self.ids("CUST-HHG", "failed_attempt", before), ([], "none"))
