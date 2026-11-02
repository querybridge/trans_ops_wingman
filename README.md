# Transportation Operations Wingman

Decision-support prototype for regional delivery operations, built with synthetic data. Live demo (sign-in required): https://opswingman-querybridge.pythonanywhere.com/ Start with `docs/project_summary.md` for what it does and how it performed, and `docs/demo_script.md` for the 3-minute walkthrough. `SETUP_CREDENTIALS.md` covers provider accounts, and `BRAND_GUIDE.md` covers visual standards.

## Status

As of Nov 2, 2026, the prototype is complete, deployed, and working end to end.

| Area | State |
| --- | --- |
| Deployment | Live on PythonAnywhere over HTTPS since Oct 24, 2026. `smoke_check --network` passes every check. |
| Data | 100 synthetic shipments, events, and notes, plus five SOP procedures in six versions (`docs/synthetic_dataset.md`). No real company data or systems are connected. |
| Exception rules | Missed window, missing scan, failed attempt, missing proof of delivery, and the missed-window escalation trigger. Plain, tested Python (`docs/exception_rules.md`). |
| Ingestion | CSV adapter with validation and a sample TMS export (`docs/tms_integration.md`). |
| AI | Live. Provider keys for Anthropic, Hugging Face, Pinecone, and LangSmith are configured locally and on the server, in `.env` only. Explanations come from Claude via LangChain. Procedure sections are ranked by Hugging Face embeddings in Pinecone, only within the procedures the database allows, and traced in LangSmith. Every answer is schema-checked and citation-checked, with one repair attempt (`docs/ai_architecture.md`). |
| Evaluation | The latest live run passed 20 of 20 cases (63 of 63 checks) with no repairs, a median of 12 s per call, and an estimated $0.55 per run (`evaluation/reports/latest_live.md`). The same result was reproduced on the deployed server. The offline run also passes (`evaluation/reports/latest_offline.md`). |
| Screens | Worklist (home), Exceptions, Shipment Detail, Manager Briefing, Settings, Demo Documentation, and Technology Map. |
| Tests | 128 automated tests pass. Provider keys are blanked during tests, so no test makes a paid AI call. |
| Safeguards | Django sign-in on every page. AI requests are limited to 20 per user per 10 minutes. If a provider key is ever removed, the app shows an honest "not configured" status rather than a stand-in answer. |

If the provider keys were removed, everything except the AI output would still work: the rules, Worklist steps, Exceptions queue, CSV import, and the offline evaluation.

## User Workflow

1. **Sign in.** Every page requires a Django account. After signing in, the user lands on the Worklist.
2. **Set defaults once (optional).** Open the username menu → **Settings** and choose default regions and urgency levels, for example Tampa with Critical and Warning. With no regions chosen, all regions are shown. Until defaults are changed, the Worklist shows Critical only.
3. **Work the Worklist.** Each card is a flagged delivery, worst first, with:
   - **Why It Failed:** the rule that fired and its reason, the last scan event, the ETA, and the field notes quoted as written.
   - **What to Do:** action steps and the owner, quoted from that customer's procedure with a citation for each. If no procedure is on file, the card says so rather than borrowing another customer's.
   - **When to Escalate:** the time the delivery must arrive by, or "Escalation due" once it's more than 2 hours past the window, plus the escalation procedure.
   The filters at the top change the view for the moment. **Back to my defaults** returns to the saved settings.
4. **Ask Wingman (optional).** **Get Wingman Recommendation** on a card, or **Get All Recommendations** for every card, adds an AI-generated next step and proposed owner. Each one cites the evidence it used and is checked before it's shown. It's labeled for review: the manager decides.
5. **Check the evidence.** **Full Evidence →** (or any citation link) opens Shipment Detail with the facts, timeline, notes, procedures, and a cited AI explanation on request.
6. **Review the whole queue.** **Exceptions** lists every flag with its rule, threshold, and age, filtered by customer and region, and can generate a cited Manager Briefing whose counts must match the rules exactly.
7. **Learn the system.** Demo Documentation explains the data and rules. Its Integrations section links to the Technology Map, where hovering over a component shows what it does.

## Directory Tree

Git-ignored files (`.env`, `db.sqlite3`, `.yzer/`, `staticfiles/`, and evaluation run payloads) are kept out of the repository.

```text
trans_ops_wingman/
├── manage.py                  Django command-line entry point
├── requirements.txt           Pinned Python dependencies
├── .env.example               Placeholder settings; copy to .env (never committed)
├── BRAND_GUIDE.md             Colors, type, and component standards
├── SETUP_CREDENTIALS.md       How to create and configure provider accounts
├── config/                    Project settings, root URLs, WSGI/ASGI, and the offline test runner
├── deploy/                    PythonAnywhere WSGI file template (no secrets)
├── docs/                      Project summary, demo script, AI architecture, rules, dataset, TMS integration, deployment
├── operations/                Core domain: customers, shipments, events, notes, procedures; exception rules and query services
├── ingestion/                 Getting data in: CSV adapter and validation, procedure ingestion, seeding, management commands
│   ├── management/commands/   seed_demo, reset_demo, import_shipments_csv, ingest_procedures, ingest_vectors, create_demo_user, smoke_check
│   └── samples/               Sample TMS export for trying the CSV import
├── procedures/                SOP Markdown files (missed window, missing scan, failed attempt, proof of delivery, escalation)
├── ai/                        AI layer: provider status, scoped tools, evidence packages, prompts, schemas, Claude adapter, embeddings, Pinecone, validation and repair
├── evaluation/                20-case evaluation harness
│   ├── fixtures/              Versioned cases and ground truth
│   ├── management/commands/   run_evaluation (offline or --live)
│   └── reports/               Curated offline and live reports
├── web/                       User-facing app: views, forms, URLs, per-user settings, rate limiting, Technology Map layout
│   └── templates/web/         Page templates; partials/ holds the HTMX fragments
├── templates/                 Site-wide base layout, sign-in page, and 404/500 pages
└── static/                    Stylesheet (css/) and vendored HTMX (js/)
```

Each Django app keeps its tests in its own `tests/` folder and its schema changes in `migrations/`.

## Local Setup

```bash
/Users/querybridge/.local/bin/python3.12 -m venv .yzer   # Python 3.12
.yzer/bin/pip install -r requirements.txt
cp .env.example .env        # set DJANGO_SECRET_KEY; DJANGO_DEBUG=true for local work
.yzer/bin/python manage.py migrate
.yzer/bin/python manage.py createcachetable
.yzer/bin/python manage.py createsuperuser
.yzer/bin/python manage.py seed_demo          # deterministic synthetic data + SOP procedures
.yzer/bin/python manage.py runserver
```

Every page requires login (Django authentication). Django admin is at `/admin/`.

## Tests

```bash
.yzer/bin/python manage.py test
```

## Other Commands

```bash
.yzer/bin/python manage.py ingest_procedures                      # reload procedures/*.md
.yzer/bin/python manage.py ingest_vectors [--create-index]        # embed procedure sections into Pinecone
.yzer/bin/python manage.py import_shipments_csv <file> --dry-run  # validate a TMS CSV export
.yzer/bin/python manage.py reset_demo --yes                       # wipe and reseed (keeps users)
.yzer/bin/python manage.py run_evaluation [--live]                # 20-case evaluation; report in evaluation/reports/
.yzer/bin/python manage.py create_demo_user demo                  # non-staff walkthrough account (prompts for password)
.yzer/bin/python manage.py smoke_check --network                  # deployment checks
```

## Deployment

See `docs/deployment_pythonanywhere.md`. To update the live site: `git pull`, `migrate`, `collectstatic`, then Reload on the Web tab.
