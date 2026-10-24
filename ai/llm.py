"""Small provider-neutral LLM adapter interface, plus the Anthropic adapter.

The Anthropic adapter calls Claude through LangChain (`langchain-anthropic`)
with structured outputs, so the response is constrained to the Pydantic
schema's JSON shape. The workflow still validates every response itself
(IDs, counts, scope); the schema constraint only reduces malformed output.

When no provider is configured `get_llm_client()` returns None and the app
shows an honest unavailable state; it never substitutes canned output.
"""

import logging
import time
from dataclasses import dataclass
from typing import Optional, Protocol

from django.conf import settings

logger = logging.getLogger(__name__)

# USD per million tokens (Anthropic first-party rates, see SETUP_CREDENTIALS.md).
PRICING = {
    "claude-opus-5-5": (4.00, 20.00),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-haiku-5-5": (0.10, 0.50),
}


class ProviderError(Exception):
    """The provider failed or returned an unusable response."""


class ProviderTimeout(ProviderError):
    """The provider did not respond within the configured timeout."""


@dataclass
class LLMResponse:
    text: str
    model: str
    latency_ms: int
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None


class LLMClient(Protocol):
    model: str

    def complete(self, system: str, user: str, schema: dict, effort: Optional[str] = None) -> LLMResponse: ...


def estimate_cost(model, input_tokens, output_tokens):
    """Estimated USD cost from documented rates, or None for an unknown model."""
    rates = PRICING.get(model)
    if rates is None or input_tokens is None or output_tokens is None:
        return None
    return (input_tokens * rates[0] + output_tokens * rates[1]) / 1_000_000


class AnthropicClient:
    """Claude via LangChain. One request per `complete` call; retries are the workflow's job."""

    def __init__(self, model, api_key, timeout, effort, max_tokens):
        from langchain_anthropic import ChatAnthropic

        self.model = model
        self._chat = ChatAnthropic(
            model=model,
            api_key=api_key,
            timeout=timeout,
            max_retries=0,
            max_tokens=max_tokens,
            effort=effort,
        )

    def complete(self, system, user, schema, effort=None):
        """`effort` overrides the client default for this call."""
        import anthropic
        import httpx
        from langchain_core.messages import HumanMessage, SystemMessage

        output_format = {"type": "json_schema", "schema": anthropic.transform_schema(schema)}
        started = time.monotonic()
        try:
            message = self._chat.invoke(
                [SystemMessage(system), HumanMessage(user)],
                output_config={"format": output_format},
                **({"effort": effort} if effort else {}),
            )
        except (anthropic.APITimeoutError, httpx.TimeoutException) as exc:
            raise ProviderTimeout("The language model did not respond in time.") from exc
        except anthropic.APIStatusError as exc:
            logger.warning("Anthropic API error %s: %s", exc.status_code, exc.message)
            raise ProviderError(f"The language model returned an error (HTTP {exc.status_code}).") from exc
        except anthropic.APIError as exc:
            logger.warning("Anthropic connection error: %s", exc)
            raise ProviderError("The language model could not be reached.") from exc
        latency_ms = int((time.monotonic() - started) * 1000)

        stop_reason = message.response_metadata.get("stop_reason")
        if stop_reason == "refusal":
            raise ProviderError("The language model declined to answer.")
        if stop_reason == "max_tokens":
            raise ProviderError("The language model's response was cut off before it finished.")

        usage = message.usage_metadata or {}
        return LLMResponse(
            text=message.text,
            model=message.response_metadata.get("model_name") or self.model,
            latency_ms=latency_ms,
            input_tokens=usage.get("input_tokens"),
            output_tokens=usage.get("output_tokens"),
        )


def llm_configured():
    return settings.LLM_PROVIDER == "anthropic" and bool(settings.LLM_MODEL and settings.ANTHROPIC_API_KEY)


def get_llm_client():
    """The configured live client, or None when no provider is configured."""
    if not llm_configured():
        return None
    return AnthropicClient(
        model=settings.LLM_MODEL,
        api_key=settings.ANTHROPIC_API_KEY,
        timeout=settings.LLM_TIMEOUT_SECONDS,
        effort=settings.LLM_EFFORT,
        max_tokens=settings.LLM_MAX_TOKENS,
    )
