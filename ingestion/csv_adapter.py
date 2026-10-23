"""CSV adapter: maps one source export format onto the canonical Shipment model.

Only this module knows the source column names and status codes. Connecting a
real TMS means writing another adapter with the same output (see
docs/tms_integration.md); rules, views, and AI code stay unchanged.
"""

import csv
from dataclasses import dataclass, field
from datetime import datetime

from django.db import transaction

from operations.models import Customer, Region, Shipment

from .models import IngestionRecord

# Source column -> canonical field for the sample "regional TMS export" format.
COLUMN_MAP = {
    "ShipmentNo": "shipment_id",
    "OrderRef": "source_record_id",
    "Client": "customer_id",
    "Market": "region",
    "SvcLevel": "service_type",
    "WindowOpen": "delivery_window_start",
    "WindowClose": "delivery_window_end",
    "StatusCode": "status",
    "LastEventTs": "latest_event_at",
    "DeliveredTs": "delivered_at",
    "EtaTs": "eta",
    "OwnerRole": "assigned_role",
}
REQUIRED = ["ShipmentNo", "OrderRef", "Client", "Market", "SvcLevel", "WindowOpen", "WindowClose", "StatusCode"]
TIMESTAMPS = ["WindowOpen", "WindowClose", "LastEventTs", "DeliveredTs", "EtaTs"]
STATUS_CODES = {
    "NEW": Shipment.Status.CREATED,
    "PU": Shipment.Status.PICKED_UP,
    "INT": Shipment.Status.IN_TRANSIT,
    "OFD": Shipment.Status.OUT_FOR_DELIVERY,
    "ATT": Shipment.Status.ATTEMPTED,
    "DEL": Shipment.Status.DELIVERED,
    "CAN": Shipment.Status.CANCELLED,
}
REGIONS = {label.lower(): value for value, label in Region.choices}


@dataclass
class ImportResult:
    accepted: list = field(default_factory=list)  # canonical dicts
    errors: list = field(default_factory=list)  # {"row": n, "field": col, "error": msg}

    @property
    def rejected_rows(self):
        return len({e["row"] for e in self.errors})


def _parse_timestamp(value):
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        raise ValueError("timestamp must include a timezone offset")
    return dt


def parse_rows(rows, known_customers):
    """Validate and normalize source rows. Never guesses missing values."""
    result = ImportResult()
    seen = set()
    for n, raw in enumerate(rows, start=2):  # row 1 is the header
        row = {k.strip(): (v or "").strip() for k, v in raw.items() if k}
        errors = []

        def err(col, msg):
            errors.append({"row": n, "field": col, "error": msg})

        for col in REQUIRED:
            if not row.get(col):
                err(col, "required value is missing")
        record = {}
        for col in TIMESTAMPS:
            if row.get(col):
                try:
                    record[COLUMN_MAP[col]] = _parse_timestamp(row[col])
                except ValueError as exc:
                    err(col, str(exc) if "offset" in str(exc) else f"not an ISO 8601 timestamp: {row[col]!r}")
            else:
                record[COLUMN_MAP[col]] = None

        status = STATUS_CODES.get(row.get("StatusCode", "").upper())
        if row.get("StatusCode") and status is None:
            err("StatusCode", f"unknown status code {row['StatusCode']!r}")
        region = REGIONS.get(row.get("Market", "").lower())
        if row.get("Market") and region is None:
            err("Market", f"unknown region {row['Market']!r}")
        if row.get("Client") and row["Client"] not in known_customers:
            err("Client", f"unknown customer {row['Client']!r}")

        start, end = record.get("delivery_window_start"), record.get("delivery_window_end")
        if start and end and start > end:
            err("WindowClose", "window closes before it opens")
        if status == Shipment.Status.DELIVERED and not record.get("delivered_at"):
            err("DeliveredTs", "delivered status requires a delivered timestamp")
        if status != Shipment.Status.DELIVERED and record.get("delivered_at"):
            err("DeliveredTs", "delivered timestamp present but status is not delivered")
        key = row.get("OrderRef")
        if key in seen:
            err("OrderRef", f"duplicate source record {key!r} in file")
        seen.add(key)

        if errors:
            result.errors.extend(errors)
            continue
        record.update(
            shipment_id=row["ShipmentNo"],
            source_record_id=row["OrderRef"],
            customer_id=row["Client"],
            region=region,
            service_type=row["SvcLevel"],
            status=status,
            assigned_role=row.get("OwnerRole", ""),
        )
        result.accepted.append(record)
    return result


def import_csv(path, source_system, imported_at, dry_run=False):
    """Validate a CSV export and upsert valid rows by (source_system, source_record_id)."""
    customers = {c.customer_id: c for c in Customer.objects.all()}
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        missing_cols = [c for c in REQUIRED if c not in (reader.fieldnames or [])]
        if missing_cols:
            result = ImportResult(errors=[{"row": 1, "field": c, "error": "required column missing"} for c in missing_cols])
        else:
            result = parse_rows(reader, set(customers))

    if dry_run:
        return result
    with transaction.atomic():
        for record in result.accepted:
            customer = customers[record.pop("customer_id")]
            Shipment.objects.update_or_create(
                source_system=source_system,
                source_record_id=record.pop("source_record_id"),
                defaults={**record, "customer": customer, "imported_at": imported_at},
            )
        IngestionRecord.objects.create(
            kind=IngestionRecord.Kind.SHIPMENT_CSV,
            source_name=f"{source_system}:{path}",
            rows_accepted=len(result.accepted),
            rows_rejected=result.rejected_rows,
            errors=result.errors,
        )
    return result
