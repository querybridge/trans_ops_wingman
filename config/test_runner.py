"""Test runner that keeps the suite offline.

A real key in `.env` must never turn a test into a paid live call, so every
provider credential is blanked for the whole run. Tests that exercise the AI
path inject `ai.testing.ScriptedLLMClient` explicitly.
"""

import os

from django.test.runner import DiscoverRunner
from django.test.utils import override_settings

OFFLINE = {
    "ANTHROPIC_API_KEY": "",
    "PINECONE_API_KEY": "",
    "HF_TOKEN": "",
    "LANGSMITH_API_KEY": "",
    "LANGSMITH_TRACING": False,
}


class OfflineTestRunner(DiscoverRunner):
    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)
        os.environ["LANGSMITH_TRACING"] = "false"  # LangChain reads tracing flags from the environment
        self._offline = override_settings(**OFFLINE)
        self._offline.enable()

    def teardown_test_environment(self, **kwargs):
        self._offline.disable()
        super().teardown_test_environment(**kwargs)
