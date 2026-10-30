"""Django settings for Transportation Operations Wingman.

All environment-specific values come from a git-ignored `.env` file
(template: `.env.example`, guide: `SETUP_CREDENTIALS.md`).
"""

import os
from datetime import datetime
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_bool(name, default=False):
    return os.environ.get(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


DEBUG = env_bool("DJANGO_DEBUG", False)

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY or SECRET_KEY == "change-me":
    if not DEBUG:
        raise ImproperlyConfigured("DJANGO_SECRET_KEY must be set when DJANGO_DEBUG is false.")
    SECRET_KEY = "insecure-dev-only-key"

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "operations",
    "ingestion",
    "ai",
    "evaluation",
    "web",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # Every view requires login unless explicitly marked @login_not_required.
    "django.contrib.auth.middleware.LoginRequiredMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "web.context_processors.demo",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Database cache so rate limits are shared across PythonAnywhere worker processes.
# Create the table once with: python manage.py createcachetable
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "wingman_cache",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "web:worklist"
LOGOUT_REDIRECT_URL = "login"

LANGUAGE_CODE = "en-us"
TIME_ZONE = "America/New_York"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Blanks provider credentials so tests never make live (paid) calls.
TEST_RUNNER = "config.test_runner.OfflineTestRunner"

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_CONTENT_TYPE_NOSNIFF = True
    # PythonAnywhere's "Force HTTPS" toggle usually handles redirects; these allow doing it in Django too.
    SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", False)
    SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_SECURE_HSTS_SECONDS", "0"))
    SESSION_COOKIE_AGE = 60 * 60 * 8  # demo sessions expire after a working day

# Errors go to the console, which PythonAnywhere writes to the web app's error log.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "WARNING"},
    "loggers": {"django": {"handlers": ["console"], "level": "WARNING", "propagate": False}},
}

# --- Demo clock -----------------------------------------------------------
# Exception rules and ages are computed against this fixed timestamp, never the
# real clock, so the demo stays reproducible.
DEMO_AS_OF = datetime.fromisoformat(os.environ.get("DEMO_AS_OF", "2026-10-21T15:00:00-04:00"))
if DEMO_AS_OF.tzinfo is None:
    raise ImproperlyConfigured("DEMO_AS_OF must include a timezone offset.")

# --- Providers --------------------------------------------------------------
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY", "")
PINECONE_INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME", "ops-wingman")
PINECONE_CLOUD = os.environ.get("PINECONE_CLOUD", "aws")
PINECONE_REGION = os.environ.get("PINECONE_REGION", "us-east-1")

HF_TOKEN = os.environ.get("HF_TOKEN", "")
HF_EMBEDDING_PROVIDER = os.environ.get("HF_EMBEDDING_PROVIDER", "hf-inference")
HF_EMBEDDING_MODEL = os.environ.get("HF_EMBEDDING_MODEL", "")
EMBEDDING_DIMENSIONS = int(os.environ.get("EMBEDDING_DIMENSIONS", "0") or 0)

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "anthropic")
LLM_MODEL = os.environ.get("LLM_MODEL", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
LLM_TIMEOUT_SECONDS = float(os.environ.get("LLM_TIMEOUT_SECONDS", "30"))
# Reasoning effort (low | medium | high | xhigh | max): higher is slower and costs more.
LLM_EFFORT = os.environ.get("LLM_EFFORT", "medium")
LLM_BRIEFING_EFFORT = os.environ.get("LLM_BRIEFING_EFFORT", "low")
# Room for adaptive thinking plus the JSON answer.
LLM_MAX_TOKENS = int(os.environ.get("LLM_MAX_TOKENS", "8000"))

LANGSMITH_TRACING = env_bool("LANGSMITH_TRACING", False)
LANGSMITH_API_KEY = os.environ.get("LANGSMITH_API_KEY", "")
LANGSMITH_PROJECT = os.environ.get("LANGSMITH_PROJECT", "ops-wingman")

# Per-user limit on costly AI endpoints (requests per window).
AI_RATE_LIMIT = int(os.environ.get("AI_RATE_LIMIT", "20"))
AI_RATE_WINDOW_SECONDS = int(os.environ.get("AI_RATE_WINDOW_SECONDS", "600"))
