# Transportation Operations Wingman

Decision-support prototype for regional delivery operations, built with synthetic data. See `Transportation_Operations_Wingman_Brief.md` for scope, `SETUP_CREDENTIALS.md` for provider accounts, and `BRAND_GUIDE.md` for visual standards.

## Local setup

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

## Layout

| App | Responsibility |
| --- | --- |
| `operations` | Canonical shipment, event, and note models; query services; exception rules |
| `ingestion` | CSV adapter, validation, seed and import commands, ingestion records |
| `ai` | Provider status; later embeddings, retrieval, LLM adapter, prompts, schemas |
| `evaluation` | Versioned evaluation cases and recorded runs |
| `web` | Views, templates, filters, and HTMX partials |

## Other commands

```bash
.yzer/bin/python manage.py ingest_procedures                      # reload procedures/*.md
.yzer/bin/python manage.py import_shipments_csv <file> --dry-run  # validate a TMS CSV export
.yzer/bin/python manage.py reset_demo --yes                       # wipe and reseed (keeps users)
```

## Status

Working without provider credentials: synthetic dataset (`docs/synthetic_dataset.md`), exception rules (`docs/exception_rules.md`), CSV import (`docs/tms_integration.md`), SOP procedures with scoped database retrieval, and the AI tools, evidence packages, validation, and repair/degrade workflow (`docs/ai_architecture.md`), tested with a scripted test double.

Waiting on credentials: the live LLM adapter and LangChain wiring, Hugging Face embeddings, Pinecone retrieval, and LangSmith tracing. Until then the UI shows honest "not configured" states.
