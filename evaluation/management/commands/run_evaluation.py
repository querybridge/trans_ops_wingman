from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from ai.llm import get_llm_client
from ai.workflow import flush_traces
from evaluation.runner import Runner, save_run


class Command(BaseCommand):
    help = "Run the 20-case evaluation. Offline by default; --live also runs checks that need the language model."

    def add_arguments(self, parser):
        parser.add_argument("--live", action="store_true", help="Use the configured live LLM provider.")
        parser.add_argument("--no-save", action="store_true", help="Don't record the run or write reports.")

    def handle(self, *args, live, no_save, **options):
        client = None
        if live:
            client = get_llm_client()
            if client is None:
                raise CommandError("No live LLM adapter is configured, so a live run isn't possible. Run without --live.")
        results, metrics = Runner(settings.DEMO_AS_OF, client).run()
        flush_traces()
        for r in results:
            style = {"pass": self.style.SUCCESS, "partial": self.style.WARNING, "fail": self.style.ERROR}[r.status]
            self.stdout.write(style(f"{r.id:6} {r.category:22} {r.status}"))
            for c in r.checks:
                if c.status == "fail":
                    self.stdout.write(f"         FAIL {c.name}: {c.detail}")
        rules = metrics["rules"]
        self.stdout.write(
            f"\nMode {metrics['mode']}: {metrics['cases']}; checks {metrics['checks']}\n"
            f"Rules: precision {rules['precision']}, recall {rules['recall']}, normal-cohort false positives {rules['normal_cohort_false_positives']}\n"
            f"Retrieval hit rate @{metrics['retrieval']['k']}: {metrics['retrieval']['hit_rate']}; isolation failures {metrics['isolation_failures']}"
        )
        if not no_save:
            run = save_run(results, metrics, client)
            self.stdout.write(f"Recorded evaluation run {run.pk}; report written to evaluation/reports/latest_{metrics['mode']}.md")
