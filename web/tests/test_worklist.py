from datetime import datetime
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from ai.testing import ScriptedLLMClient
from ai.tests.test_ai_layer import explanation
from ingestion.procedures import ingest_procedures
from ingestion.seed import seed
from web.models import UserPreference

AS_OF = datetime.fromisoformat("2026-10-21T15:00:00-04:00")


@override_settings(DEMO_AS_OF=AS_OF)
class WorklistTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed(AS_OF)
        ingest_procedures()
        cls.user = get_user_model().objects.create_user("demo", password="demo-pass-123")

    def setUp(self):
        self.client.force_login(self.user)

    def test_login_required(self):
        self.client.logout()
        response = self.client.get(reverse("web:worklist"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('web:worklist')}")

    def test_lists_only_critical_shipments_worst_first(self):
        response = self.client.get(reverse("web:worklist"))
        ids = [item["shipment"].shipment_id for item in response.context["items"]]
        self.assertEqual(ids, ["SHP-00031", "SHP-00007", "SHP-00046"])
        self.assertNotContains(response, "SHP-00052")  # warning only
        self.assertContains(response, "3</strong> deliveries")

    def test_why_and_what_to_do_come_from_records_and_the_customers_procedure(self):
        response = self.client.get(reverse("web:worklist"), {"regions": "tampa", "severities": "critical"})
        self.assertEqual([i["shipment"].shipment_id for i in response.context["items"]], ["SHP-00031", "SHP-00007"])
        self.assertContains(response, "Delivery attempt failed at 11:10 AM")
        self.assertContains(response, "no one knocked")  # customer service note, quoted
        self.assertContains(response, "Disputed attempts.")
        self.assertContains(response, 'href="/shipments/SHP-00031/?customer=#SOP-FA-HHG@v1#disputed-attempts"')
        self.assertContains(response, "Harborview Home Goods only")
        # Missed window uses the current version of the shared procedure, not the superseded one.
        self.assertContains(response, "SOP-MW v2")
        self.assertNotContains(response, "SOP-MW v1")
        self.assertContains(response, "Escalate if not delivered by")

    def test_reference_sections_are_not_steps(self):
        response = self.client.get(reverse("web:worklist"), {"regions": "tampa", "severities": "critical"})
        self.assertNotContains(response, "Applies only to Harborview Home Goods shipments")  # Scope section
        self.assertContains(response, "<strong>Owner:</strong>", count=2)

    def test_missing_procedure_is_reported_not_substituted(self):
        response = self.client.get(reverse("web:worklist"), {"regions": "jacksonville", "severities": "critical"})
        self.assertContains(response, "No failed delivery attempt procedure on file")
        self.assertNotContains(response, "SOP-FA-HHG")
        self.assertContains(response, "SOP-ESC@v1#when-to-escalate")

    def test_empty_scope(self):
        response = self.client.get(reverse("web:worklist"), {"regions": "orlando", "severities": "critical"})
        self.assertContains(response, "No Deliveries Match These Filters")

    def test_htmx_filter_returns_partial(self):
        response = self.client.get(reverse("web:worklist"), {"regions": "tampa", "severities": "critical"}, HTTP_HX_REQUEST="true")
        self.assertNotContains(response, "<html")
        self.assertContains(response, "SHP-00031")

    def test_page_makes_no_ai_call(self):
        with mock.patch("web.views.get_llm_client") as get_client:
            self.client.get(reverse("web:worklist"))
        get_client.assert_not_called()

    def test_recommendation_is_compact_cited_and_escaped(self):
        with mock.patch("web.views.ai_available", return_value=True), \
             mock.patch("web.views.get_llm_client", return_value=ScriptedLLMClient([explanation(summary="<b>x</b> Attempt disputed.")])):
            response = self.client.post(reverse("web:recommend_next_step", args=["SHP-00031"]))
        self.assertContains(response, "Recommended next step")
        self.assertContains(response, "Needs verification")
        self.assertContains(response, "Accounts conflict.")
        self.assertContains(response, 'href="/shipments/SHP-00031/?customer=#NOTE-00031-2"')
        self.assertContains(response, "&lt;b&gt;x&lt;/b&gt;")

    def test_recommendation_without_key_is_honest(self):
        response = self.client.post(reverse("web:recommend_next_step", args=["SHP-00031"]))
        self.assertContains(response, "AI explanation unavailable")

    def test_recommendation_respects_customer_scope(self):
        response = self.client.post(reverse("web:recommend_next_step", args=["SHP-00031"]), {"customer": "CUST-CKS"})
        self.assertEqual(response.status_code, 404)


@override_settings(DEMO_AS_OF=AS_OF)
class WorklistPreferenceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed(AS_OF)
        ingest_procedures()
        cls.user = get_user_model().objects.create_user("demo", password="demo-pass-123")

    def setUp(self):
        self.client.force_login(self.user)

    def ids(self, response):
        return [item["shipment"].shipment_id for item in response.context["items"]]

    def test_settings_saves_defaults_that_the_worklist_opens_with(self):
        response = self.client.post(reverse("web:settings"), {"worklist_regions": ["tampa"], "worklist_severities": ["critical", "warning"]})
        self.assertRedirects(response, reverse("web:settings"))
        pref = UserPreference.objects.get(user=self.user)
        self.assertEqual((pref.worklist_regions, pref.worklist_severities), (["tampa"], ["critical", "warning"]))
        worklist = self.client.get(reverse("web:worklist"))
        self.assertEqual(self.ids(worklist), ["SHP-00031", "SHP-00007", "SHP-00052", "SHP-00078"])
        self.assertContains(worklist, "Showing your default filters")
        self.assertEqual(worklist.context["form"].initial["regions"], ["tampa"])

    def test_settings_requires_an_urgency_level_and_rejects_unknown_values(self):
        none = self.client.post(reverse("web:settings"), {"worklist_regions": ["tampa"]})
        self.assertContains(none, "Choose at least one urgency level.")
        bad = self.client.post(reverse("web:settings"), {"worklist_regions": ["miami"], "worklist_severities": ["critical"]})
        self.assertEqual(bad.status_code, 200)
        self.assertFalse(UserPreference.objects.filter(user=self.user).exists())

    def test_submitted_filters_override_defaults(self):
        UserPreference.objects.create(user=self.user, worklist_regions=["tampa"], worklist_severities=["critical"])
        response = self.client.get(reverse("web:worklist"), {"customer": "", "severities": "warning"})
        self.assertEqual(self.ids(response), ["SHP-00052", "SHP-00023", "SHP-00064", "SHP-00078", "SHP-00089"])
        self.assertContains(response, "Back to my defaults")

    def test_preferences_are_per_user(self):
        other = get_user_model().objects.create_user("other", password="other-pass-123")
        UserPreference.objects.create(user=other, worklist_regions=["orlando"], worklist_severities=["warning"])
        self.assertEqual(self.ids(self.client.get(reverse("web:worklist"))), ["SHP-00031", "SHP-00007", "SHP-00046"])

    def test_warning_cards_are_marked_and_get_their_procedure(self):
        response = self.client.get(reverse("web:worklist"), {"regions": "tampa", "severities": "warning"})
        self.assertContains(response, "work-item--warning")
        self.assertContains(response, "SOP-MS v1")
        self.assertContains(response, "SOP-POD v1")

    def test_worklist_is_home_and_the_post_login_page(self):
        self.assertEqual(reverse("web:worklist"), "/")
        self.assertRedirects(self.client.get("/worklist/?regions=tampa"), "/?regions=tampa")
        self.client.logout()
        response = self.client.post(reverse("login"), {"username": "demo", "password": "demo-pass-123"})
        self.assertRedirects(response, "/")

    def test_nav_order_and_account_menu(self):
        html = self.client.get(reverse("web:worklist")).content.decode()
        self.assertLess(html.index(">Worklist</a>"), html.index(">Exceptions</a>"))
        menu = html[html.index('class="user-menu"'):]
        self.assertIn("demo", menu)
        self.assertIn(">Settings</a>", menu)
        self.assertIn("Sign Out", menu)
