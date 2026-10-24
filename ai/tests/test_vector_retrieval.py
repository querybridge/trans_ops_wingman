"""Semantic procedure ranking with Pinecone mocked. No network calls."""

from datetime import datetime
from unittest import mock

from django.test import TestCase, override_settings
from langchain_core.documents import Document

from ai import vectorstore
from ai.evidence import build_shipment_evidence
from ai.schemas import RetrieveProcedureInput
from ai.tools import ToolContext, procedure_query, retrieve_procedure
from ingestion.procedures import ingest_procedures
from ingestion.seed import seed

AS_OF = datetime.fromisoformat("2026-10-21T15:00:00-04:00")
CONFIGURED = dict(PINECONE_API_KEY="test", HF_TOKEN="test", HF_EMBEDDING_MODEL="m", EMBEDDING_DIMENSIONS=384)


def hit(chunk_id, score):
    return (Document(page_content="", metadata={"chunk_id": chunk_id}), score)


class FakeStore:
    def __init__(self, results=None, error=None):
        self.results, self.error, self.calls = results or [], error, []

    def similarity_search_with_score(self, query, k, filter):
        self.calls.append({"query": query, "k": k, "filter": filter})
        if self.error:
            raise self.error
        return self.results


@override_settings(DEMO_AS_OF=AS_OF)
class VectorRetrievalTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed(AS_OF)
        ingest_procedures()

    def retrieve(self, store, customer="CUST-HHG", issue="failed_attempt", query="disputed attempt"):
        with mock.patch("ai.vectorstore.get_store", return_value=store):
            return retrieve_procedure(ToolContext(customer, AS_OF), RetrieveProcedureInput(issue_type=issue, query=query))

    def test_unconfigured_uses_database_order_without_calling_pinecone(self):
        store = FakeStore()
        result = self.retrieve(store)
        self.assertEqual(result["retrieval"], "database")
        self.assertEqual(len(result["sections"]), 5)
        self.assertEqual(store.calls, [])

    @override_settings(**CONFIGURED)
    def test_semantic_ranks_allowed_sections_with_customer_filter(self):
        store = FakeStore([hit("SOP-FA-HHG@v1#disputed-attempts", 0.8), hit("SOP-FA-HHG@v1#ownership", 0.6)])
        result = self.retrieve(store)
        self.assertEqual(result["retrieval"], "semantic")
        self.assertEqual([s["chunk_id"] for s in result["sections"]], ["SOP-FA-HHG@v1#disputed-attempts", "SOP-FA-HHG@v1#ownership"])
        self.assertEqual(store.calls[0]["filter"]["customer_id"], {"$in": ["CUST-HHG", "shared"]})
        self.assertTrue(all(c.startswith("SOP-FA-HHG@v1#") for c in store.calls[0]["filter"]["chunk_id"]["$in"]))

    @override_settings(**CONFIGURED)
    def test_section_outside_allowed_set_is_dropped(self):
        store = FakeStore([hit("SOP-FA-HHG@v1#disputed-attempts", 0.8)])
        result = self.retrieve(store, customer="CUST-SLO", issue="missed_window", query="late")
        self.assertNotIn("SOP-FA-HHG@v1#disputed-attempts", [s["chunk_id"] for s in result["sections"]])
        self.assertEqual(result["retrieval"], "database (vector search unavailable)")

    @override_settings(**CONFIGURED)
    def test_pinecone_failure_falls_back_to_database(self):
        result = self.retrieve(FakeStore(error=RuntimeError("down")))
        self.assertEqual(result["retrieval"], "database (vector search unavailable)")
        self.assertEqual(len(result["sections"]), 5)

    @override_settings(**CONFIGURED)
    def test_no_applicable_procedure_never_queries_pinecone(self):
        store = FakeStore([hit("SOP-FA-HHG@v1#disputed-attempts", 0.9)])
        result = self.retrieve(store, customer="CUST-CKS")
        self.assertEqual((result["match"], result["retrieval"], result["sections"]), ("none", "none", []))
        self.assertEqual(store.calls, [])

    @override_settings(**CONFIGURED)
    def test_evidence_records_semantic_method(self):
        store = FakeStore([hit("SOP-FA-HHG@v1#disputed-attempts", 0.8), hit("SOP-ESC@v1#roles", 0.7)])
        with mock.patch("ai.vectorstore.get_store", return_value=store):
            pkg = build_shipment_evidence(ToolContext("CUST-HHG", AS_OF), "SHP-00031")
        self.assertEqual(pkg.retrieval_label, "semantic (Pinecone)")
        self.assertIn("Delivery attempt failed", store.calls[0]["query"])

    def test_query_text_is_bounded(self):
        self.assertLessEqual(len(procedure_query("missing_scan", ["x" * 5000])), 1000)

    def test_chunk_metadata(self):
        from operations.models import ProcedureChunk

        chunk = ProcedureChunk.objects.get(chunk_id="SOP-FA-HHG@v1#scope")
        meta = vectorstore.chunk_metadata(chunk)
        self.assertEqual((meta["customer_id"], meta["issue_type"], meta["region"]), ("CUST-HHG", "failed_attempt", "all"))
        shared = vectorstore.chunk_metadata(ProcedureChunk.objects.get(chunk_id="SOP-ESC@v1#roles"))
        self.assertEqual(shared["customer_id"], "shared")
