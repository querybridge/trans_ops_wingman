# Transportation Operations Wingman — Claude Code Build Brief

## Start here

Act as a senior AI engineer and pragmatic product developer. Build the working application described below, not just a plan. Inspect the repository and any applicable project instructions first. Reuse a suitable existing Django foundation when present; otherwise create a small standalone Django project. Preserve unrelated files. Make routine implementation decisions autonomously, record tradeoffs, and continue through local verification. Ask only for missing credentials or choices that genuinely block progress. Never expose secrets. Do not deploy publicly, incur new paid subscriptions, or connect to real company systems without explicit authorization.

The builder is Sherman Distin, an experienced analytics and marketing technology leader with Python, Django, SQL, dashboards, data governance, and business problem-solving experience. The deadline is Sunday night, October 25, 2026, after a Friday–Sunday build. Budget approximately 20–25 focused development hours. Deliver the smallest complete, credible product within that limit.

## Why this project exists

Demonstrate to Yzer Next's CIO that Sherman can identify an operational problem, connect disparate information, implement useful AI, and ship a reliable prototype as an initial one-person engineering function.

Interview context supplied by Sherman:

- The CIO's twelve-month priorities include TMS integration and creating efficiency.
- Managers and department leaders spend time pulling information from disconnected sources.
- Success means making stakeholders' lives easier through useful solutions.
- Additional team investment depends on proving value first.

Yzer operates transportation and delivery services. This prototype uses a fictional regional last-mile operation. It is an independent demonstration, not an official Yzer product, and does not imply access to Yzer systems, procedures, or confidential data.

## CIO-facing goals and evidence

| Goal | Evidence the product must show |
| --- | --- |
| Reduce information gathering | One screen combines shipment facts, dispatch notes, and relevant procedures. |
| Demonstrate a path to TMS integration | A documented canonical shipment schema and CSV adapter isolate source formats from application logic. |
| Improve manager decisions | Every flagged shipment has a reason, evidence, next action, and proposed responsible role. |
| Engineer trustworthy AI | Deterministic calculations, source citations, validated outputs, and explicit handling of unknowns. |
| Show solo execution ability | Working deployment instructions, repeatable data setup, meaningful tests, evaluation results, and a short demo. |
| Make investment measurable | Report observed task time, model latency, estimated API cost, and evaluation accuracy without inventing ROI. |

Desired CIO takeaway: “Sherman can translate an operational need into a working system, understand integration constraints, and prove value before asking for a team.” Do not put hiring language in the product UI. Let the usefulness and engineering evidence make that case.

## Product promise

“See which deliveries need attention, understand the evidence, and prepare the next action without searching several systems.”

Primary user: a regional operations manager. Three primary workflows only:

1. **Find exceptions:** choose customer, region, and demo date; see a prioritized exception list.
2. **Explain shipment:** select a shipment; see its timeline, notes, applicable SOP excerpts, and an evidence-backed explanation.
3. **Create manager briefing:** summarize the current filtered exception list with counts, proposed actions, and source links.

Optional only after all acceptance criteria pass: draft an individual customer update. Drafts must remain unsent.

## Scope boundaries

Build a decision-support prototype. Do not build route optimization, predictive ETA models, autonomous dispatch, live GPS, a full TMS, arbitrary SQL chat, email integrations, a multi-agent system, model fine-tuning, or a complex JavaScript frontend. Do not claim predicted lateness when the app only detects rule-based exceptions. No operational writeback or automated communication.

## Required technology and meaningful roles

| Technology | Responsibility |
| --- | --- |
| Python + Django | Application, ORM, validation, templates, and admin. |
| HTMX | Small interactions and loading states; plain Django forms are acceptable if faster. |
| SQLite | Structured shipments, events, notes, ingestion records, and evaluation runs. |
| LangChain | A bounded workflow connecting tools, retrieval, prompts, and model calls. |
| Pinecone | Semantic retrieval over SOP chunks and dispatch-note text with metadata filters. |
| Hugging Face Inference Providers | Hosted embeddings using a currently available model; verify access before implementation. |
| Hosted LLM | Evidence-backed explanations and briefing generation. Use an available provider through a small adapter. |
| Pydantic | Validate generated structured responses and tool inputs. |
| LangSmith | Trace retrieval/model steps and support evaluation when credentials are available. |

Verify current official SDK documentation and PythonAnywhere compatibility before pinning dependencies. Do not assume a specific model is served just because it exists on Hugging Face. Use the same embedding model and dimensions for ingestion and queries; store model metadata and reject incompatible indexes. Keep large models and GPU dependencies off the web host.

Prefer explicit, inspectable orchestration. A workflow that calls typed tools is sufficient; an open-ended autonomous agent is unnecessary. Do not add frameworks just to increase the tool count.

## Architecture

Separate these concerns:

- `ingestion/`: CSV adapter, validation, normalization, deterministic seed generation.
- `operations/`: ORM models, exception rules, query functions, evidence assembly.
- `ai/`: embedding client, Pinecone retrieval, LLM adapter, prompts, output schemas, tracing.
- `web/`: views, templates, filters, evidence drawer, and evaluation display.
- `evaluation/`: versioned fixtures, expected answers, scoring, and exported results.

These are logical boundaries; adapt directory names to Django conventions.

Request flow:

1. Validate requested customer, region, shipment, and date.
2. Query structured facts through allowlisted ORM tools.
3. Calculate exception flags and counts in Python/SQL.
4. Retrieve relevant SOPs using customer, issue type, effective date, and region where appropriate. Retrieve shipment notes with exact shipment/customer filters; their database records remain authoritative.
5. Assemble a bounded evidence package with stable IDs.
6. Generate a Pydantic-validated explanation or briefing through LangChain.
7. Check cited IDs against supplied evidence and display the result with source links.

Do not use semantic search as the source of truth for shipment status, timestamps, or counts. Do not send an entire database to the model. Unknown facts must remain unknown.

## Synthetic dataset and repeatability

Use a deterministic random seed and a fixed timezone-aware demo timestamp, displayed prominently. Do not depend on the real current clock, since the demo must remain reproducible after Sunday.

Create:

- 100 shipments across three fictional customers and Tampa, Orlando, and Jacksonville.
- 30 dispatch notes with explicit timestamps and source IDs.
- Five short fictional SOP documents covering missed delivery windows, failed attempts, missing scans, POD requirements, and escalation ownership.
- Eight deliberately planted exception shipments with a ground-truth manifest. Other shipments should be clean under the configured rules.
- At least one unknown shipment, one unavailable ETA, one contradictory note pair, and one customer-specific procedure mismatch scenario in evaluation fixtures.

Use fictional operational details, never real patient/customer/driver data. For the first version, use ordinary retail deliveries rather than regulated clinical scenarios.

Canonical shipment fields: shipment_id, customer_id, region, service_type, delivery_window_start, delivery_window_end, status, latest_event_at, delivered_at, assigned_role, source_system, source_record_id, imported_at. Keep event and note tables separate. Include timezone offsets. ETA is optional and nullable; do not infer it without a source.

SOP chunk metadata: document_id, chunk_id, customer_id or explicit shared scope, issue_type, version, effective_from, effective_to if applicable, source_title, section, and region if applicable. A missing matching customer procedure must not silently select another customer's policy.

Provide idempotent commands to seed the database, import a sample CSV, ingest documents/notes, and reset demo state. Use stable vector IDs so reingestion does not duplicate content.

## Deterministic exception rules

Document exact rules and test boundaries:

- **Missed window:** not delivered/cancelled and demo timestamp exceeds delivery_window_end.
- **Missing scan:** active shipment has no qualifying scan within a configurable threshold for its status.
- **Failed attempt:** latest authoritative event indicates delivery attempted but unsuccessful, with no subsequent successful delivery.
- **Missing POD:** delivered shipment lacks required proof of delivery, after any configured grace period.

Prioritize with transparent rule-based severity and age. Show the reason and threshold used. Distinguish a shipment count from an exception count because one shipment may have multiple flags. Never label severity as a learned probability.

## AI tools and output contract

Expose typed, read-only tools such as:

- `list_exceptions(customer_id, region, as_of)`
- `get_shipment(shipment_id, customer_id)`
- `get_shipment_events(shipment_id, customer_id)`
- `get_dispatch_notes(shipment_id, customer_id)`
- `retrieve_procedure(customer_id, issue_type, region, as_of)`

Customer scope must come from validated application context and be enforced inside tools, not merely trusted from a model-generated argument. No arbitrary SQL or model-supplied file paths.

Generated output should include summary, shipment_id where applicable, issue category, evidence references, recommended next action, proposed responsible role, missing information, and requires_review. Separate observed facts from suggestions. Avoid unsupported numerical confidence scores.

Validate schema and references. Allow at most one repair attempt for malformed output; otherwise return a useful deterministic evidence view with a clear AI-unavailable state. If the evidence is contradictory, display the conflict and request verification. Cite facts with clickable shipment/event/note IDs and procedures with document/version/section references. Do not fabricate SOPs, ETAs, diagnoses, actions already taken, or delivery commitments.

Treat retrieved text as untrusted data, never as instructions. Include a malicious dispatch note in evaluation to verify that it cannot override instructions or trigger unrelated tools.

## Interface

Use a restrained operations-dashboard style: clear typography, readable tables, neutral colors, and purposeful severity badges. No decorative maps or animations that displace the core workflow.

Main screen:

- Title: Transportation Operations Wingman.
- Visible “Prototype - Synthetic data - For Demo Only” label and fixed demo timestamp.
- Customer and region filters.
- Four compact metrics: shipments, shipments needing attention, missed windows, missing POD.
- Exception table with shipment, customer, issue, severity reason, age, and details action.
- Shipment detail panel with event timeline, facts, notes, explanation, and source excerpts.
- Generate Briefing button with loading, error, and retry states.

Provide suggested actions as reviewable recommendations. Avoid technology names and hiring claims in the manager workflow. Put the product promise, user workflow, architecture, dependency versions, limitations, and evaluation details on a Demo Documentation page linked from the footer. That link is intentionally off brand (bold red) so the CIO notices and reviews it.

## Evaluation and tests

Create 20 versioned evaluation cases with expected facts and source IDs:

| Cases | Coverage |
| --- | --- |
| 8 | Each planted exception is detected and explained correctly. |
| 3 | Correct customer and issue-specific SOP retrieval. |
| 2 | Unknown shipment and missing ETA produce honest unknowns. |
| 2 | Conflicting notes and stale/superseded procedures. |
| 2 | Customer-scope isolation and prevention of policy leakage. |
| 1 | Prompt injection inside a retrieved note. |
| 1 | Accurate filtered briefing counts and valid references. |
| 1 | Provider timeout produces a usable degraded response. |

Measure rule precision/recall against ground truth, retrieval hit rate at a stated k, citation validity, factual correctness, schema validity, and latency. Use deterministic assertions for facts and counts; manually inspect or separately judge narrative correctness rather than assuming valid citations prove support. Include a few normal shipments to measure false positives. Record actual results, model and embedding identifiers, prompt version, run date, and dataset version.

Targets, not preclaimed results: all planted exceptions detected; zero false positives in the seeded normal cohort; all cited IDs valid; no cross-customer leakage; unknowns never invented. Correct critical factual or isolation failures before cosmetic work. Show failed cases honestly if unresolved.

Track per-request latency and token usage where available. Estimate model/embedding cost only from documented current rates and usage; label estimates and exclude unsupported charges. Never hardcode impressive accuracy, savings, or ROI.

Use meaningful unit tests for rule boundaries, import validation, scoping, and citation validation, plus an integration smoke test. Keep offline/mock tests distinct from live-provider evaluation. A fixture response is not evidence that Pinecone or model integration works.

## PythonAnywhere deployment

Target a conventional Django WSGI application on a paid PythonAnywhere account, using hosted inference APIs. Verify outbound connectivity early; free accounts have allowlist restrictions. Avoid WebSockets, local model serving, Docker, and background-worker dependencies for the MVP. Use Python 3.12 both locally (the `.yzer` virtualenv) and on PythonAnywhere (the `innit` system image).

Pre-ingest vectors with a management command. Bound network calls with timeouts and limited retries. Keep normal requests short; do not launch unmanaged threads inside web views. If processing requires a job queue, document it as future work rather than expanding weekend scope.

Provide `.env.example` with placeholders (real values live in a git-ignored `.env`; see `SETUP_CREDENTIALS.md`), pinned compatible dependencies, WSGI configuration guidance, static-file setup, migrations, seed/ingest commands, and a deployment smoke checklist. Configuration should cover Django secret/hosts/debug, Pinecone index/key, Hugging Face token/model, LLM provider/model/key, and optional LangSmith settings. Do not commit credentials, databases with real information, or trace payloads containing secrets. Use Django CSRF protection and escaped templates; sanitize model output before rendering. Restrict write/admin actions and apply request limits to costly endpoints.

Access control uses Django's built-in authentication, not PythonAnywhere's web-app password protection (leave that off). Require login on every view. Keep a non-staff demo user for the walkthrough separate from the Django admin superuser. Create passwords interactively; never embed a real password in the repository, fixtures, or `.env.example`. Use the database cache backend for rate limiting so limits hold across PythonAnywhere worker processes. Missing provider configuration must show an honest status, not silently substitute fake AI results.

## Three-day delivery plan

### Friday, October 23 — prove the integration path (7–8 hours)

1. Inspect repository; write a short implementation checklist and choose supported dependency/model versions.
2. Test Hugging Face embedding, Pinecone upsert/query, and one LLM call immediately. Confirm deployment connectivity before investing in UI.
3. Build schema, deterministic data, importer, and exception rules.
4. Ingest SOPs and notes; demonstrate a source-filtered retrieval.
5. Produce one complete shipment explanation through real integrations.

Friday exit: a vertical slice works. If any provider is unavailable, surface the blocker and choose the smallest documented alternative; record what changed and why.

### Saturday, October 24 — complete the manager workflows (8–9 hours)

1. Build exception list and shipment details with evidence links.
2. Implement bounded LangChain workflow and Pydantic validation.
3. Add briefing generation with deterministic totals.
4. Add unknown/conflict handling, scoped retrieval, and traces.
5. Deploy a rough version if access is available; run smoke tests.

Saturday exit: all three workflows function and core failure cases are handled.

### Sunday, October 25 — prove reliability and prepare the demonstration (5–8 hours)

1. Run tests and the 20-case evaluation; fix substantive failures.
2. Polish states, readability, and source evidence.
3. Verify deployed behavior and record actual measurements.
4. Finish README, architecture notes, evaluation report, and demo script.
5. Rehearse and record a three-minute walkthrough manually if recording tools are unavailable.

Scope cuts in order: free-form chat, customer-message drafting, elaborate styling, extra metrics. Preserve the real retrieval path, factual accuracy, exception list, one explanation, briefing, and evidence.

## Three-minute CIO demonstration

- **0:00–0:25 — Problem:** “A manager should not need to reconcile a shipment export, dispatch notes, and a procedure folder just to know what needs attention.”
- **0:25–1:05 — Find:** Filter to Tampa and show the exception queue. Explain that counts and deadlines come from deterministic rules.
- **1:05–1:50 — Explain:** Open one shipment. Show the event timeline, a relevant dispatch note, the matching customer SOP, and a cited recommended action.
- **1:50–2:15 — Trust:** Show an unavailable ETA or conflicting note. The system identifies the gap rather than inventing an answer.
- **2:15–2:40 — Brief:** Generate a manager briefing from the same evidence.
- **2:40–3:00 — Hiring relevance:** “This is a prototype using synthetic data. The next step would be validating a narrow workflow with one manager and connecting a read-only TMS export or API. I would measure accuracy, adoption, and preparation time before expanding it.”

Have a few screenshots and a clearly labeled prerecorded walkthrough available if connectivity fails. Never present a recording, cached answer, or fixture as a live model call.

## Business value validation

Measure the same task manually and with the prototype on the same synthetic scenario. Report sample size and timings, and acknowledge the artificial dataset and small sample. Use a transparent scenario calculator only if useful:

`potential weekly hours saved = managers × briefings per week × observed minutes saved / 60`

All inputs must be visible and editable. This is an illustrative opportunity estimate, not verified Yzer savings. Do not claim that a synthetic benchmark establishes production ROI.

## Final deliverables and definition of done

- Runnable Django project with all three workflows.
- Deterministic synthetic dataset, ground truth, and idempotent import/ingestion commands.
- Working LangChain + Pinecone + hosted Hugging Face embedding integration and LLM generation, or explicit documentation of any incomplete integration.
- Validated answers with source links and useful unknown/failure states.
- Meaningful tests and a reproducible 20-case evaluation with actual results.
- README covering local setup, environment configuration, commands, and PythonAnywhere deployment.
- Architecture/tradeoff notes showing what changes when connecting a real TMS.
- Demo script and short CIO-facing project summary focused on operational value.
- Clear limitations: synthetic data, no real TMS integration, no predictive ETA, no operational actions, and no production readiness claim.

At completion, report what works, commands executed, actual test/evaluation results, deployment status, remaining blockers, and the next smallest real-world pilot. Never describe an unrun test, unverified deployment, or assumed integration as completed.

## Official references to verify during implementation

- Yzer Next: https://www.yzernext.com/
- Pinecone/LangChain: https://docs.pinecone.io/integrations/langchain
- Hugging Face hosted embeddings: https://huggingface.co/docs/inference-providers/tasks/feature-extraction
- Hugging Face provider availability: https://huggingface.co/docs/inference-providers/index
- LangSmith evaluation: https://docs.langchain.com/langsmith/evaluation-types
- PythonAnywhere outbound access: https://help.pythonanywhere.com/pages/403ForbiddenError/
- PythonAnywhere asynchronous work: https://help.pythonanywhere.com/pages/AsyncInWebApps/

## Instruction to begin

Read this entire brief and the repository instructions. Implement the Friday vertical slice first, then continue through the remaining milestones. Keep a short progress checklist in the repository and update it at meaningful checkpoints. Prefer a complete, reliable narrow workflow over additional features. If credentials block live integration, finish independently testable work, state exactly what is blocked, and provide the precise next command or configuration required.
