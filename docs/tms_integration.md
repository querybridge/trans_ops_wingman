# Path to TMS Integration

The app depends only on the canonical schema in `operations/models.py` (`Shipment`, `ShipmentEvent`, `DispatchNote`). Source formats are isolated in adapters under `ingestion/`.

## Today: CSV adapter

`ingestion/csv_adapter.py` maps a sample "regional TMS export" onto `Shipment`:

| Source column | Canonical field | Notes |
| --- | --- | --- |
| ShipmentNo | shipment_id | |
| OrderRef | source_record_id | Upsert key together with `source_system` |
| Client | customer | Must be a known customer |
| Market | region | Tampa / Orlando / Jacksonville |
| SvcLevel | service_type | |
| WindowOpen / WindowClose | delivery_window_start / end | ISO 8601 **with offset**; open ≤ close |
| StatusCode | status | NEW, PU, INT, OFD, ATT, DEL, CAN |
| LastEventTs / DeliveredTs | latest_event_at / delivered_at | DEL requires DeliveredTs; others must not have it |
| EtaTs | eta | Optional; blank stays unknown, never inferred |
| OwnerRole | assigned_role | Optional |

```bash
.yzer/bin/python manage.py import_shipments_csv ingestion/samples/regional_tms_export.csv --dry-run
.yzer/bin/python manage.py import_shipments_csv ingestion/samples/regional_tms_export.csv
```

Invalid rows are rejected with row, field, and reason, and every run is recorded as an `IngestionRecord`. The sample file has 3 valid rows and 4 rows with deliberate errors. Re-running is idempotent. `reset_demo` removes imported rows.

## What changes for a real TMS

| Area | Change | What stays the same |
| --- | --- | --- |
| Adapter | New module mapping the TMS export or API payload (column names, status codes, time zones) to the canonical fields | Rules, views, AI tools, evaluation |
| Events | Import scan events into `ShipmentEvent`; the rules read scans from events, so event coverage matters more than shipment status | Rule definitions |
| Scheduling | A scheduled job (PythonAnywhere scheduled task) pulls a read-only export every N minutes instead of a manual command | Web requests stay read-only |
| Identity | Map TMS customer and region codes; decide how users map to customer scope | Scope enforcement inside tools |
| Clock | Replace the fixed demo timestamp with the import snapshot time, so rules evaluate against the data's freshness | Rule code (it already takes `as_of`) |
| Data handling | Real customer data needs access control, retention, and a decision about what may be sent to hosted AI providers | Evidence packages are already bounded |

Smallest real pilot: one region, one read-only daily export, one manager, measured against their current preparation time.
