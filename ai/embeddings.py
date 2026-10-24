"""Hugging Face Inference Providers embeddings as a LangChain `Embeddings`."""

from django.conf import settings
from langchain_core.embeddings import Embeddings


class EmbeddingError(Exception):
    """The embedding provider failed or returned vectors of the wrong size."""


class HFInferenceEmbeddings(Embeddings):
    def __init__(self, model, token, provider, dimensions, timeout=15):
        from huggingface_hub import InferenceClient

        self.model = model
        self.dimensions = dimensions
        self._client = InferenceClient(provider=provider, api_key=token, timeout=timeout)

    def _embed(self, texts):
        try:
            vectors = self._client.feature_extraction(texts, model=self.model)
        except Exception as exc:  # noqa: BLE001 - provider errors vary by transport
            raise EmbeddingError(f"Embedding request failed: {type(exc).__name__}") from exc
        if vectors.ndim != 2 or vectors.shape != (len(texts), self.dimensions):
            raise EmbeddingError(f"Expected {len(texts)}x{self.dimensions} vectors, got shape {vectors.shape}.")
        return vectors.tolist()

    def embed_documents(self, texts):
        return self._embed(list(texts)) if texts else []

    def embed_query(self, text):
        return self._embed([text])[0]


def embeddings_configured():
    return bool(settings.HF_TOKEN and settings.HF_EMBEDDING_MODEL and settings.EMBEDDING_DIMENSIONS)


def get_embeddings():
    return HFInferenceEmbeddings(
        model=settings.HF_EMBEDDING_MODEL,
        token=settings.HF_TOKEN,
        provider=settings.HF_EMBEDDING_PROVIDER,
        dimensions=settings.EMBEDDING_DIMENSIONS,
    )
