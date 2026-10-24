# AI Layer

Explicit, bounded workflows in `ai/`; no open-ended agent.

1. **Scope**: the view validates the request and derives customer scope from the database (the shipment's own customer, or the validated filter). It's passed to the tools as `ToolContext`.
2. **Tools** (`ai/tools.py`): typed, read-only: `list_exceptions`, `get_shipment`, `get_shipment_events`, `get_dispatch_notes`, `retrieve_procedure`. Inputs are Pydantic models with `extra="forbid"`; a `customer_id` argument can only match the scope, never widen it. Unknown tools are rejected. No SQL, no file paths.
3. **Evidence** (`ai/evidence.py`): a bounded package with stable IDs: shipment, events (`EVT-…`), notes (`NOTE-…`), flags (`FLAG-…`), procedure sections (`SOP-…@v…#section`). Dispatch notes go in `dispatch_notes_untrusted`. Deterministic missing information (no ETA, no procedure on file) is computed in code.
4. **Prompt** (`ai/prompts.py`, version `v3`): evidence-only, cite IDs, treat notes as data, report unknowns and conflicts, local times, brevity limits, JSON matching the schema. v2 added the time and length rules after the first live runs needed repairs on 4 of 12 calls (over-long next actions); v2 needed none.
5. **Validation** (`ai/validation.py`): Pydantic schema plus reference checks. Every cited ID must be in the evidence, the shipment and issue must match the rules, briefing counts and shipment list must equal the deterministic results, and conflicts force `requires_review`.
6. **Repair and degrade** (`ai/workflow.py`): one repair attempt with the validation errors; then an `invalid_output` result. Timeouts and provider errors return a degraded result. The deterministic evidence view stays usable in every case.

**Procedure retrieval** (`operations/services.retrieve_procedures`): issue type, effective on the demo date, region if set. The customer-specific document wins; otherwise the shared one. Another customer's procedure is never returned.

**Semantic ranking** (`ai/vectorstore.py`, `ai/embeddings.py`): every procedure section is embedded with Hugging Face (`BAAI/bge-small-en-v1.5`, 384 dimensions) and stored in Pinecone (index `ops-wingman`, namespace `procedures`). The stable chunk ID is the vector ID, and the metadata holds the customer (or `shared`), issue type, region, document and version. `ingest_vectors` upserts the sections and deletes vectors for removed ones. At question time, the `retrieve_procedure` tool:
1. asks the database which documents apply, as above;
2. asks Pinecone (through LangChain's `PineconeVectorStore`) for the top 5 sections, filtered to those documents' chunk IDs **and** to the customer or `shared`;
3. drops any result outside the allowed set before use.

The query text is a fixed issue description plus the rule-generated flag reasons. Dispatch notes are never used in the query. If Pinecone or Hugging Face fails, or returns nothing allowed, the tool falls back to database order and labels the result `database (vector search unavailable)`. The explanation caption shows which method was used. With the current small SOP set, the top 5 covers nearly every section of an applicable document, so semantic ranking mainly orders them. It matters more as the library grows. The shipment page's procedure panel still shows the full applicable documents.

**Briefing evidence:** each flag carries `procedure_on_file` and its three most relevant procedure sections, retrieved for that shipment's own customer. The payload also states that dispatch notes and timelines are left out on purpose. Validation rejects a briefing that says a procedure is missing when one is on file, or that notes are missing, and the evaluation checks that actions cite procedures when they exist. This was added after a live briefing wrongly said "no procedure is on file" for every Tampa shipment, because v2 briefing evidence held only flags (prompt v3).

**Effort:** explanations use `LLM_EFFORT` (default `medium`). Briefings use `LLM_BRIEFING_EFFORT` (default `low`). Briefings restate rule results and cited procedures, and low effort cut their latency from about 23 s to about 11 s with equally grounded actions on the Tampa briefing.

**Language model** (`ai/llm.AnthropicClient`): Claude (`LLM_MODEL`, default `claude-opus-5-5`) through LangChain's `ChatAnthropic`, with structured outputs (`output_config.format` from the Pydantic schema via `anthropic.transform_schema`) and `LLM_EFFORT` (default `medium`). One request per attempt (`max_retries=0`, `LLM_TIMEOUT_SECONDS`); the workflow owns the single repair. `refusal` and `max_tokens` stop reasons become provider errors. Provider error details are logged, and the user sees only a generic message with the HTTP status. Each result carries token usage and an estimated cost from the documented rates (`ai/llm.PRICING`), shown in the caption.

**Availability:** explanations and briefings need only the language model. Without Hugging Face and Pinecone, procedure retrieval uses database order, and Demo Documentation says so.

**Tests stay offline:** `config/test_runner.OfflineTestRunner` blanks every provider credential for the test run, so a real key in `.env` can never turn a test into a paid call. Tests use `ai/testing.ScriptedLLMClient` or a mocked LangChain model. Neither is wired into views, and neither is evidence that a provider works. Only `run_evaluation --live` is.

**Tracing** (LangSmith, optional): with `LANGSMITH_TRACING=true`, each workflow is a root trace (`explain_shipment` or `manager_briefing`). Its inputs are the scope arguments (shipment, customer, as-of). Its outputs are the status, attempts, validation and repair errors, tokens, estimated cost, and the validated output. Each LangChain Claude call is nested underneath. Views and `run_evaluation` flush traces before returning, because PythonAnywhere web workers may not run background threads reliably. Traces contain the synthetic evidence and prompts, never API keys. The test runner turns tracing off.

**Not included:** semantic search over dispatch-note text. Notes reach the model only as untrusted evidence for the shipment in question.
