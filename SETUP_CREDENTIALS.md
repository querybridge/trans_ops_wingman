# Transportation Operations Wingman: Accounts, Credentials, and Costs

This guide covers every external account Transportation Operations Wingman needs, how to get each credential, how to check it works, and what it costs. Prices were checked on **2026-10-22** from each vendor's public pricing page. Re-check them before quoting any number in the demo.

All values go into a local `.env` file copied from `.env.example`. `.env` is git-ignored, so never commit it. On PythonAnywhere, keep a separate `.env` in the project directory and load it from the WSGI file.

## Cost summary

| Service | Plan to use | Fixed cost | Usage cost for this project | Watch out for |
| --- | --- | --- | --- | --- |
| PythonAnywhere | Existing paid account | Already paid | $0 extra | Use the `innit` system image so Python 3.12 is available |
| Pinecone | Starter (free) | $0 | $0 within free limits | Starter only offers AWS `us-east-1`; Standard has a $50/month minimum |
| Hugging Face | Free account plus purchased credits, **or** PRO | Free: $0. PRO: $9/month | A few cents of CPU time for this dataset | **Free accounts no longer get any included credits.** You must buy credits or subscribe to PRO before any API call |
| LLM (Anthropic Claude API) | Pay-as-you-go prepaid credits | $0 | Roughly $5–$30 for the weekend at Opus 5.5 rates (see the estimate) | Prepaid balance needed; set a spend limit |
| LangSmith | Developer (free) | $0 | $0 up to 5,000 traces/month | Overage rates are listed inconsistently; base traces are kept only 14 days |

**Expected new spend for the weekend:** about **$10–$40** in total. Most of it is LLM usage, plus either a small HF credit purchase or a $9 HF PRO month. None of these is a new recurring subscription unless you pick HF PRO. If you do, cancel it after the demo if it isn't needed.

---

## 1. Pinecone (semantic retrieval)

### Set up
1. Sign up at https://app.pinecone.io (the free Starter plan needs no card).
2. Use the default project. Go to **API Keys → Create API key** and name it `ops-wingman-dev`.
3. Put it in `.env` as `PINECONE_API_KEY`.
4. Don't create the index by hand. The ingest management command creates `PINECONE_INDEX_NAME` as a **serverless index on `aws` / `us-east-1`** with:
   - `dimension` = `EMBEDDING_DIMENSIONS`, which must equal the HF embedding model's output size (384 for `BAAI/bge-small-en-v1.5`)
   - `metric` = `cosine`

### Check it works
```bash
.yzer/bin/pip install pinecone python-dotenv
.yzer/bin/python -c "
from dotenv import load_dotenv; load_dotenv()
import os; from pinecone import Pinecone
print(Pinecone(api_key=os.environ['PINECONE_API_KEY']).list_indexes())"
```

### Costs (Starter plan)
- $0. Includes up to 2 GB storage, 2M write units/month, 1M read units/month, 1 GB egress, and 5 indexes. Limited to 1 project, 2 users, and AWS `us-east-1` only. There are no backups.
- This project's data (5 SOPs plus 30 notes, a few hundred vectors) is a tiny fraction of those limits.
- Standard costs $50/month minimum, then storage at $0.33/GB/month, write units at $4–4.50 per million and read units at $16–18 per million. **You don't need it.**

### Gotchas
- Metadata can't contain `null`. Leave out `effective_to` when it doesn't apply.
- Range filters need numbers, so store dates as epoch integers.
- Newly upserted vectors take a moment to become searchable. Ingest commands and tests should wait and retry.
- Install the `pinecone` package. `pinecone-client` is deprecated.

---

## 2. Hugging Face Inference Providers (embeddings)

### Set up
1. Sign up at https://huggingface.co/join.
2. **Pay for usage before testing.** Free accounts have *no* included Inference Providers credits. Pick one option:
   - **Option A (cheapest):** buy a small amount of pay-as-you-go credit at https://huggingface.co/settings/billing.
   - **Option B:** subscribe to PRO at **$9/month**, which includes **$2/month** of compute credit. That's more than enough for this project. Cancel after the demo if it isn't needed.
3. Go to **Settings → Access Tokens → Create new token** and choose type **Fine-grained**. Enable only **"Make calls to Inference Providers"**. Name it `ops-wingman`.
4. Put it in `.env` as `HF_TOKEN`.
5. Choose an embedding model that the `hf-inference` provider actually serves. Start with `BAAI/bge-small-en-v1.5` (384 dimensions). If it isn't served, try `sentence-transformers/all-MiniLM-L6-v2` (also 384). Confirm on the model page that the "Inference Providers" widget lists HF Inference for **Feature Extraction**.

### Check it works (also confirms the dimension)
```bash
.yzer/bin/pip install huggingface_hub python-dotenv
.yzer/bin/python -c "
from dotenv import load_dotenv; load_dotenv()
import os; from huggingface_hub import InferenceClient
c = InferenceClient(provider=os.environ['HF_EMBEDDING_PROVIDER'], api_key=os.environ['HF_TOKEN'])
v = c.feature_extraction('missed delivery window', model=os.environ['HF_EMBEDDING_MODEL'])
print(getattr(v, 'shape', len(v)))"
```
The last number printed must equal `EMBEDDING_DIMENSIONS`. If you get a 402 error, there is no credit (step 2). A 404 or "not supported" error means the provider doesn't serve that model (step 5).

### Costs
- `hf-inference` bills **compute time × hardware price**. Embedding models run on CPU, so a few hundred short chunks plus query embeddings should cost well under $1.
- HF passes provider rates through with no markup. You can see usage at https://huggingface.co/settings/inference-providers/overview.
- Per-request dollar cost is **not** returned in API responses. The app's cost report should label embedding cost as an estimate based on billing-page totals, not a per-call figure.

---

## 3. Hosted LLM: Anthropic Claude API (recommended)

The brief asks for "an available provider through a small adapter." Anthropic's Claude API is the default here. `LLM_PROVIDER`/`LLM_MODEL` keep this swappable.

### Set up
1. Sign up at https://console.anthropic.com.
2. Go to **Billing** and add prepaid credits (start small). **Set a monthly spend limit** under Limits.
3. Create a workspace named `ops-wingman` (optional; useful for separate limits and usage reports).
4. Go to **API Keys → Create Key** in that workspace and put it in `.env` as `ANTHROPIC_API_KEY`.

### Check it works
```bash
.yzer/bin/pip install anthropic python-dotenv
.yzer/bin/python -c "
from dotenv import load_dotenv; load_dotenv()
import anthropic
r = anthropic.Anthropic().messages.create(model='claude-opus-5-5', max_tokens=256,
    messages=[{'role':'user','content':'Reply with the single word: ready'}])
print(r.content[-1].text, r.usage)"
```

### Costs (per million tokens, Anthropic first-party rates)

| Model | Model ID | Input | Output | Notes |
| --- | --- | --- | --- | --- |
| Claude Opus 5.5 | `claude-opus-5-5` | $4.00 | $20.00 | Default. Cached input reads cost $0.20 |
| Claude Sonnet 5.5 | `claude-sonnet-5-5` | $2.00 | $10.00 | Cached input reads cost $0.20 |
| Claude Haiku 5.5 | `claude-haiku-5-5` | $0.10 | $0.50 | Prompts up to 100K tokens; $0.50 / $2.50 above that |

**Rough estimate:** an explanation or briefing call uses about 6K input tokens of evidence and about 1.5K output tokens, including thinking. On Opus 5.5 that's about **$0.05 per call**. Expect around 200–500 calls across development, the 20-case evaluation (run several times) and rehearsals, so roughly **$10–$25**. On Haiku 5.5 the same work costs well under $1. Choosing the model is a quality-versus-cost decision; measure it with the evaluation set.

Every response includes `usage.input_tokens` and `usage.output_tokens`, so the app can compute real per-request cost from these documented rates.

### Gotchas
- Opus 5.5 always uses adaptive thinking; you can't turn it off. Its effort setting defaults to `medium`, so set `output_config.effort` explicitly.
- Opus 5.5 rejects forced `tool_choice` (`any`/`tool`). Use structured outputs (`output_config.format`) for the Pydantic-validated response.
- Check `stop_reason` before reading content (`refusal`, `max_tokens`).

### Alternative: one bill via Hugging Face
HF Inference Providers also serves open chat models through `https://router.huggingface.co/v1`, using the same `HF_TOKEN`. Prices vary by model and provider. This avoids a second account, but output quality, structured-output support and latency vary. Verify a specific model before choosing it.

---

## 4. LangSmith (optional tracing and evaluation)

### Set up
1. Sign up at https://smith.langchain.com (Developer plan, free, 1 seat).
2. Go to **Settings → API Keys → Create API Key** and choose type **Personal Access Token**.
3. In `.env`, set `LANGSMITH_TRACING=true`, `LANGSMITH_API_KEY=<key>` and `LANGSMITH_PROJECT=ops-wingman`.
4. Keep `LANGSMITH_TRACING=false` in any environment where you don't want trace payloads leaving the host.

### Check it works
```bash
.yzer/bin/pip install langsmith python-dotenv
.yzer/bin/python -c "
from dotenv import load_dotenv; load_dotenv()
from langsmith import Client
print([p.name for p in Client().list_projects()])"
```

### Costs
- Developer plan: **$0** for up to **5,000 base traces/month**, kept for **14 days**. This project should stay well under that.
- Plus costs $39/seat/month with 10,000 traces. **You don't need it.**
- Overage: the official page only says "pay as you go." Third-party sources disagree, quoting $2.50 or $5.00 per 1,000 base traces after a July 2026 pricing change. Treat overage as unconfirmed.
- Evaluation runs and online evaluators count as traces and can upgrade them to extended retention (higher cost). Don't enable online evaluators.
- Traces contain prompts and responses. With synthetic data that's acceptable, but never trace secrets.

---

## 5. Django secret and demo access (no external account)

Access control uses **Django's built-in authentication**, not PythonAnywhere's password-protection feature. Leave that feature **off** on the web app.

- Generate `DJANGO_SECRET_KEY`:
  ```bash
  .yzer/bin/python -c "import secrets; print(secrets.token_urlsafe(50))"
  ```
- Every Transportation Operations Wingman view requires login (`LoginRequiredMiddleware` or `@login_required`).
- **Two separate accounts:**
  - A **demo user** (not staff, not superuser) for the CIO walkthrough. Create it with a management command that prompts for the password, or with `createsuperuser` followed by removing the flags. Use only the operations screens.
  - An **admin superuser** for Django admin, made with `manage.py createsuperuser`. Never share it.
- Passwords are entered interactively on each machine. **Never** put them in the repo, `.env.example`, seed data or fixtures.
- The costly endpoints (explain, briefing) are POST-only, CSRF-protected and rate-limited per user. Use Django's **database cache** backend for the limiter, because PythonAnywhere runs several worker processes and the in-memory cache isn't shared between them.

---

## 6. PythonAnywhere (already paid)

- Paid accounts have unrestricted outbound internet, so Pinecone, HF, Anthropic and LangSmith calls work from the web app.
- Under **Account → System image**, confirm the image is **`innit`**, the current one, so Python 3.12 is available. Then create the virtualenv on PythonAnywhere with Python 3.12 to match the local `.yzer` environment.
- No extra cost for this project.

---

## Pre-flight checklist (run Friday morning)

- [ ] `.env` created from `.env.example`, with all keys filled in
- [ ] Pinecone `list_indexes()` succeeds
- [ ] HF embedding call returns a vector with the expected dimension (credits or PRO active)
- [ ] Anthropic call returns `ready` and reports usage
- [ ] LangSmith `list_projects()` succeeds (optional)
- [ ] Spend limits set in the Anthropic console and the HF billing settings
- [ ] Same four checks pass from a PythonAnywhere Bash console

## Pricing sources
- Pinecone: https://www.pinecone.io/pricing/
- Hugging Face Inference Providers billing: https://huggingface.co/docs/inference-providers/pricing
- Hugging Face PRO: https://huggingface.co/pricing
- LangSmith: https://www.langchain.com/pricing
- Anthropic: https://www.anthropic.com/pricing (Claude API section)
- PythonAnywhere Python versions: https://help.pythonanywhere.com/pages/PythonVersions
