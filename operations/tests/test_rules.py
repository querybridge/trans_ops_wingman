from datetime import datetime, timedelta, timezone

from django.test import TestCase

from operations.models import Customer, Region, Shipment, ShipmentEvent
from operations.rules import evaluate, evaluate_shipment, format_duration, missed_window_escalation

EDT = timezone(timedelta(hours=-4))
AS_OF = datetime(2026, 10, 21, 15, 0, tzinfo=EDT)
E = ShipmentEvent.EventType
S = Shipment.Status


class RuleTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.customer = Customer.objects.create(customer_id="CUST-T", name="Test Retail")

    def make(self, status, window_end=None, events=(), sid="SHP-T1"):
        window_end = window_end or AS_OF + timedelta(hours=3)
        shipment = Shipment.objects.create(
            shipment_id=sid, customer=self.customer, region=Region.TAMPA, service_type="Standard",
            delivery_window_start=window_end - timedelta(hours=4), delivery_window_end=window_end,
            status=status, source_system="test", source_record_id=sid, imported_at=AS_OF - timedelta(minutes=5),
        )
        for i, (kind, at) in enumerate(events, start=1):
            ShipmentEvent.objects.create(
                event_id=f"{sid}-E{i}", shipment=shipment, event_type=kind, occurred_at=at,
                source_system="test", source_record_id=f"{sid}-E{i}",
            )
        return shipment

    def rules(self, shipment, as_of=AS_OF):
        return {f.rule: f.severity for f in evaluate_shipment(shipment, as_of)}

    def recent_scan(self):
        return [(E.OUT_FOR_DELIVERY, AS_OF - timedelta(minutes=30))]


class MissedWindowTests(RuleTestCase):
    def test_exactly_at_window_end_is_not_flagged(self):
        s = self.make(S.OUT_FOR_DELIVERY, window_end=AS_OF, events=self.recent_scan())
        self.assertNotIn("missed_window", self.rules(s))

    def test_one_minute_past_window_end_is_warning(self):
        s = self.make(S.OUT_FOR_DELIVERY, window_end=AS_OF - timedelta(minutes=1), events=self.recent_scan())
        self.assertEqual(self.rules(s)["missed_window"], "warning")

    def test_becomes_critical_at_sixty_minutes(self):
        s59 = self.make(S.OUT_FOR_DELIVERY, window_end=AS_OF - timedelta(minutes=59), events=self.recent_scan(), sid="A")
        s60 = self.make(S.OUT_FOR_DELIVERY, window_end=AS_OF - timedelta(minutes=60), events=self.recent_scan(), sid="B")
        self.assertEqual(self.rules(s59)["missed_window"], "warning")
        self.assertEqual(self.rules(s60)["missed_window"], "critical")

    def test_delivered_and_cancelled_are_never_missed(self):
        past = AS_OF - timedelta(hours=5)
        delivered = self.make(S.DELIVERED, window_end=past, sid="D", events=[
            (E.DELIVERED, past + timedelta(hours=1)), (E.POD_CAPTURED, past + timedelta(hours=1, minutes=1))])
        cancelled = self.make(S.CANCELLED, window_end=past, sid="C")
        self.assertEqual(self.rules(delivered), {})
        self.assertEqual(self.rules(cancelled), {})


class EscalationTests(RuleTestCase):
    def test_escalation_due_only_after_two_hours_past_window(self):
        at_limit = self.make(S.OUT_FOR_DELIVERY, window_end=AS_OF - timedelta(hours=2), events=self.recent_scan(), sid="A")
        past_limit = self.make(S.OUT_FOR_DELIVERY, window_end=AS_OF - timedelta(hours=2, minutes=1), events=self.recent_scan(), sid="B")
        check = missed_window_escalation(evaluate_shipment(at_limit, AS_OF), AS_OF)
        self.assertEqual(check["due"], False)
        self.assertEqual(check["at"], AS_OF)
        self.assertTrue(missed_window_escalation(evaluate_shipment(past_limit, AS_OF), AS_OF)["due"])

    def test_no_missed_window_means_no_time_based_escalation(self):
        s = self.make(S.ATTEMPTED, events=[(E.DELIVERY_ATTEMPT_FAILED, AS_OF - timedelta(hours=1))])
        self.assertIsNone(missed_window_escalation(evaluate_shipment(s, AS_OF), AS_OF))


class MissingScanTests(RuleTestCase):
    def test_gap_equal_to_threshold_is_not_flagged(self):
        s = self.make(S.IN_TRANSIT, events=[(E.HUB_SCAN, AS_OF - timedelta(hours=6))])
        self.assertNotIn("missing_scan", self.rules(s))

    def test_gap_one_minute_over_threshold_is_flagged(self):
        s = self.make(S.IN_TRANSIT, events=[(E.HUB_SCAN, AS_OF - timedelta(hours=6, minutes=1))])
        self.assertEqual(self.rules(s)["missing_scan"], "warning")

    def test_out_for_delivery_uses_shorter_threshold(self):
        s = self.make(S.OUT_FOR_DELIVERY, events=[(E.OUT_FOR_DELIVERY, AS_OF - timedelta(hours=3, minutes=1))])
        self.assertEqual(self.rules(s)["missing_scan"], "warning")

    def test_critical_at_twice_threshold(self):
        s = self.make(S.OUT_FOR_DELIVERY, events=[(E.OUT_FOR_DELIVERY, AS_OF - timedelta(hours=6))])
        self.assertEqual(self.rules(s)["missing_scan"], "critical")

    def test_non_scan_events_do_not_count(self):
        s = self.make(S.IN_TRANSIT, events=[(E.HUB_SCAN, AS_OF - timedelta(hours=7)), (E.CREATED, AS_OF - timedelta(minutes=10))])
        self.assertIn("missing_scan", self.rules(s))

    def test_active_shipment_with_no_scans_is_critical(self):
        s = self.make(S.PICKED_UP)
        self.assertEqual(self.rules(s)["missing_scan"], "critical")

    def test_created_and_attempted_are_not_checked(self):
        created = self.make(S.CREATED, sid="C", events=[(E.CREATED, AS_OF - timedelta(days=2))])
        self.assertNotIn("missing_scan", self.rules(created))


class FailedAttemptTests(RuleTestCase):
    def test_latest_failed_attempt_is_critical(self):
        s = self.make(S.ATTEMPTED, events=[(E.OUT_FOR_DELIVERY, AS_OF - timedelta(hours=4)),
                                           (E.DELIVERY_ATTEMPT_FAILED, AS_OF - timedelta(hours=2))])
        self.assertEqual(self.rules(s)["failed_attempt"], "critical")

    def test_later_delivery_clears_failed_attempt(self):
        s = self.make(S.DELIVERED, events=[(E.DELIVERY_ATTEMPT_FAILED, AS_OF - timedelta(hours=4)),
                                           (E.DELIVERED, AS_OF - timedelta(hours=2)),
                                           (E.POD_CAPTURED, AS_OF - timedelta(hours=2))])
        self.assertNotIn("failed_attempt", self.rules(s))

    def test_reattempt_in_progress_clears_failed_attempt(self):
        s = self.make(S.OUT_FOR_DELIVERY, events=[(E.DELIVERY_ATTEMPT_FAILED, AS_OF - timedelta(hours=2)),
                                                  (E.OUT_FOR_DELIVERY, AS_OF - timedelta(minutes=20))])
        self.assertNotIn("failed_attempt", self.rules(s))


class MissingPodTests(RuleTestCase):
    def delivered(self, minutes_ago, pod=False, sid="SHP-T1"):
        at = AS_OF - timedelta(minutes=minutes_ago)
        events = [(E.DELIVERED, at)] + ([(E.POD_CAPTURED, at + timedelta(minutes=1))] if pod else [])
        return self.make(S.DELIVERED, window_end=AS_OF + timedelta(hours=1), events=events, sid=sid)

    def test_within_grace_is_not_flagged(self):
        self.assertNotIn("missing_pod", self.rules(self.delivered(60)))

    def test_past_grace_is_flagged(self):
        self.assertEqual(self.rules(self.delivered(61))["missing_pod"], "warning")

    def test_pod_present_is_not_flagged(self):
        self.assertNotIn("missing_pod", self.rules(self.delivered(240, pod=True)))


class ClockAndOrderingTests(RuleTestCase):
    def test_events_after_as_of_are_ignored(self):
        s = self.make(S.ATTEMPTED, events=[(E.DELIVERY_ATTEMPT_FAILED, AS_OF - timedelta(hours=1)),
                                           (E.DELIVERED, AS_OF + timedelta(hours=1))])
        self.assertIn("failed_attempt", self.rules(s))

    def test_one_shipment_can_have_multiple_flags(self):
        s = self.make(S.IN_TRANSIT, window_end=AS_OF - timedelta(minutes=30), events=[(E.HUB_SCAN, AS_OF - timedelta(hours=8))])
        self.assertEqual(self.rules(s), {"missed_window": "warning", "missing_scan": "warning"})

    def test_sorted_by_severity_then_age(self):
        warn_old = self.make(S.IN_TRANSIT, sid="W", events=[(E.HUB_SCAN, AS_OF - timedelta(hours=9))])
        crit_new = self.make(S.ATTEMPTED, sid="C", events=[(E.DELIVERY_ATTEMPT_FAILED, AS_OF - timedelta(minutes=10))])
        flags = evaluate(Shipment.objects.prefetch_related("events"), AS_OF)
        self.assertEqual([f.shipment_id for f in flags], ["C", "W"])

    def test_format_duration(self):
        self.assertEqual(format_duration(timedelta(minutes=125)), "2h 05m")
        self.assertEqual(format_duration(timedelta(hours=27)), "1d 3h")
