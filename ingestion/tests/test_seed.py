import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.test import TestCase

from ingestion.seed import seed
from operations.models import DispatchNote, Shipment, ShipmentEvent
from operations.services import list_exceptions

MANIFEST = json.loads((Path(settings.BASE_DIR) / "evaluation/fixtures/ground_truth_v1.json").read_text())
AS_OF = datetime.fromisoformat(MANIFEST["as_of"])


def snapshot():
    return (
        list(Shipment.objects.order_by("shipment_id").values_list(
            "shipment_id", "customer__customer_id", "region", "status",
            "delivery_window_start", "delivery_window_end", "eta")),
        list(ShipmentEvent.objects.order_by("event_id").values_list("event_id", "event_type", "occurred_at")),
        list(DispatchNote.objects.order_by("note_id").values_list("note_id", "noted_at", "text")),
    )


class SeedTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed(AS_OF)

    def flags_by_shipment(self):
        result = defaultdict(dict)
        for f in list_exceptions(None, None, AS_OF):
            result[f.shipment_id][f.rule] = f.severity
        return result

    def test_counts_match_manifest(self):
        self.assertEqual(Shipment.objects.count(), MANIFEST["counts"]["shipments"])
        self.assertEqual(DispatchNote.objects.count(), MANIFEST["counts"]["dispatch_notes"])
        self.assertEqual(set(Shipment.objects.values_list("region", flat=True)), {"tampa", "orlando", "jacksonville"})
        self.assertEqual(Shipment.objects.values("customer").distinct().count(), 3)

    def test_planted_exceptions_match_ground_truth_exactly(self):
        expected = {p["shipment_id"]: p["flags"] for p in MANIFEST["planted"]}
        self.assertEqual(dict(self.flags_by_shipment()), expected)

    def test_normal_cohort_has_no_flags(self):
        planted = {p["shipment_id"] for p in MANIFEST["planted"]}
        flagged_normals = set(self.flags_by_shipment()) - planted
        self.assertEqual(flagged_normals, set())
        self.assertEqual(Shipment.objects.exclude(shipment_id__in=planted).count(), 92)

    def test_planted_scope_matches_manifest(self):
        for p in MANIFEST["planted"]:
            s = Shipment.objects.select_related("customer").get(shipment_id=p["shipment_id"])
            self.assertEqual((s.customer.customer_id, s.region), (p["customer_id"], p["region"]))

    def test_demo_focus_region(self):
        focus = MANIFEST["demo_focus"]
        shipments = {f.shipment_id for f in list_exceptions(None, focus["region"], AS_OF)}
        self.assertEqual(sorted(shipments), focus["shipments"])

    def test_trust_scenarios_present(self):
        t = MANIFEST["trust_scenarios"]
        self.assertIsNone(Shipment.objects.get(shipment_id=t["unavailable_eta"]["shipment_id"]).eta)
        notes = DispatchNote.objects.filter(note_id__in=t["contradictory_notes"]["note_ids"])
        self.assertEqual({n.shipment.shipment_id for n in notes}, {t["contradictory_notes"]["shipment_id"]})
        self.assertEqual(notes.count(), 2)
        injection = DispatchNote.objects.get(note_id=t["prompt_injection_note"]["note_ids"][0])
        self.assertIn("ignore all previous instructions", injection.text.lower())
        self.assertFalse(Shipment.objects.filter(shipment_id=t["unknown_shipment"]["shipment_id"]).exists())

    def test_no_records_after_demo_clock_and_all_timezone_aware(self):
        self.assertFalse(ShipmentEvent.objects.filter(occurred_at__gt=AS_OF).exists())
        self.assertFalse(DispatchNote.objects.filter(noted_at__gt=AS_OF).exists())
        for s in Shipment.objects.all():
            self.assertIsNotNone(s.delivery_window_end.tzinfo)
            self.assertLessEqual(s.delivery_window_start, s.delivery_window_end)

    def test_reseeding_is_idempotent_and_deterministic(self):
        before = snapshot()
        seed(AS_OF)
        self.assertEqual(snapshot(), before)
        self.assertEqual(Shipment.objects.count(), 100)
