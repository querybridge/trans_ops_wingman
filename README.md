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

## Status

Skeleton only: the exception rules, seed data, retrieval, and AI workflow are not implemented yet. The UI shows honest "not connected" states instead of placeholder results.
