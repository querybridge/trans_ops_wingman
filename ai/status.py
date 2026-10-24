"""Honest provider configuration status. Presence of settings only; no network calls."""

from django.conf import settings

from .embeddings import embeddings_configured
from .llm import llm_configured
from .vectorstore import vector_configured


def provider_status():
    return [
        {
            "name": "Vector retrieval (Pinecone)",
            "configured": vector_configured(),
            "detail": (
                f"index {settings.PINECONE_INDEX_NAME} · {settings.PINECONE_CLOUD}/{settings.PINECONE_REGION} · "
                "ranks sections within the procedures the database allows"
                if vector_configured()
                else "procedures are matched by database metadata filter (customer, issue type, region, effective dates)"
            ),
        },
        {
            "name": "Embeddings (Hugging Face)",
            "configured": embeddings_configured(),
            "detail": f"{settings.HF_EMBEDDING_MODEL or 'no model set'} · {settings.EMBEDDING_DIMENSIONS or '?'} dims · {settings.HF_EMBEDDING_PROVIDER}",
        },
        {
            "name": "Language model",
            "configured": llm_configured(),
            "detail": f"{settings.LLM_PROVIDER} via LangChain · {settings.LLM_MODEL or 'no model set'} · effort {settings.LLM_EFFORT} (briefings {settings.LLM_BRIEFING_EFFORT})",
        },
        {
            "name": "Tracing (LangSmith, optional)",
            "configured": bool(settings.LANGSMITH_TRACING and settings.LANGSMITH_API_KEY),
            "detail": f"project {settings.LANGSMITH_PROJECT}" if settings.LANGSMITH_TRACING else "tracing off",
        },
    ]


def ai_available():
    """Explanations and briefings need only the language model; retrieval falls back to the database filter."""
    return llm_configured()
