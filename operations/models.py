"""Canonical operational schema.

Source formats (CSV exports today, a TMS API later) are mapped into these
models by `ingestion`; nothing else in the app depends on source layouts.
"""

from django.db import models


class Region(models.TextChoices):
    TAMPA = "tampa", "Tampa"
    ORLANDO = "orlando", "Orlando"
    JACKSONVILLE = "jacksonville", "Jacksonville"


class Customer(models.Model):
    customer_id = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=120)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Shipment(models.Model):
    class Status(models.TextChoices):
        CREATED = "created", "Created"
        PICKED_UP = "picked_up", "Picked up"
        IN_TRANSIT = "in_transit", "In transit"
        OUT_FOR_DELIVERY = "out_for_delivery", "Out for delivery"
        ATTEMPTED = "attempted", "Delivery attempted"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    shipment_id = models.CharField(max_length=32, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="shipments")
    region = models.CharField(max_length=16, choices=Region.choices)
    service_type = models.CharField(max_length=32)
    delivery_window_start = models.DateTimeField()
    delivery_window_end = models.DateTimeField()
    status = models.CharField(max_length=24, choices=Status.choices)
    latest_event_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    # Optional and only ever copied from a source record; never inferred.
    eta = models.DateTimeField(null=True, blank=True)
    assigned_role = models.CharField(max_length=64, blank=True)
    source_system = models.CharField(max_length=32)
    source_record_id = models.CharField(max_length=64)
    imported_at = models.DateTimeField()

    class Meta:
        ordering = ["shipment_id"]
        constraints = [
            models.UniqueConstraint(
                fields=["source_system", "source_record_id"], name="unique_shipment_source_record"
            ),
        ]
        indexes = [models.Index(fields=["customer", "region"])]

    def __str__(self):
        return self.shipment_id


class ShipmentEvent(models.Model):
    class EventType(models.TextChoices):
        CREATED = "created", "Created"
        PICKUP_SCAN = "pickup_scan", "Pickup scan"
        HUB_SCAN = "hub_scan", "Hub scan"
        OUT_FOR_DELIVERY = "out_for_delivery", "Out for delivery"
        DELIVERY_ATTEMPT_FAILED = "delivery_attempt_failed", "Delivery attempt failed"
        DELIVERED = "delivered", "Delivered"
        POD_CAPTURED = "pod_captured", "Proof of delivery captured"
        CANCELLED = "cancelled", "Cancelled"

    event_id = models.CharField(max_length=32, unique=True)
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name="events")
    event_type = models.CharField(max_length=32, choices=EventType.choices)
    occurred_at = models.DateTimeField()
    detail = models.CharField(max_length=255, blank=True)
    source_system = models.CharField(max_length=32)
    source_record_id = models.CharField(max_length=64)

    class Meta:
        ordering = ["occurred_at", "event_id"]

    def __str__(self):
        return f"{self.event_id} {self.event_type}"


class DispatchNote(models.Model):
    note_id = models.CharField(max_length=32, unique=True)
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name="notes")
    author_role = models.CharField(max_length=64)
    noted_at = models.DateTimeField()
    text = models.TextField()
    source_system = models.CharField(max_length=32)
    source_record_id = models.CharField(max_length=64)

    class Meta:
        ordering = ["noted_at", "note_id"]

    def __str__(self):
        return self.note_id
