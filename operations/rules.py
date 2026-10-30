"""Deterministic exception rules.

Every flag is computed from authoritative shipment and event records at an
explicit `as_of` timestamp (the demo clock), never from the real clock or AI.
Exact definitions and boundaries are documented in docs/exception_rules.md.
"""

from dataclasses import dataclass, field
from datetime import timedelta

from .models import Shipment, ShipmentEvent

E = ShipmentEvent.EventType
S = Shipment.Status


@dataclass(frozen=True)
class RuleConfig:
    # Missing scan: max allowed time since the last qualifying scan, per status.
    scan_thresholds: dict = field(
        default_factory=lambda: {
            S.PICKED_UP: timedelta(hours=6),
            S.IN_TRANSIT: timedelta(hours=6),
            S.OUT_FOR_DELIVERY: timedelta(hours=3),
        }
    )
    qualifying_scans: frozenset = frozenset({E.PICKUP_SCAN, E.HUB_SCAN, E.OUT_FOR_DELIVERY})
    # Missing POD: grace period after delivery before a missing POD is flagged.
    pod_grace: timedelta = timedelta(minutes=60)
    # Missed window becomes critical once this overdue.
    missed_window_critical_after: timedelta = timedelta(minutes=60)
    # Missing scan becomes critical at this multiple of its threshold.
    missing_scan_critical_multiple: int = 2
    # Escalation to the regional operations manager once this far past the window (SOP-ESC "When to escalate").
    escalate_after_overdue: timedelta = timedelta(hours=2)


DEFAULT_CONFIG = RuleConfig()

RULE_LABELS = {
    "missed_window": "Missed window",
    "missing_scan": "Missing scan",
    "failed_attempt": "Failed attempt",
    "missing_pod": "Missing POD",
}
SEVERITY_RANK = {"critical": 0, "warning": 1}
CLOSED_STATUSES = {S.DELIVERED, S.CANCELLED}


@dataclass(frozen=True)
class ExceptionFlag:
    shipment_id: str
    customer_id: str
    customer_name: str
    region: str
    rule: str
    severity: str
    reason: str
    threshold: str
    age: timedelta
    evidence_ids: tuple = ()

    @property
    def rule_label(self):
        return RULE_LABELS[self.rule]

    @property
    def age_display(self):
        return format_duration(self.age)


def format_duration(delta):
    minutes = max(int(delta.total_seconds() // 60), 0)
    days, minutes = divmod(minutes, 24 * 60)
    hours, minutes = divmod(minutes, 60)
    if days:
        return f"{days}d {hours}h"
    return f"{hours}h {minutes:02d}m"


def _fmt_time(dt, as_of):
    local = dt.astimezone(as_of.tzinfo)
    fmt = "%-I:%M %p" if local.date() == as_of.date() else "%b %-d %-I:%M %p"
    return local.strftime(fmt)


def evaluate_shipment(shipment, as_of, config=DEFAULT_CONFIG):
    """Return all exception flags for one shipment as of `as_of`.

    Expects `shipment.events` to be prefetched for list views. Events after
    `as_of` are ignored so the demo clock is authoritative.
    """
    events = sorted(
        (ev for ev in shipment.events.all() if ev.occurred_at <= as_of),
        key=lambda ev: (ev.occurred_at, ev.event_id),
    )

    def flag(rule, severity, reason, threshold, age, evidence=()):
        return ExceptionFlag(
            shipment_id=shipment.shipment_id,
            customer_id=shipment.customer.customer_id,
            customer_name=shipment.customer.name,
            region=shipment.get_region_display(),
            rule=rule,
            severity=severity,
            reason=reason,
            threshold=threshold,
            age=age,
            evidence_ids=tuple(evidence),
        )

    flags = []

    # Missed window: not delivered/cancelled and the demo clock is past window end.
    if shipment.status not in CLOSED_STATUSES and as_of > shipment.delivery_window_end:
        overdue = as_of - shipment.delivery_window_end
        severity = "critical" if overdue >= config.missed_window_critical_after else "warning"
        flags.append(
            flag(
                "missed_window",
                severity,
                f"Window ended {_fmt_time(shipment.delivery_window_end, as_of)}; not delivered.",
                f"Any time past window end; critical after {format_duration(config.missed_window_critical_after)}",
                overdue,
            )
        )

    # Missing scan: active shipment whose last qualifying scan is older than its status threshold.
    threshold = config.scan_thresholds.get(shipment.status)
    if threshold is not None:
        scans = [ev for ev in events if ev.event_type in config.qualifying_scans]
        if scans:
            last = scans[-1]
            gap = as_of - last.occurred_at
            if gap > threshold:
                severity = "critical" if gap >= threshold * config.missing_scan_critical_multiple else "warning"
                flags.append(
                    flag(
                        "missing_scan",
                        severity,
                        f"{shipment.get_status_display()}; last scan {_fmt_time(last.occurred_at, as_of)} ({format_duration(gap)} ago).",
                        f"{format_duration(threshold)} for {shipment.get_status_display().lower()}",
                        gap,
                        [last.event_id],
                    )
                )
        else:
            gap = as_of - shipment.imported_at
            flags.append(
                flag(
                    "missing_scan",
                    "critical",
                    f"{shipment.get_status_display()} with no qualifying scan recorded.",
                    f"{format_duration(threshold)} for {shipment.get_status_display().lower()}",
                    gap,
                )
            )

    # Failed attempt: latest delivery-relevant event is a failed attempt, with no later delivery.
    progress = [ev for ev in events if ev.event_type != E.POD_CAPTURED]
    if progress and progress[-1].event_type == E.DELIVERY_ATTEMPT_FAILED:
        attempt = progress[-1]
        detail = f": {attempt.detail}" if attempt.detail else ""
        flags.append(
            flag(
                "failed_attempt",
                "critical",
                f"Delivery attempt failed at {_fmt_time(attempt.occurred_at, as_of)}{detail}. No later delivery.",
                "Any failed attempt without a later delivery",
                as_of - attempt.occurred_at,
                [attempt.event_id],
            )
        )

    # Missing POD: delivered, no POD captured, and past the grace period.
    delivered = [ev for ev in events if ev.event_type == E.DELIVERED]
    if shipment.status == S.DELIVERED and delivered:
        delivered_event = delivered[-1]
        has_pod = any(ev.event_type == E.POD_CAPTURED for ev in events)
        since = as_of - delivered_event.occurred_at
        if not has_pod and since > config.pod_grace:
            flags.append(
                flag(
                    "missing_pod",
                    "warning",
                    f"Delivered {_fmt_time(delivered_event.occurred_at, as_of)} without proof of delivery.",
                    f"POD required within {format_duration(config.pod_grace)} of delivery",
                    since,
                    [delivered_event.event_id],
                )
            )

    return flags


def sort_flags(flags):
    return sorted(flags, key=lambda f: (SEVERITY_RANK[f.severity], -f.age.total_seconds(), f.shipment_id, f.rule))


def evaluate(shipments, as_of, config=DEFAULT_CONFIG):
    flags = []
    for shipment in shipments:
        flags.extend(evaluate_shipment(shipment, as_of, config))
    return sort_flags(flags)


def missed_window_escalation(flags, as_of, config=DEFAULT_CONFIG):
    """Time-based escalation check for a shipment's flags, or None if it has no missed window.

    Returns {"due": bool, "at": datetime, "limit": str}: due once the shipment is more than
    `escalate_after_overdue` past its window end (not at exactly the limit).
    """
    missed = next((f for f in flags if f.rule == "missed_window"), None)
    if missed is None:
        return None
    window_end = as_of - missed.age
    return {
        "due": missed.age > config.escalate_after_overdue,
        "at": window_end + config.escalate_after_overdue,
        "limit": format_duration(config.escalate_after_overdue),
    }


def rule_definitions(config=DEFAULT_CONFIG):
    """Human-readable rule table for the Demo Documentation page."""
    scan = ", ".join(
        f"{Shipment.Status(status).label.lower()} {format_duration(limit)}"
        for status, limit in config.scan_thresholds.items()
    )
    return [
        {
            "label": RULE_LABELS["missed_window"],
            "definition": "Not delivered or cancelled, and the demo timestamp is past the delivery window end.",
            "threshold": f"Any time past window end. Critical after {format_duration(config.missed_window_critical_after)}.",
        },
        {
            "label": RULE_LABELS["missing_scan"],
            "definition": "Active shipment whose most recent pickup, hub, or out-for-delivery scan is older than the limit for its status.",
            "threshold": f"{scan}. Critical at {config.missing_scan_critical_multiple}x the limit.",
        },
        {
            "label": RULE_LABELS["failed_attempt"],
            "definition": "The latest delivery event is a failed attempt and no successful delivery follows it.",
            "threshold": "Any. Always critical.",
        },
        {
            "label": RULE_LABELS["missing_pod"],
            "definition": "Delivered, but no proof of delivery has been captured.",
            "threshold": f"Flagged after a {format_duration(config.pod_grace)} grace period. Warning.",
        },
    ]
