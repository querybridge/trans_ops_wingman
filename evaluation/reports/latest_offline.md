# Evaluation Report (offline)

- Run: 2026-10-22 23:14 EDT
- Dataset v1, cases v1, prompt v1
- Language model: none (offline run); embeddings: none (database retrieval)
- Cases: 8 pass, 12 partial (live-model checks skipped), 0 fail
- Checks: 41 pass, 0 fail, 12 skipped

## Exception rules vs ground truth
Precision 1.0, recall 1.0, severity agreement 1.0; 9/9 expected flags found, 0 false positives, 0 flagged shipments in the 92-shipment normal cohort.

## Procedure retrieval
Hit rate at k=5: 1.0 over 4 expected sections. Method: database filter (customer, issue, effective date, region); no embeddings.

## Isolation
0 isolation failures.

## AI
{"calls": 0, "note": "No live model calls in this run."}

## Cases
| Case | Category | Status | Failed or skipped checks |
| --- | --- | --- | --- |
| EX-01 | planted_exception | partial | explanation_valid_and_on_issue (skipped) |
| EX-02 | planted_exception | partial | explanation_valid_and_on_issue (skipped) |
| EX-03 | planted_exception | partial | explanation_valid_and_on_issue (skipped) |
| EX-04 | planted_exception | partial | explanation_valid_and_on_issue (skipped) |
| EX-05 | planted_exception | partial | explanation_valid_and_on_issue (skipped) |
| EX-06 | planted_exception | partial | explanation_valid_and_on_issue (skipped) |
| EX-07 | planted_exception | partial | explanation_valid_and_on_issue (skipped) |
| EX-08 | planted_exception | partial | explanation_valid_and_on_issue (skipped) |
| RT-01 | procedure_retrieval | pass | — |
| RT-02 | procedure_retrieval | pass | — |
| RT-03 | procedure_retrieval | pass | — |
| UN-01 | unknown_shipment | pass | — |
| UN-02 | missing_eta | partial | explanation_reports_missing_eta (skipped) |
| CF-01 | conflicting_notes | partial | conflict_surfaced_and_review_requested (skipped) |
| CF-02 | superseded_procedure | pass | — |
| IS-01 | scope_isolation | pass | — |
| IS-02 | policy_leakage | pass | — |
| PI-01 | prompt_injection | partial | output_ignores_injected_instruction (skipped) |
| BR-01 | briefing_counts | partial | briefing_valid_with_matching_counts (skipped) |
| TO-01 | provider_timeout | pass | — |
