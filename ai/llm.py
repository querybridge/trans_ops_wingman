"""Small provider-neutral LLM adapter interface.

Real provider adapters (and the LangChain wiring) are added once credentials
are available. Until then `get_llm_client()` returns None and the app shows an
honest unavailable state; it never substitutes canned output.
"""

from dataclasses import dataclass
from typing import Optional, Protocol


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

    def complete(self, system: str, user: str, schema: dict) -> LLMResponse: ...


def get_llm_client():
    """The configured live client, or None when no adapter is available."""
    return None
