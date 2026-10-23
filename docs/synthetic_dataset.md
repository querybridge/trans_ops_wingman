# Synthetic Dataset v1

Built by `ingestion/seed.py` with random seed `20261021`, relative to the demo timestamp `2026-10-21T15:00:00-04:00`. All customers, people, and events are fictional retail deliveries.

```bash
.yzer/bin/python manage.py seed_demo          # create or replace synthetic data (idempotent)
.yzer/bin/python manage.py reset_demo --yes   # wipe shipments, ingestion records, eval runs; reseed (keeps users)
```

**Contents:** 100 shipments (SHP-00001 to SHP-00100), 3 customers (Harborview Home Goods, Sunline Outfitters, Coastal Kitchen Supply), 3 regions (Tampa, Orlando, Jacksonville), 267 scan events, and 30 dispatch notes. IDs are stable: events `EVT-<shipment>-<n>`, notes `NOTE-<shipment>-<n>`.

**Ground truth:** `evaluation/fixtures/ground_truth_v1.json`, written by hand separately from the rules code. It lists the 8 planted exception shipments (9 flags), the expectation that the other 92 have zero flags, and the trust scenarios:

| Scenario | Where |
| --- | --- |
| ETA unavailable from source | SHP-00007 (Tampa, missed window) |
| Contradictory notes (driver vs. customer) | SHP-00031 (Tampa, failed attempt): NOTE-00031-1 / NOTE-00031-2 |
| Prompt-injection text in a dispatch note | SHP-00046 (Jacksonville): NOTE-00046-2 |
| One shipment, two flags | SHP-00023 (Orlando): missing scan and missed window |
| Unknown shipment | SHP-99999 (doesn't exist) |
| Customer procedure mismatch | Coastal Kitchen Supply has no failed-attempt SOP (defined when SOPs are written) |

**Demo focus:** filtering to Tampa shows 4 exception shipments (SHP-00007, SHP-00031, SHP-00052, SHP-00078), including the unavailable-ETA and contradictory-notes scenarios.

`ingestion/tests/test_seed.py` checks the counts, the exact planted flags, the clean cohort, the trust scenarios, that no record postdates the demo clock, and that reseeding produces identical data.
