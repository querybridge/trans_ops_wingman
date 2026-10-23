"""Read-only query functions used by views and, later, by the AI tools.

Customer scope is always passed in from validated application context.
"""

from .models import Customer, Region, Shipment
from .rules import evaluate, evaluate_shipment


def scoped_shipments(customer_id=None, region=None):
    qs = Shipment.objects.select_related("customer")
    if customer_id:
        qs = qs.filter(customer__customer_id=customer_id)
    if region:
        qs = qs.filter(region=region)
    return qs


def get_shipment(shipment_id, customer_id=None):
    qs = scoped_shipments(customer_id).prefetch_related("events", "notes")
    return qs.filter(shipment_id=shipment_id).first()


def filter_choices():
    return {
        "customers": list(Customer.objects.values_list("customer_id", "name")),
        "regions": Region.choices,
    }


def list_exceptions(customer_id, region, as_of):
    """Prioritized exception flags for the scope, from the deterministic rules."""
    return evaluate(scoped_shipments(customer_id, region).prefetch_related("events"), as_of)


def shipment_flags(shipment, as_of):
    return evaluate_shipment(shipment, as_of)


def dashboard_metrics(customer_id, region, as_of, exceptions=None):
    if exceptions is None:
        exceptions = list_exceptions(customer_id, region, as_of)
    shipments = scoped_shipments(customer_id, region).count()
    return {
        "shipments": shipments,
        "needing_attention": len({e.shipment_id for e in exceptions}),
        "missed_windows": sum(1 for e in exceptions if e.rule == "missed_window"),
        "missing_pod": sum(1 for e in exceptions if e.rule == "missing_pod"),
    }


ISSUE_FOR_RULE = {
    "missed_window": "missed_window",
    "missing_scan": "missing_scan",
    "failed_attempt": "failed_attempt",
    "missing_pod": "missing_pod",
}


def retrieve_procedures(customer_id, issue_type, region, as_of):
    """Procedures in effect on the demo date for this customer and issue.

    Customer-specific documents take precedence; otherwise shared-scope
    documents apply. Another customer's procedure is never returned.
    Returns (documents_with_chunks, match) where match is "customer",
    "shared", or "none".
    """
    from django.db.models import Q

    from .models import ProcedureDocument

    day = as_of.date()
    docs = (
        ProcedureDocument.objects.filter(issue_type=issue_type, effective_from__lte=day)
        .filter(Q(effective_to__isnull=True) | Q(effective_to__gte=day))
        .filter(Q(region="") | Q(region=region or ""))
        .select_related("customer")
        .prefetch_related("chunks")
    )
    specific = [d for d in docs if d.customer_id and d.customer.customer_id == customer_id]
    if specific:
        chosen, match = specific, "customer"
    else:
        chosen, match = [d for d in docs if d.customer_id is None], "shared"
    latest = {}
    for doc in sorted(chosen, key=lambda d: d.effective_from):
        latest[doc.document_id] = doc  # newest effective version per document wins
    result = sorted(latest.values(), key=lambda d: d.document_id)
    return result, (match if result else "none")


def procedures_for_flags(shipment, flags, as_of):
    """Procedure sections relevant to a shipment's flags, plus escalation ownership."""
    customer_id, region = shipment.customer.customer_id, shipment.region
    groups = []
    issues = []
    for f in flags:
        issue = ISSUE_FOR_RULE[f.rule]
        if issue not in issues:
            issues.append(issue)
    if flags:
        issues.append("escalation")
    for issue in issues:
        from .models import ProcedureDocument

        docs, match = retrieve_procedures(customer_id, issue, region, as_of)
        label = ProcedureDocument.IssueType(issue).label.lower()
        groups.append({"issue_type": issue, "label": label, "documents": docs, "match": match})
    return groups
