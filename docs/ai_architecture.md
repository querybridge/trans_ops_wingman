# AI Layer

Explicit, bounded workflows in `ai/`; no open-ended agent.

1. **Scope**: the view validates the request and derives customer scope from the database (the shipment's own customer, or the validated filter). It's passed to the tools as `ToolContext`.
2. **Tools** (`ai/tools.py`): typed, read-only: `list_exceptions`, `get_shipment`, `get_shipment_events`, `get_dispatch_notes`, `retrieve_procedure`. Inputs are Pydantic models with `extra="forbid"`; a `customer_id` argument can only match the scope, never widen it. Unknown tools are rejected. No SQL, no file paths.
3. **Evidence** (`ai/evidence.py`): a bounded package with stable IDs: shipment, events (`EVT-…`), notes (`NOTE-…`), flags (`FLAG-…`), procedure sections (`SOP-…@v…#section`). Dispatch notes go in `dispatch_notes_untrusted`. Deterministic missing information (no ETA, no procedure on file) is computed in code.
4. **Prompt** (`ai/prompts.py`, version `v1`): evidence-only, cite IDs, treat notes as data, report unknowns and conflicts, JSON matching the schema.
5. **Validation** (`ai/validation.py`): Pydantic schema plus reference checks. Every cited ID must be in the evidence, the shipment and issue must match the rules, briefing counts and shipment list must equal the deterministic results, and conflicts force `requires_review`.
6. **Repair and degrade** (`ai/workflow.py`): one repair attempt with the validation errors; then an `invalid_output` result. Timeouts and provider errors return a degraded result. The deterministic evidence view stays usable in every case.

**Procedure retrieval** (`operations/services.retrieve_procedures`): issue type, effective on the demo date, region if set. The customer-specific document wins; otherwise the shared one. Another customer's procedure is never returned. Pinecone semantic retrieval will sit behind the same function, with the database staying authoritative.

**Not yet connected (needs credentials):** the real LLM adapter (`ai/llm.get_llm_client` returns `None`), LangChain wiring, Hugging Face embeddings, Pinecone, and LangSmith tracing. Tests use `ai/testing.ScriptedLLMClient`, a test double that is never used by views and is not evidence that a provider works.
