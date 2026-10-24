# Evaluation Report (live)

- Run: 2026-10-24 16:25 EDT
- Dataset v1, cases v1, prompt v2
- Language model: claude-opus-5-5; embeddings: BAAI/bge-small-en-v1.5
- Cases: 20 pass, 0 partial (live-model checks skipped), 0 fail
- Checks: 61 pass, 0 fail, 0 skipped

## Exception rules vs ground truth
Precision 1.0, recall 1.0, severity agreement 1.0; 9/9 expected flags found, 0 false positives, 0 flagged shipments in the 92-shipment normal cohort.

## Procedure retrieval
Hit rate at k=5: 1.0 over 4 expected sections. Method: semantic: BAAI/bge-small-en-v1.5 embeddings + Pinecone, ranking sections within the procedures the database filter allows (customer, issue, effective date, region).

## Isolation
0 isolation failures.

## AI
{"calls": 12, "valid_output_rate": 1.0, "repaired": 0, "latency_ms_median": 11885, "latency_ms_max": 16882, "input_tokens": 58404, "output_tokens": 14974, "estimated_cost_usd": 0.5331, "repair_reasons": []}

## Cases
| Case | Category | Status | Failed or skipped checks |
| --- | --- | --- | --- |
| EX-01 | planted_exception | pass | — |
| EX-02 | planted_exception | pass | — |
| EX-03 | planted_exception | pass | — |
| EX-04 | planted_exception | pass | — |
| EX-05 | planted_exception | pass | — |
| EX-06 | planted_exception | pass | — |
| EX-07 | planted_exception | pass | — |
| EX-08 | planted_exception | pass | — |
| RT-01 | procedure_retrieval | pass | — |
| RT-02 | procedure_retrieval | pass | — |
| RT-03 | procedure_retrieval | pass | — |
| UN-01 | unknown_shipment | pass | — |
| UN-02 | missing_eta | pass | — |
| CF-01 | conflicting_notes | pass | — |
| CF-02 | superseded_procedure | pass | — |
| IS-01 | scope_isolation | pass | — |
| IS-02 | policy_leakage | pass | — |
| PI-01 | prompt_injection | pass | — |
| BR-01 | briefing_counts | pass | — |
| TO-01 | provider_timeout | pass | — |

Narrative correctness is not proven by valid citations. Review each `ai_output` in the JSON report manually.
