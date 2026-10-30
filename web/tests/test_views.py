from datetime import datetime, timedelta, timezone

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from operations.models import Customer, Region, Shipment

EDT = timezone(timedelta(hours=-4))
NO_PROVIDERS = {"PINECONE_API_KEY": "", "HF_TOKEN": "", "ANTHROPIC_API_KEY": "", "LLM_MODEL": ""}


def make_shipment(customer, shipment_id):
    start = datetime(2026, 10, 21, 9, 0, tzinfo=EDT)
    return Shipment.objects.create(
        shipment_id=shipment_id,
        customer=customer,
        region=Region.TAMPA,
        service_type="standard",
        delivery_window_start=start,
        delivery_window_end=start + timedelta(hours=4),
        status=Shipment.Status.OUT_FOR_DELIVERY,
        source_system="csv",
        source_record_id=shipment_id,
        imported_at=start - timedelta(days=1),
    )


@override_settings(**NO_PROVIDERS)
class ViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user("demo", password="demo-pass-123")
        cls.acme = Customer.objects.create(customer_id="ACME", name="Acme Home Goods")
        cls.other = Customer.objects.create(customer_id="BOLT", name="Bolt Outfitters")
        cls.shipment = make_shipment(cls.acme, "SHP-00001")

    def setUp(self):
        self.client.force_login(self.user)

    def test_login_required(self):
        self.client.logout()
        response = self.client.get(reverse("web:dashboard"))
        self.assertRedirects(response, f"{reverse('login')}?next=/exceptions/")

    def test_dashboard_renders_brand_shell_and_rule_flags(self):
        response = self.client.get(reverse("web:dashboard"))
        self.assertContains(response, "Transportation Operations Wingman")
        self.assertContains(response, "Prototype - Synthetic data - For Demo Only")
        # The fixture shipment's window ended at 13:00 with no scans, so both rules flag it.
        self.assertContains(response, "Missed window")
        self.assertContains(response, "Threshold:")

    def test_empty_scope_shows_no_exceptions_state(self):
        response = self.client.get(reverse("web:dashboard"), {"customer": "BOLT"})
        self.assertContains(response, "No Exceptions in This Scope")

    def test_shipment_detail_lists_flags_with_evidence(self):
        response = self.client.get(reverse("web:shipment_detail", args=["SHP-00001"]))
        self.assertContains(response, "Exception Flags")
        self.assertContains(response, "Missed window")

    def test_documentation_link_is_in_footer_not_header(self):
        html = self.client.get(reverse("web:dashboard")).content.decode()
        header, footer = html.split("</header>")[0], html.split('<footer class="footer">')[1]
        self.assertNotIn("Demo Documentation", header)
        self.assertIn('class="doc-link"', footer)
        self.assertIn(reverse("web:documentation"), footer)

    def test_htmx_filter_returns_partial(self):
        response = self.client.get(reverse("web:dashboard"), {"customer": "ACME"}, HTTP_HX_REQUEST="true")
        self.assertNotContains(response, "<html")
        self.assertContains(response, "Shipments")

    def test_shipment_detail_respects_customer_scope(self):
        url = reverse("web:shipment_detail", args=["SHP-00001"])
        self.assertEqual(self.client.get(url, {"customer": "ACME"}).status_code, 200)
        self.assertEqual(self.client.get(url, {"customer": "BOLT"}).status_code, 404)

    def test_missing_eta_is_shown_as_unknown(self):
        response = self.client.get(reverse("web:shipment_detail", args=["SHP-00001"]))
        self.assertContains(response, "Unavailable from source")

    def test_explain_requires_post_and_reports_unconfigured(self):
        url = reverse("web:explain_shipment", args=["SHP-00001"])
        self.assertEqual(self.client.get(url).status_code, 405)
        response = self.client.post(url, {"customer": "ACME"})
        self.assertContains(response, "AI explanation unavailable")

    @override_settings(AI_RATE_LIMIT=2)
    def test_briefing_is_rate_limited(self):
        url = reverse("web:generate_briefing")
        codes = [self.client.post(url).status_code for _ in range(3)]
        self.assertEqual(codes, [200, 200, 429])

    def test_documentation_shows_promise_workflow_and_provider_status(self):
        response = self.client.get(reverse("web:documentation"))
        self.assertContains(response, "See which deliveries need attention")
        self.assertContains(response, "Find Exceptions")
        self.assertContains(response, "Explain a Shipment")
        self.assertContains(response, "Create a Manager Briefing")
        self.assertContains(response, "How Shipments Are Flagged")
        self.assertContains(response, "Not configured")
        self.assertContains(response, "No Evaluation Runs Yet")
