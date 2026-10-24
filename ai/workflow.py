"""Bounded, explicit workflows: assemble evidence -> generate -> validate -> (one repair) -> result.

There is no open-ended agent loop. Evidence is gathered by calling the typed
tools in a fixed order; the model only writes the narrative and cannot change
facts, counts, or scope.
"""

import time
from dataclasses import dataclass, field
from typing import Any, Optional

from langsmith import traceable

from .evidence import build_briefing_evidence, build_shipment_evidence
from .llm import ProviderError, ProviderTimeout, estimate_cost
from .prompts import PROMPT_VERSION, briefing_messages, explain_messages, repair_message
from .schemas import ManagerBriefing, ShipmentExplanation
from .tools import ToolContext
from .validation import validate_briefing, validate_explanation

MAX_ATTEMPTS = 2  # first attempt + one repair


@dataclass
class AIResult:
    status: str  # ok | unconfigured | not_found | timeout | provider_error | invalid_output
    evidence: Any = None
    output: Any = None
    errors: list = field(default_factory=list)
    repair_reasons: list = field(default_factory=list)  # validation errors from rejected attempts
    attempts: int = 0
    latency_ms: int = 0
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    model: Optional[str] = None
    prompt_version: str = PROMPT_VERSION

    @property
    def ok(self):
        return self.status == "ok"

    @property
    def cost_usd(self):
        return estimate_cost(self.model, self.input_tokens, self.output_tokens)


def _generate(client, system, user, schema, validate, evidence):
    result = AIResult(status="invalid_output", evidence=evidence, model=getattr(client, "model", None))
    started = time.monotonic()
    prompt = user
    try:
        for attempt in range(1, MAX_ATTEMPTS + 1):
            result.attempts = attempt
            response = client.complete(system, prompt, schema)
            result.input_tokens = (result.input_tokens or 0) + (response.input_tokens or 0)
            result.output_tokens = (result.output_tokens or 0) + (response.output_tokens or 0)
            outcome = validate(response.text)
            if outcome.ok:
                result.status, result.output, result.errors = "ok", outcome.output, []
                break
            result.errors = outcome.errors
            result.repair_reasons.extend(outcome.errors)
            prompt = repair_message(user, outcome.errors)
    except ProviderTimeout:
        result.status, result.errors = "timeout", ["The language model did not respond in time."]
    except ProviderError as exc:
        result.status, result.errors = "provider_error", [str(exc) or "The language model returned an error."]
    result.latency_ms = int((time.monotonic() - started) * 1000)
    return result


def _trace_inputs(inputs):
    """Drop the client object; keep the scope arguments readable in the trace."""
    return {k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in inputs.items() if k != "client"}


def _trace_outputs(result):
    return {
        "status": result.status,
        "attempts": result.attempts,
        "errors": result.errors,
        "repair_reasons": result.repair_reasons,
        "model": result.model,
        "prompt_version": result.prompt_version,
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
        "estimated_cost_usd": result.cost_usd,
        "output": result.output.model_dump() if result.output else None,
    }


# Traces go to LangSmith only when LANGSMITH_TRACING is on; otherwise these are no-ops.
@traceable(name="explain_shipment", run_type="chain", process_inputs=_trace_inputs,
           process_outputs=_trace_outputs, metadata={"prompt_version": PROMPT_VERSION})
def run_explanation(shipment_id, customer_id, as_of, client):
    """`customer_id` must come from validated application state, never from model output."""
    evidence = build_shipment_evidence(ToolContext(customer_id=customer_id, as_of=as_of), shipment_id)
    if evidence is None:
        return AIResult(status="not_found", errors=[f"Shipment {shipment_id} was not found in the current scope."])
    if client is None:
        return AIResult(status="unconfigured", evidence=evidence)
    system, user = explain_messages(evidence)
    return _generate(client, system, user, ShipmentExplanation.model_json_schema(),
                     lambda text: validate_explanation(text, evidence), evidence)


@traceable(name="manager_briefing", run_type="chain", process_inputs=_trace_inputs,
           process_outputs=_trace_outputs, metadata={"prompt_version": PROMPT_VERSION})
def run_briefing(customer_id, region, as_of, client, scope_label="All customers"):
    evidence = build_briefing_evidence(ToolContext(customer_id=customer_id, as_of=as_of), region, scope_label)
    if client is None:
        return AIResult(status="unconfigured", evidence=evidence)
    system, user = briefing_messages(evidence)
    return _generate(client, system, user, ManagerBriefing.model_json_schema(),
                     lambda text: validate_briefing(text, evidence), evidence)


def flush_traces():
    """Send pending LangSmith traces before the request ends.

    PythonAnywhere web workers may not run background threads reliably, so
    views flush explicitly. A tracing failure never affects the response.
    """
    try:
        from langchain_core.tracers.langchain import wait_for_all_tracers

        wait_for_all_tracers()
    except Exception:  # noqa: BLE001 - tracing is optional
        pass
