"""Typed, read-only tools over the operational data.

Customer scope comes from `ToolContext`, which the view builds from validated
application state. A customer_id supplied as a tool argument (for example by a
model) is only accepted if it matches that scope; it can never widen it. There
is no arbitrary SQL and no file access.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from django.utils import timezone

from operations import services
from operations.models import Shipment

from .schemas import ListExceptionsInput, RetrieveProcedureInput, ShipmentInput


def _local(dt):
    """ISO 8601 in the operations timezone (America/New_York), so the model reports local times."""
    return timezone.localtime(dt).isoformat()


class ScopeError(PermissionError):
    pass


class UnknownToolError(LookupError):
    pass


@dataclass(frozen=True)
class ToolContext:
    customer_id: Optional[str]  # None = every customer the signed-in user may see
    as_of: datetime


def _scope(ctx, requested):
    if requested and ctx.customer_id and requested != ctx.customer_id:
        raise ScopeError(f"customer {requested!r} is outside the current scope")
    return ctx.customer_id or requested


def _shipment(ctx, args):
    return services.get_shipment(args.shipment_id, _scope(ctx, args.customer_id))


def list_exceptions(ctx, args: ListExceptionsInput):
    return [
        {
            "flag_id": f"FLAG-{f.shipment_id}-{f.rule}",
            "shipment_id": f.shipment_id,
            "customer": f.customer_name,
            "region": f.region,
            "rule": f.rule,
            "severity": f.severity,
            "reason": f.reason,
            "threshold": f.threshold,
            "age": f.age_display,
            "evidence_ids": list(f.evidence_ids),
        }
        for f in services.list_exceptions(_scope(ctx, args.customer_id), args.region, ctx.as_of)
    ]


def get_shipment(ctx, args: ShipmentInput):
    s = _shipment(ctx, args)
    if s is None:
        return None
    closed = s.status in {Shipment.Status.DELIVERED, Shipment.Status.CANCELLED}
    return {
        "shipment_id": s.shipment_id,
        "customer_id": s.customer.customer_id,
        "customer": s.customer.name,
        "region": s.region,
        "service_type": s.service_type,
        "status": s.status,
        "delivery_window_start": _local(s.delivery_window_start),
        "delivery_window_end": _local(s.delivery_window_end),
        "latest_event_at": _local(s.latest_event_at) if s.latest_event_at else None,
        "delivered_at": _local(s.delivered_at) if s.delivered_at else None,
        "eta": _local(s.eta) if s.eta else ("not provided by source" if not closed else None),
        "assigned_role": s.assigned_role or None,
        "source": f"{s.source_system}/{s.source_record_id}",
    }


def get_shipment_events(ctx, args: ShipmentInput):
    s = _shipment(ctx, args)
    if s is None:
        return None
    return [
        {"event_id": e.event_id, "type": e.event_type, "occurred_at": _local(e.occurred_at), "detail": e.detail}
        for e in s.events.all()
        if e.occurred_at <= ctx.as_of
    ]


def get_dispatch_notes(ctx, args: ShipmentInput):
    s = _shipment(ctx, args)
    if s is None:
        return None
    return [
        {"note_id": n.note_id, "author_role": n.author_role, "noted_at": _local(n.noted_at), "text": n.text}
        for n in s.notes.all()
        if n.noted_at <= ctx.as_of
    ]


def retrieve_procedure(ctx, args: RetrieveProcedureInput):
    customer_id = _scope(ctx, args.customer_id)
    docs, match = services.retrieve_procedures(customer_id, args.issue_type, args.region, ctx.as_of)
    return {
        "issue_type": args.issue_type,
        "match": match,
        "sections": [
            {
                "chunk_id": c.chunk_id,
                "document_id": d.document_id,
                "version": d.version,
                "title": d.title,
                "scope": d.scope_label,
                "section": c.section,
                "text": c.text,
            }
            for d in docs
            for c in d.chunks.all()
        ],
    }


TOOLS = {
    "list_exceptions": (ListExceptionsInput, list_exceptions),
    "get_shipment": (ShipmentInput, get_shipment),
    "get_shipment_events": (ShipmentInput, get_shipment_events),
    "get_dispatch_notes": (ShipmentInput, get_dispatch_notes),
    "retrieve_procedure": (RetrieveProcedureInput, retrieve_procedure),
}


def call_tool(ctx, name, arguments):
    """Validate a tool call (name and arguments) before running it."""
    if name not in TOOLS:
        raise UnknownToolError(f"unknown tool {name!r}")
    input_model, fn = TOOLS[name]
    return fn(ctx, input_model.model_validate(arguments))
