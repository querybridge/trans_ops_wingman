"""Read-only query functions used by views and, later, by the AI tools.

Customer scope is always passed in from validated application context.
"""

from .models import Customer, Region, Shipment


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
    """Deterministic exception rules. Not implemented yet: returns None, never fake rows."""
    return None


def dashboard_metrics(customer_id, region, as_of):
    exceptions = list_exceptions(customer_id, region, as_of)
    shipments = scoped_shipments(customer_id, region).count()
    if exceptions is None:
        return {"shipments": shipments, "needing_attention": None, "missed_windows": None, "missing_pod": None}
    return {
        "shipments": shipments,
        "needing_attention": len({e.shipment_id for e in exceptions}),
        "missed_windows": sum(1 for e in exceptions if e.rule == "missed_window"),
        "missing_pod": sum(1 for e in exceptions if e.rule == "missing_pod"),
    }
