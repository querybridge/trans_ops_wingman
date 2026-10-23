from datetime import datetime
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from ai.llm import ProviderTimeout
from ai.testing import ScriptedLLMClient
from ai.tests.test_ai_layer import explanation
from ingestion.procedures import ingest_procedures
from ingestion.seed import seed

AS_OF = datetime.fromisoformat("2026-10-21T15:00:00-04:00")


@override_settings(DEMO_AS_OF=AS_OF)
class AIViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed(AS_OF)
        ingest_procedures()
        cls.user = get_user_model().objects.create_user("demo", password="demo-pass-123")

    def setUp(self):
        self.client.force_login(self.user)

    def post_explain(self, responses):
        with mock.patch("web.views.ai_available", return_value=True), \
             mock.patch("web.views.get_llm_client", return_value=ScriptedLLMClient(responses)):
            return self.client.post(reverse("web:explain_shipment", args=["SHP-00031"]))

    def test_explanation_renders_escaped_with_citations(self):
        response = self.post_explain([explanation(summary="<script>alert(1)</script> Attempt failed.")])
        self.assertContains(response, "AI-generated · for review")
        self.assertContains(response, "&lt;script&gt;alert(1)&lt;/script&gt;")
        self.assertNotContains(response, "<script>alert(1)</script>")
        self.assertContains(response, 'href="#NOTE-00031-2"')
        self.assertContains(response, "Needs verification")

    def test_timeout_shows_retry(self):
        response = self.post_explain([ProviderTimeout()])
        self.assertContains(response, "didn't respond")
        self.assertContains(response, "Retry")

    def test_configured_but_no_adapter_is_honest(self):
        with mock.patch("web.views.ai_available", return_value=True):
            response = self.client.post(reverse("web:explain_shipment", args=["SHP-00031"]))
        self.assertContains(response, "not connected yet")

    def test_detail_shows_procedures_and_gap(self):
        hhg = self.client.get(reverse("web:shipment_detail", args=["SHP-00031"]))
        self.assertContains(hhg, "SOP-FA-HHG v1")
        self.assertContains(hhg, 'id="SOP-FA-HHG@v1#disputed-attempts"')
        cks = self.client.get(reverse("web:shipment_detail", args=["SHP-00046"]))
        self.assertContains(cks, "No failed delivery attempt procedure on file")
        self.assertNotContains(cks, "SOP-FA-HHG")
