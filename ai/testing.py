"""Test double for the LLM adapter. Used only by tests; never wired into views."""

import json

from .llm import LLMResponse


class ScriptedLLMClient:
    """Returns scripted responses in order. Items may be str, dict, or an exception to raise."""

    model = "scripted-test-double"

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def complete(self, system, user, schema, effort=None):
        self.calls.append({"system": system, "user": user, "effort": effort})
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        text = item if isinstance(item, str) else json.dumps(item)
        return LLMResponse(text=text, model=self.model, latency_ms=1, input_tokens=len(user) // 4, output_tokens=len(text) // 4)
