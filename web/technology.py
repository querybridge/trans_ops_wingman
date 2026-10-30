"""Layout and copy for the Technology Map page.

Coordinates are in the SVG's viewBox units. Descriptions are kept short and
must stay true to the code; update them when a component changes.
"""

from django.conf import settings

W, H = 200, 56
COLS = [20, 270, 520, 770, 1020]
LANES = ["Sources", "Ingestion", "Core (Django)", "AI Layer", "Manager Screens"]
BUS_X = 1003  # gutter between the AI layer and the screens
TRACE_X = 984  # LangSmith's dashed route, left of the bus
CORRIDOR_Y = 398  # gap between the AI layer's upper and lower nodes


def _node(key, col, y, title, subtitle, description, provider=None):
    return {"key": key, "x": COLS[col], "y": y, "col": col, "title": title, "subtitle": subtitle,
            "description": description, "provider": provider}


def nodes():
    return [
        # Sources
        _node("tms", 0, 90, "Shipment export", "CSV · synthetic in the demo",
              "A transportation management system export of shipments and scan events. In the demo, 100 synthetic shipments stand in for it."),
        _node("notes", 0, 190, "Dispatch notes", "drivers · dispatch · customer service",
              "Free-text notes from the field. They're treated as untrusted data, never as instructions to the AI."),
        _node("sops", 0, 330, "Customer procedures", "SOPs in Markdown",
              "Procedures tagged with customer, issue type, region and effective dates. A customer's own version overrides the shared one."),
        # Ingestion
        _node("adapter", 1, 140, "CSV adapter", "mapping + validation",
              "Maps a source export into the canonical schema. Bad timezones, regions, customers, windows or duplicate rows are rejected and reported, never guessed. A new source system needs only a new adapter."),
        _node("procingest", 1, 330, "Procedure ingestion", "sections with stable IDs",
              "Splits each procedure into sections with stable IDs, such as SOP-FA-HHG@v1#disputed-attempts, so every step can be cited."),
        _node("vectors", 1, 470, "Embedding sync", "ingest_vectors",
              "Embeds every procedure section and stores it in Pinecone under its section ID. Vectors for removed sections are deleted."),
        # Core
        _node("db", 2, 140, "Canonical data model", "Django ORM · SQLite",
              "Customers, shipments, scan events, notes, procedures, user settings and evaluation runs. Nothing downstream depends on the source format."),
        _node("rules", 2, 240, "Exception rules", "plain, tested Python",
              "Missed window, missing scan, failed attempt and missing proof of delivery. The rules decide what's flagged and how urgent, at a fixed demo time. The AI can't change them."),
        _node("tools", 2, 340, "Scoped read-only tools", "typed · customer-scoped",
              "Typed tools that read shipments, events, notes and procedures. Customer scope comes from the database, and neither a request nor the model can widen it."),
        _node("hf", 2, 470, "Hugging Face", settings.HF_EMBEDDING_MODEL or "embedding model not set",
              f"Turns procedure sections and situation descriptions into {settings.EMBEDDING_DIMENSIONS or 'N'}-dimension vectors so related steps can be found by meaning, not keywords.",
              provider="Embeddings (Hugging Face)"),
        # AI layer
        _node("evidence", 3, 90, "Evidence package", "stable IDs for every record",
              "Bundles exactly the records for one shipment or one queue, each with an ID the answer must cite. Missing facts, such as no ETA or no procedure on file, are worked out in code."),
        _node("claude", 3, 190, "Claude via LangChain", settings.LLM_MODEL or "model not set",
              "Writes the explanation, recommendation or briefing from the evidence alone, as structured JSON that cites evidence IDs.",
              provider="Language model"),
        _node("validate", 3, 290, "Validation + one repair", "schema · citations · counts",
              "Checks the schema, that every cited ID is in the evidence, and that counts match the rules. One retry with the errors; after that, an honest error. Unchecked text is never shown."),
        _node("pinecone", 3, 470, "Pinecone vector index", settings.PINECONE_INDEX_NAME,
              "Ranks procedure sections by relevance, only within the procedures the database already allows for that customer. Anything outside that set is dropped.",
              provider="Vector retrieval (Pinecone)"),
        # Screens
        _node("worklist", 4, 90, "Worklist", "home page",
              "Each flagged delivery, why it failed, and the steps, owner and escalation trigger quoted from that customer's procedure. Loads without AI; a Wingman recommendation is one click away."),
        _node("exceptions", 4, 170, "Exception queue", "filters · severity · age",
              "Every flag in scope with its rule, threshold and age, filtered by customer and region."),
        _node("detail", 4, 250, "Shipment detail", "evidence + explanation",
              "Facts, timeline, notes and applicable procedures on one page, with a cited AI explanation on request."),
        _node("briefing", 4, 330, "Manager briefing", "queue summary",
              "A cited summary of the current queue. Its counts must match the rules exactly, or it's rejected."),
        _node("settings", 4, 410, "Settings", "per-user defaults",
              "Each user's default Worklist regions and urgency levels."),
        _node("langsmith", 4, 520, "LangSmith tracing", f"project {settings.LANGSMITH_PROJECT}",
              "Records every AI call: the evidence sent, the answer, the validation result, tokens and estimated cost.",
              provider="Tracing (LangSmith, optional)"),
    ]


PLATFORM = [
    ("django", "Django + login", "Django's own sign-in protects every page. The demo account is separate from the admin, and AI requests are rate-limited per user."),
    ("htmx", "HTMX", "Updates parts of a page, such as filters, explanations and recommendations, without a JavaScript framework."),
    ("pythonanywhere", "PythonAnywhere", "Hosts the app over HTTPS. Provider keys live only in the server's environment file, never in the code."),
    ("evaluation", "Evaluation harness", "20 fixed cases that score the rules, procedure retrieval, customer isolation and AI answers, offline or against the live providers."),
    ("tests", "Automated tests", "Django test suite. Provider keys are blanked while it runs, so a test can never make a paid AI call."),
]

# (from, to, style) — "flow" is data flow; "assist" is ranking or tracing; "join" and "bus" feed the screens (no arrowhead).
EDGES = [
    ("tms", "adapter", "flow"), ("notes", "adapter", "flow"), ("sops", "procingest", "flow"),
    ("adapter", "db", "flow"), ("procingest", "db", "flow"), ("procingest", "vectors", "flow"),
    ("vectors", "hf", "flow"), ("hf", "pinecone", "flow"),
    ("db", "rules", "flow"), ("rules", "tools", "flow"), ("tools", "evidence", "flow"),
    ("evidence", "claude", "flow"), ("claude", "validate", "flow"),
    ("tools", "pinecone", "assist"), ("claude", "langsmith", "assist"),
]
BUS_TARGETS = ["worklist", "exceptions", "detail", "briefing"]


def _anchor(n, side):
    return {
        "right": (n["x"] + W, n["y"] + H / 2), "left": (n["x"], n["y"] + H / 2),
        "top": (n["x"] + W / 2, n["y"]), "bottom": (n["x"] + W / 2, n["y"] + H),
    }[side]


def _curve(a, b):
    (x1, y1), (x2, y2) = a, b
    mid = (x1 + x2) / 2
    return f"M{x1},{y1} C{mid},{y1} {mid},{y2} {x2},{y2}"


def edges(by_key):
    out = []
    for a, b, style in EDGES:
        na, nb = by_key[a], by_key[b]
        if na["col"] == nb["col"]:
            d = "M{},{} L{},{}".format(*_anchor(na, "bottom"), *_anchor(nb, "top"))
        elif a == "claude" and b == "langsmith":
            # Leave Claude on the right, run down the gutter, and enter LangSmith from the left.
            x1, y1 = _anchor(na, "right")
            x2, y2 = _anchor(nb, "left")
            y1 += 12
            d = f"M{x1},{y1} L{TRACE_X - 6},{y1} Q{TRACE_X},{y1} {TRACE_X},{y1 + 6} L{TRACE_X},{y2 - 6} Q{TRACE_X},{y2} {TRACE_X + 6},{y2} L{x2},{y2}"
        else:
            d = _curve(_anchor(na, "right"), _anchor(nb, "left"))
        out.append({"a": a, "b": b, "style": style, "d": d})
    # Rules and validated AI output reach the screens through a shared bus in the gutter.
    rx, ry = _anchor(by_key["rules"], "right")
    out.append({"a": "rules", "b": " ".join(BUS_TARGETS), "style": "join",
                "d": f"M{rx},{ry} C{rx + 30},{ry} {rx + 20},{CORRIDOR_Y} {rx + 50},{CORRIDOR_Y} L{BUS_X - 8},{CORRIDOR_Y} Q{BUS_X},{CORRIDOR_Y} {BUS_X},{CORRIDOR_Y - 8}"})
    vx, vy = _anchor(by_key["validate"], "right")
    out.append({"a": "validate", "b": " ".join(BUS_TARGETS), "style": "join", "d": f"M{vx},{vy} L{BUS_X},{vy}"})
    top = _anchor(by_key[BUS_TARGETS[0]], "left")[1]
    out.append({"a": "rules validate", "b": " ".join(BUS_TARGETS), "style": "bus", "d": f"M{BUS_X},{CORRIDOR_Y - 8} L{BUS_X},{top}"})
    for key in BUS_TARGETS:
        x, y = _anchor(by_key[key], "left")
        out.append({"a": "rules validate", "b": key, "style": "flow", "d": f"M{BUS_X},{y} L{x},{y}"})
    return out


def diagram(provider_status):
    configured = {p["name"]: p["configured"] for p in provider_status}
    items = nodes()
    for n in items:
        n["configured"] = configured.get(n["provider"]) if n["provider"] else None
    by_key = {n["key"]: n for n in items}
    platform_w = (COLS[-1] + W - COLS[0] - 4 * 20) / 5
    platform = [
        {"key": key, "title": title, "description": desc, "x": COLS[0] + i * (platform_w + 20), "y": 640, "w": platform_w,
         "cx": COLS[0] + i * (platform_w + 20) + platform_w / 2}
        for i, (key, title, desc) in enumerate(PLATFORM)
    ]
    return {
        "nodes": items,
        "edges": edges(by_key),
        "lanes": [{"title": t, "x": x + W / 2} for t, x in zip(LANES, COLS)],
        "platform": platform,
        "w": W, "h": H,
        "view_w": COLS[-1] + W + 20, "view_h": 720,
    }
