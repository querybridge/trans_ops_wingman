import socket
import urllib.error
import urllib.request

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.staticfiles import finders
from django.core.management.base import BaseCommand
from django.db import connection

from ai.status import provider_status
from evaluation.models import EvaluationRun
from operations.models import ProcedureDocument, Shipment

PROVIDER_HOSTS = {
    "Pinecone": "https://api.pinecone.io",
    "Hugging Face": "https://router.huggingface.co",
    "Anthropic": "https://api.anthropic.com",
    "LangSmith": "https://api.smith.langchain.com",
}


class Command(BaseCommand):
    help = "Deployment smoke checks: database, demo data, static files, users, provider config; --network tests outbound HTTPS."

    def add_arguments(self, parser):
        parser.add_argument("--network", action="store_true", help="Check outbound HTTPS reachability of provider hosts (no credentials sent).")

    def line(self, ok, label, detail=""):
        mark = self.style.SUCCESS("PASS") if ok else self.style.ERROR("FAIL")
        self.stdout.write(f"{mark}  {label}{f' — {detail}' if detail else ''}")
        return ok

    def handle(self, *args, network, **options):
        results = []
        try:
            connection.ensure_connection()
            results.append(self.line(True, "Database reachable", str(settings.DATABASES["default"]["NAME"])))
        except Exception as exc:
            results.append(self.line(False, "Database reachable", str(exc)))
            return
        results.append(self.line(Shipment.objects.count() == 100, "Demo data seeded", f"{Shipment.objects.count()} shipments (expect 100; run seed_demo)"))
        results.append(self.line(ProcedureDocument.objects.count() >= 6, "Procedures loaded", f"{ProcedureDocument.objects.count()} documents"))
        try:
            from django.core.cache import cache
            cache.set("smoke", 1, 5)
            results.append(self.line(cache.get("smoke") == 1, "Cache table works", "run createcachetable if this fails"))
        except Exception as exc:
            results.append(self.line(False, "Cache table works", f"{exc} (run createcachetable)"))
        static_ok = (settings.STATIC_ROOT / "css/wingman.css").exists() if not settings.DEBUG else bool(finders.find("css/wingman.css"))
        results.append(self.line(static_ok, "Static files available", "run collectstatic" if not static_ok else str(settings.STATIC_ROOT)))
        users = get_user_model().objects
        results.append(self.line(users.filter(is_superuser=False, is_active=True).exists(), "Non-staff demo user exists", "run create_demo_user"))
        results.append(self.line(users.filter(is_superuser=True).exists(), "Admin superuser exists", "run createsuperuser"))
        results.append(self.line(not settings.DEBUG, "DEBUG is off", "set DJANGO_DEBUG=false in .env" if settings.DEBUG else ""))
        results.append(self.line(EvaluationRun.objects.exists(), "Evaluation run recorded", "run run_evaluation"))
        for p in provider_status():
            self.line(p["configured"], f"Provider configured: {p['name']}", p["detail"])
        if network:
            for name, url in PROVIDER_HOSTS.items():
                try:
                    urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=8)
                    self.line(True, f"Outbound HTTPS to {name}", url)
                except urllib.error.HTTPError as exc:  # any HTTP response proves the host is reachable
                    self.line(True, f"Outbound HTTPS to {name}", f"{url} (HTTP {exc.code})")
                except (urllib.error.URLError, socket.timeout) as exc:
                    self.line(False, f"Outbound HTTPS to {name}", f"{url}: {getattr(exc, 'reason', exc)}")
        self.stdout.write(self.style.SUCCESS("Core checks passed.") if all(results) else self.style.WARNING("Some core checks failed."))
