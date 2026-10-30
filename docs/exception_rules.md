# Exception Rules

All flags are computed in `operations/rules.py` from authoritative shipment and event records at the fixed demo timestamp (`DEMO_AS_OF`). Events dated after the demo timestamp are ignored. The AI never decides what is flagged or how many. Thresholds live in `RuleConfig`; the values below are the defaults.

| Rule | Flagged when | Boundary (not flagged at exactly) | Severity |
| --- | --- | --- | --- |
| Missed window | Status is not delivered or cancelled **and** demo time > `delivery_window_end` | demo time = window end | Warning; **critical** once ≥ 60 min overdue |
| Missing scan | Status is picked up, in transit, or out for delivery **and** time since the last qualifying scan (pickup, hub, or out-for-delivery) > limit for the status | gap = limit | Warning; **critical** at ≥ 2× the limit, or if no qualifying scan exists |
| Failed attempt | The latest event (ignoring POD capture) is a failed delivery attempt, so no delivery or re-attempt follows it | n/a | Always critical |
| Missing POD | Status is delivered, no POD-captured event exists, **and** time since delivery > grace period | time since delivery = grace | Warning |

Scan limits: picked up 6h, in transit 6h, out for delivery 3h. POD grace: 60 min. Created and attempted shipments are not scan-checked (attempted shipments are covered by the failed-attempt rule).

**Age** shown per flag: time past window end (missed window), time since last scan (missing scan), time since the attempt (failed attempt), or time since delivery (missing POD).

**Ordering:** critical before warning, then oldest first, then shipment ID.

**Counts:** "Needing attention" counts distinct shipments. One shipment can carry several flags, so the flag count can be higher (v1 dataset: 8 shipments, 9 flags).

**Escalation check (Worklist):** a missed window becomes "Escalation due" once the shipment is **more than** 2 hours past its window end (`RuleConfig.escalate_after_overdue`, from SOP-ESC "When to escalate"). At exactly 2 hours it shows "Escalate if not delivered by" that time. The other SOP-ESC triggers (package not located within two hours of the search, conflicting accounts) depend on facts the records don't hold, so the Worklist quotes them instead of evaluating them.

**Worklist steps:** procedure sections are quoted verbatim. Sections that define or scope a procedure (Scope, Purpose, Thresholds, Requirement, Grace period, Roles) are left out of the action steps. Ownership sections become the "Owner" line. When no procedure exists for the customer and issue, the gap is shown and no other customer's procedure is substituted.

Severity is a transparent rule outcome, never a learned probability.

Boundary tests: `operations/tests/test_rules.py`.
