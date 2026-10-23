"""Honest provider configuration status. Presence of settings only; no network calls."""

from django.conf import settings


def provider_status():
    return [
        {
            "name": "Vector retrieval (Pinecone)",
            "configured": bool(settings.PINECONE_API_KEY),
            "detail": f"index {settings.PINECONE_INDEX_NAME} · {settings.PINECONE_CLOUD}/{settings.PINECONE_REGION}",
        },
        {
            "name": "Embeddings (Hugging Face)",
            "configured": bool(settings.HF_TOKEN and settings.HF_EMBEDDING_MODEL and settings.EMBEDDING_DIMENSIONS),
            "detail": f"{settings.HF_EMBEDDING_MODEL or 'no model set'} · {settings.EMBEDDING_DIMENSIONS or '?'} dims · {settings.HF_EMBEDDING_PROVIDER}",
        },
        {
            "name": "Language model",
            "configured": bool(settings.LLM_MODEL and settings.ANTHROPIC_API_KEY),
            "detail": f"{settings.LLM_PROVIDER} · {settings.LLM_MODEL or 'no model set'}",
        },
        {
            "name": "Tracing (LangSmith, optional)",
            "configured": bool(settings.LANGSMITH_TRACING and settings.LANGSMITH_API_KEY),
            "detail": f"project {settings.LANGSMITH_PROJECT}" if settings.LANGSMITH_TRACING else "tracing off",
        },
    ]


def ai_available():
    return all(p["configured"] for p in provider_status()[:3])
