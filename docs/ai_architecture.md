# AI Layer

Explicit, bounded workflows in `ai/`; no open-ended agent.

1. **Scope**: the view validates the request and derives customer scope from the database (the shipment's own customer, or the validated filter). It's passed to the tools as `ToolContext`.
2. **Tools** (`ai/tools.py`): typed, read-only: `list_exceptions`, `get_shipment`, `get_shipment_events`, `get_dispatch_notes`, `retrieve_procedure`. Inputs are Pydantic models with `extra="forbid"`; a `customer_id` argument can only match the scope, never widen it. Unknown tools are rejected. No SQL, no file paths.
3. **Evidence** (`ai/evidence.py`): a bounded package with stable IDs: shipment, events (`EVT-…`), notes (`NOTE-…`), flags (`FLAG-…`), procedure sections (`SOP-…@v…#section`). Dispatch notes go in `dispatch_notes_untrusted`. Deterministic missing information (no ETA, no procedure on file) is computed in code.
4. **Prompt** (`ai/prompts.py`, version `v2`): evidence-only, cite IDs, treat notes as data, report unknowns and conflicts, local times, brevity limits, JSON matching the schema. v2 added the time and length rules after the first live runs needed repairs on 4 of 12 calls (over-long next actions); v2 needed none.
5. **Validation** (`ai/validation.py`): Pydantic schema plus reference checks. Every cited ID must be in the evidence, the shipment and issue must match the rules, briefing counts and shipment list must equal the deterministic results, and conflicts force `requires_review`.
6. **Repair and degrade** (`ai/workflow.py`): one repair attempt with the validation errors; then an `invalid_output` result. Timeouts and provider errors return a degraded result. The deterministic evidence view stays usable in every case.

**Procedure retrieval** (`operations/services.retrieve_procedures`): issue type, effective on the demo date, region if set. The customer-specific document wins; otherwise the shared one. Another customer's procedure is never returned. Pinecone semantic retrieval will sit behind the same function, with the database staying authoritative.

**Language model** (`ai/llm.AnthropicClient`): Claude (`LLM_MODEL`, default `claude-opus-5-5`) through LangChain's `ChatAnthropic`, with structured outputs (`output_config.format` from the Pydantic schema via `anthropic.transform_schema`) and `LLM_EFFORT` (default `medium`). One request per attempt (`max_retries=0`, `LLM_TIMEOUT_SECONDS`); the workflow owns the single repair. `refusal` and `max_tokens` stop reasons become provider errors. Provider error details are logged, and the user sees only a generic message with the HTTP status. Each result carries token usage and an estimated cost from the documented rates (`ai/llm.PRICING`), shown in the caption.

**Availability:** explanations and briefings need only the language model. Until Hugging Face and Pinecone are connected, procedure retrieval uses the database filter, and Demo Documentation says so.

**Tests stay offline:** `config/test_runner.OfflineTestRunner` blanks every provider credential for the test run, so a real key in `.env` can never turn a test into a paid call. Tests use `ai/testing.ScriptedLLMClient` or a mocked LangChain model. Neither is wired into views, and neither is evidence that a provider works. Only `run_evaluation --live` is.

**Not yet connected (needs credentials):** Hugging Face embeddings, Pinecone, and LangSmith tracing.
