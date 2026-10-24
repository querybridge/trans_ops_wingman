"""Pinecone semantic ranking of procedure sections, through LangChain.

The database decides which procedure documents apply (customer, issue type,
region, effective dates). Pinecone only ranks sections inside that set, with
its own customer filter as a second guard, and every result is checked
against the allowed set again before use. Any failure raises
`VectorUnavailable` so callers fall back to the database order.
"""

import logging
from functools import lru_cache

from django.conf import settings

from .embeddings import EmbeddingError, embeddings_configured, get_embeddings

logger = logging.getLogger(__name__)

NAMESPACE = "procedures"


class VectorUnavailable(Exception):
    """Vector search is not configured or failed; use the database order."""


def vector_configured():
    return bool(settings.PINECONE_API_KEY) and embeddings_configured()


def _client():
    from pinecone import Pinecone

    return Pinecone(api_key=settings.PINECONE_API_KEY)


def ensure_index(create=False):
    """Check the index exists with the configured dimension, creating it if asked."""
    from pinecone import ServerlessSpec

    pc = _client()
    name = settings.PINECONE_INDEX_NAME
    if not pc.has_index(name):
        if not create:
            raise VectorUnavailable(f"Pinecone index '{name}' does not exist. Run ingest_vectors --create-index.")
        pc.create_index(
            name=name,
            dimension=settings.EMBEDDING_DIMENSIONS,
            metric="cosine",
            spec=ServerlessSpec(cloud=settings.PINECONE_CLOUD, region=settings.PINECONE_REGION),
        )
    description = pc.describe_index(name)
    if description.dimension != settings.EMBEDDING_DIMENSIONS:
        raise VectorUnavailable(
            f"Index '{name}' has dimension {description.dimension}, but EMBEDDING_DIMENSIONS is {settings.EMBEDDING_DIMENSIONS}."
        )
    return description


@lru_cache(maxsize=1)
def _store(api_key, index_name):
    from langchain_pinecone import PineconeVectorStore

    index = _client().Index(index_name)
    return PineconeVectorStore(index=index, embedding=get_embeddings(), namespace=NAMESPACE)


def get_store():
    if not vector_configured():
        raise VectorUnavailable("Pinecone or Hugging Face is not configured.")
    return _store(settings.PINECONE_API_KEY, settings.PINECONE_INDEX_NAME)


def chunk_metadata(chunk):
    doc = chunk.document
    return {
        "chunk_id": chunk.chunk_id,
        "document_id": doc.document_id,
        "version": doc.version,
        "customer_id": doc.customer.customer_id if doc.customer_id else "shared",
        "issue_type": doc.issue_type,
        "region": doc.region or "all",
        "section": chunk.section,
    }


def sync_procedures(create_index=False):
    """Upsert every procedure chunk by its stable ID and delete vectors for removed chunks."""
    from operations.models import ProcedureChunk

    ensure_index(create=create_index)
    store = get_store()
    chunks = list(ProcedureChunk.objects.select_related("document__customer").order_by("chunk_id"))
    ids = [c.chunk_id for c in chunks]
    texts = [f"{c.document.title}: {c.section}\n{c.text}" for c in chunks]
    store.add_texts(texts, metadatas=[chunk_metadata(c) for c in chunks], ids=ids, async_req=False)
    existing = {vid for page in store.index.list(namespace=NAMESPACE) for vid in page}
    stale = sorted(existing - set(ids))
    if stale:
        store.index.delete(ids=stale, namespace=NAMESPACE)
    return {"upserted": len(ids), "removed": len(stale)}


def rank_sections(query, allowed_chunk_ids, customer_id, k):
    """[(chunk_id, score)] for the most relevant allowed sections, best first."""
    allowed = set(allowed_chunk_ids)
    if not allowed:
        return []
    store = get_store()
    scope = sorted({customer_id, "shared"} - {None})
    try:
        results = store.similarity_search_with_score(
            query,
            k=k,
            filter={"chunk_id": {"$in": sorted(allowed)}, "customer_id": {"$in": scope}},
        )
    except EmbeddingError as exc:
        raise VectorUnavailable(str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 - Pinecone transport errors vary
        logger.warning("Pinecone query failed: %s", type(exc).__name__)
        raise VectorUnavailable("Pinecone query failed.") from exc
    ranked = []
    for doc, score in results:
        chunk_id = doc.metadata.get("chunk_id")
        if chunk_id in allowed:
            ranked.append((chunk_id, float(score)))
        else:
            logger.error("Pinecone returned a section outside the allowed set: %s", chunk_id)
    if not ranked:
        raise VectorUnavailable("Pinecone returned no allowed sections; is the index loaded?")
    return ranked
