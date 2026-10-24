"""Anthropic adapter behavior with the LangChain model mocked. No network calls."""

from unittest import mock

import anthropic
import httpx
from django.test import SimpleTestCase, override_settings
from langchain_core.messages import AIMessage

from ai.llm import AnthropicClient, ProviderError, ProviderTimeout, estimate_cost, get_llm_client
from ai.schemas import ShipmentExplanation

SCHEMA = ShipmentExplanation.model_json_schema()
REQUEST = httpx.Request("POST", "https://api.anthropic.com/v1/messages")


def reply(text='{"ok": true}', stop_reason="end_turn"):
    return AIMessage(
        content=[{"type": "text", "text": text}],
        response_metadata={"stop_reason": stop_reason, "model_name": "claude-opus-5-5"},
        usage_metadata={"input_tokens": 1000, "output_tokens": 200, "total_tokens": 1200},
    )


class AdapterTests(SimpleTestCase):
    def setUp(self):
        self.client = AnthropicClient(model="claude-opus-5-5", api_key="test-key", timeout=5, effort="low", max_tokens=1000)

    def complete_with(self, side_effect):
        with mock.patch.object(type(self.client._chat), "invoke", side_effect=side_effect) as invoke:
            return self.client.complete("system", "user", SCHEMA), invoke

    def test_returns_text_usage_and_requests_structured_output(self):
        response, invoke = self.complete_with([reply('{"summary": "x"}')])
        self.assertEqual(response.text, '{"summary": "x"}')
        self.assertEqual((response.input_tokens, response.output_tokens), (1000, 200))
        output_format = invoke.call_args.kwargs["output_config"]["format"]
        self.assertEqual(output_format["type"], "json_schema")
        self.assertFalse(output_format["schema"]["additionalProperties"])

    def test_effort_override_is_passed_per_call(self):
        with mock.patch.object(type(self.client._chat), "invoke", side_effect=[reply(), reply()]) as invoke:
            self.client.complete("s", "u", SCHEMA, effort="low")
            self.client.complete("s", "u", SCHEMA)
        self.assertEqual(invoke.call_args_list[0].kwargs["effort"], "low")
        self.assertNotIn("effort", invoke.call_args_list[1].kwargs)

    def test_refusal_and_truncation_are_provider_errors(self):
        for stop_reason in ("refusal", "max_tokens"):
            with self.subTest(stop_reason=stop_reason), self.assertRaises(ProviderError):
                self.complete_with([reply(stop_reason=stop_reason)])

    def test_timeout_maps_to_provider_timeout(self):
        with self.assertRaises(ProviderTimeout):
            self.complete_with(anthropic.APITimeoutError(request=REQUEST))

    def test_api_error_message_has_status_but_no_details(self):
        error = anthropic.AuthenticationError("invalid x-api-key", response=httpx.Response(401, request=REQUEST), body=None)
        with self.assertRaises(ProviderError) as ctx:
            self.complete_with(error)
        self.assertEqual(str(ctx.exception), "The language model returned an error (HTTP 401).")

    def test_cost_estimate(self):
        self.assertAlmostEqual(estimate_cost("claude-opus-5-5", 1_000_000, 100_000), 6.0)
        self.assertIsNone(estimate_cost("unknown-model", 10, 10))


class FactoryTests(SimpleTestCase):
    def test_offline_test_run_has_no_client(self):
        self.assertIsNone(get_llm_client())

    @override_settings(ANTHROPIC_API_KEY="test-key", LLM_MODEL="claude-opus-5-5", LLM_PROVIDER="anthropic")
    def test_configured_returns_anthropic_client(self):
        self.assertIsInstance(get_llm_client(), AnthropicClient)

    @override_settings(ANTHROPIC_API_KEY="test-key", LLM_PROVIDER="other")
    def test_unknown_provider_is_unconfigured(self):
        self.assertIsNone(get_llm_client())
