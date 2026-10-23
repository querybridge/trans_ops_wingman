# Deploying to PythonAnywhere

This is a conventional Django WSGI app on a paid PythonAnywhere account: SQLite, no background workers, no WebSockets. Replace `YOUR_USERNAME` throughout.

## 1. Get the code onto PythonAnywhere

The repository has no remote yet. Pick one:

- **Private GitHub repository (recommended):** push this repo to a private GitHub repo, then in a PythonAnywhere Bash console run `git clone <repo-url> ~/yzer_demo`. Updates are a `git pull`.
- **Upload:** zip the project without `.yzer/`, `db.sqlite3`, `.env`, or `staticfiles/`, upload it in the Files tab, and run `unzip yzer_demo.zip -d ~/yzer_demo`.

Never upload `.env` or `db.sqlite3` from your laptop. Create both fresh on the server.

## 2. Check the system image

Under **Account → System image**, confirm the image provides Python 3.12 (the current `innit` image). The local `.yzer` environment uses Python 3.12.

## 3. Virtualenv and dependencies (Bash console)

```bash
mkvirtualenv --python=/usr/bin/python3.12 yzer
cd ~/yzer_demo
pip install -r requirements.txt
```

## 4. Environment file

```bash
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(50))"   # paste as DJANGO_SECRET_KEY
nano .env
```

Set at least:

```
DJANGO_SECRET_KEY=<generated>
DJANGO_DEBUG=false
DJANGO_ALLOWED_HOSTS=YOUR_USERNAME.pythonanywhere.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://YOUR_USERNAME.pythonanywhere.com
```

Provider keys can be added later (see `SETUP_CREDENTIALS.md`). Until then the app shows "not configured" states. Run `chmod 600 .env`.

## 5. Database, data, static files, users

```bash
python manage.py migrate
python manage.py createcachetable
python manage.py seed_demo
python manage.py collectstatic --noinput
python manage.py createsuperuser          # admin account (strong password)
python manage.py create_demo_user demo    # walkthrough account, no admin access
python manage.py run_evaluation           # records an offline evaluation run
```

Passwords are typed at prompts. Never put them in files or shell history.

## 6. Web app configuration (Web tab)

1. **Add a new web app → Manual configuration → Python 3.12.** Don't choose the "Django" quick start.
2. **Virtualenv:** `/home/YOUR_USERNAME/.virtualenvs/yzer`
3. **Source code / Working directory:** `/home/YOUR_USERNAME/yzer_demo`
4. **WSGI configuration file:** replace its contents with `deploy/pythonanywhere_wsgi.py` (set `YOUR_USERNAME`).
5. **Static files:** URL `/static/` → Directory `/home/YOUR_USERNAME/yzer_demo/staticfiles`
6. **Security:** turn on **Force HTTPS**. Leave **Password protection off**; access control is Django's login.
7. Click **Reload**.

## 7. Smoke checklist

```bash
python manage.py smoke_check --network
```

It checks the database, the 100 seeded shipments, procedures, the cache table, collected static files, the demo user and superuser, DEBUG off, a recorded evaluation run, provider configuration, and outbound HTTPS to Pinecone, Hugging Face, Anthropic, and LangSmith (no credentials sent).

Then in a browser:

- [ ] `https://YOUR_USERNAME.pythonanywhere.com/` redirects to the sign-in page
- [ ] Sign in as `demo`: the Exception Queue loads with the Plus Jakarta Sans font and navy header
- [ ] Filter Region → Tampa: 36 shipments, 4 needing attention (SHP-00007, SHP-00031, SHP-00052, SHP-00078)
- [ ] Open SHP-00031: timeline, two conflicting notes, SOP-FA-HHG and SOP-ESC sections
- [ ] Open SHP-00046 (Jacksonville): "No failed delivery attempt procedure on file"
- [ ] Explain Shipment and Generate Briefing show an honest "not configured" message (until providers are set)
- [ ] Footer **Demo Documentation** (red) shows the promise, workflow, rules, provider status, and the evaluation run
- [ ] `/admin/` rejects the `demo` user and accepts the superuser
- [ ] The Web tab's error log has no tracebacks

## Updating

```bash
cd ~/yzer_demo && git pull
workon yzer && pip install -r requirements.txt
python manage.py migrate && python manage.py collectstatic --noinput
python manage.py seed_demo     # only if the dataset changed; replaces synthetic data
```

Then click **Reload** on the Web tab.

## Notes and limits

- Web requests stay short: AI calls are bounded by `LLM_TIMEOUT_SECONDS` (default 30) with one repair attempt, and are rate-limited per user (`AI_RATE_LIMIT` per `AI_RATE_WINDOW_SECONDS`) via the database cache, which every worker process shares.
- No threads are started inside views. If longer processing is ever needed, a job queue is future work.
- `check --deploy` leaves two deliberate warnings: HTTPS redirects are handled by PythonAnywhere's Force HTTPS (or set `DJANGO_SECURE_SSL_REDIRECT=true`), and HSTS is off for a demo subdomain (`DJANGO_SECURE_HSTS_SECONDS` enables it).
- SQLite is fine for a single-user demo. A real deployment would move to MySQL or Postgres.
