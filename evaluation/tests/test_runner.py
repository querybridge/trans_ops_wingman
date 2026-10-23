from datetime import datetime

from django.test import TestCase

from ai.testing import ScriptedLLMClient
from evaluation.models import EvaluationRun
from evaluation.runner import Runner, save_run
from ingestion.procedures import ingest_procedures
from ingestion.seed import seed

AS_OF = datetime.fromisoformat("2026-10-21T15:00:00-04:00")


class RunnerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed(AS_OF)
        ingest_procedures()

    def test_offline_run_has_no_failures_and_skips_live_checks(self):
        results, metrics = Runner(AS_OF).run()
        self.assertEqual(len(results), 20)
        self.assertEqual(metrics["cases"]["fail"], 0)
        self.assertEqual(metrics["rules"]["precision"], 1.0)
        self.assertEqual(metrics["rules"]["recall"], 1.0)
        self.assertEqual(metrics["rules"]["normal_cohort_false_positives"], 0)
        self.assertEqual(metrics["isolation_failures"], 0)
        skipped = [c for r in results for c in r.checks if c.status == "skipped"]
        self.assertTrue(skipped)
        self.assertTrue(all("live language model" in c.detail for c in skipped))
        self.assertEqual(metrics["ai"]["calls"], 0)

    def test_bad_model_output_fails_ai_checks_instead_of_passing(self):
        results, metrics = Runner(AS_OF, ScriptedLLMClient(["{not json"] * 40)).run()
        self.assertGreater(metrics["cases"]["fail"], 0)
        self.assertEqual(metrics["checks"]["skipped"], 0)
        self.assertEqual(metrics["ai"]["valid_output_rate"], 0.0)

    def test_save_run_records_offline_mode(self):
        results, metrics = Runner(AS_OF).run()
        run = save_run(results, metrics, None, write_report=False)
        self.assertFalse(run.live_providers)
        self.assertEqual(run.cases_total, 20)
        self.assertEqual(EvaluationRun.objects.count(), 1)
