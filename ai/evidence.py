"""Bounded evidence packages with stable IDs.

The model only sees what is assembled here, and every citation it returns must
be one of these IDs. Dispatch note text is marked untrusted: it is data written
by people in the field, never instructions.
"""

from dataclasses import dataclass, field

from . import tools
from .schemas import ListExceptionsInput, RetrieveProcedureInput, ShipmentInput

MAX_EVENTS = 25
MAX_NOTES = 10
MAX_NOTE_CHARS = 600
MAX_BRIEFING_FLAGS = 25


@dataclass
class EvidencePackage:
    kind: str  # "shipment" or "briefing"
    subject: str  # shipment ID, or a scope label for briefings
    as_of: str
    facts: dict = field(default_factory=dict)
    flags: list = field(default_factory=list)
    events: list = field(default_factory=list)
    notes: list = field(default_factory=list)
    procedures: list = field(default_factory=list)
    procedure_gaps: list = field(default_factory=list)
    missing_information: list = field(default_factory=list)
    retrieval: list = field(default_factory=list)  # procedure retrieval method per issue
    deterministic: dict = field(default_factory=dict)
    truncated: bool = False

    @property
    def ids(self):
        ids = {f["flag_id"] for f in self.flags}
        ids |= {e for f in self.flags for e in f.get("evidence_ids", [])}  # events the rules cited
        ids |= {e["event_id"] for e in self.events}
        ids |= {n["note_id"] for n in self.notes}
        ids |= {p["chunk_id"] for p in self.procedures}
        if self.kind == "shipment":
            ids.add(self.subject)
        else:
            ids |= {f["shipment_id"] for f in self.flags}
        return ids

    @property
    def retrieval_label(self):
        methods = set(self.retrieval) - {"none"}
        if not methods:
            return "no procedures on file"
        if methods == {"semantic"}:
            return "semantic (Pinecone)"
        if any("unavailable" in m for m in methods):
            return "database (vector search unavailable)"
        return "database" if methods <= {"database"} else "mixed"

    def to_payload(self):
        payload = {
            "evidence_kind": self.kind,
            "subject": self.subject,
            "as_of": self.as_of,
            "deterministic_results": self.deterministic,
            "exception_flags": self.flags,
            "missing_information": self.missing_information,
        }
        if self.kind == "shipment":
            payload["shipment_facts"] = {"id": self.subject, **self.facts}
            payload["events"] = self.events
            payload["dispatch_notes_untrusted"] = [
                {"note_id": n["note_id"], "author_role": n["author_role"], "noted_at": n["noted_at"],
                 "untrusted_text": n["text"]}
                for n in self.notes
            ]
            payload["procedures"] = self.procedures
            payload["procedure_gaps"] = self.procedure_gaps
        if self.truncated:
            payload["note"] = "Evidence was truncated to stay within limits."
        return payload


def _clip(text, limit):
    return text if len(text) <= limit else text[: limit - 1] + "…"


def build_shipment_evidence(ctx, shipment_id):
    """Evidence for one shipment, or None if it doesn't exist in the scope."""
    args = ShipmentInput(shipment_id=shipment_id)
    facts = tools.get_shipment(ctx, args)
    if facts is None:
        return None
    flags = [f for f in tools.list_exceptions(ctx, ListExceptionsInput(region=facts["region"])) if f["shipment_id"] == shipment_id]
    events = tools.get_shipment_events(ctx, args)
    notes = tools.get_dispatch_notes(ctx, args)
    pkg = EvidencePackage(kind="shipment", subject=shipment_id, as_of=ctx.as_of.isoformat(), facts=facts, flags=flags)
    pkg.truncated = len(events) > MAX_EVENTS or len(notes) > MAX_NOTES
    pkg.events = events[-MAX_EVENTS:]
    pkg.notes = [{**n, "text": _clip(n["text"], MAX_NOTE_CHARS)} for n in notes[-MAX_NOTES:]]
    pkg.deterministic = {"flag_count": len(flags), "rules": [f["rule"] for f in flags]}

    issues = list(dict.fromkeys(f["rule"] for f in flags))
    if flags:
        issues.append("escalation")
    for issue in issues:
        details = [f["reason"] for f in flags if issue in (f["rule"], "escalation")]
        query = tools.procedure_query(issue, details)
        result = tools.retrieve_procedure(ctx, RetrieveProcedureInput(issue_type=issue, region=facts["region"], query=query))
        pkg.retrieval.append(result["retrieval"])
        if result["match"] == "none":
            pkg.procedure_gaps.append(issue)
        pkg.procedures.extend(result["sections"])

    if facts["eta"] == "not provided by source":
        pkg.missing_information.append("ETA is not provided by the source system.")
    if not events:
        pkg.missing_information.append("No scan events are recorded for this shipment.")
    for issue in pkg.procedure_gaps:
        pkg.missing_information.append(f"No {issue.replace('_', ' ')} procedure is on file for {facts['customer']}.")
    return pkg


def build_briefing_evidence(ctx, region=None, scope_label="All customers"):
    flags = tools.list_exceptions(ctx, ListExceptionsInput(region=region))
    pkg = EvidencePackage(kind="briefing", subject=scope_label, as_of=ctx.as_of.isoformat())
    pkg.truncated = len(flags) > MAX_BRIEFING_FLAGS
    pkg.flags = flags[:MAX_BRIEFING_FLAGS]
    pkg.deterministic = {
        "shipment_count": len({f["shipment_id"] for f in flags}),
        "exception_count": len(flags),
        "by_rule": {rule: sum(1 for f in flags if f["rule"] == rule) for rule in dict.fromkeys(f["rule"] for f in flags)},
    }
    return pkg
