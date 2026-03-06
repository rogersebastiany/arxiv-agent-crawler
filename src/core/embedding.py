"""SentenceTransformers embedding wrapper."""

from __future__ import annotations

import numpy as np
from sentence_transformers import SentenceTransformer

DEFAULT_MODEL = "BAAI/bge-small-en-v1.5"


class EmbeddingService:
    """Thin wrapper around SentenceTransformers for lazy loading and reuse."""

    def __init__(self, model_name: str = DEFAULT_MODEL):
        self._model_name = model_name
        self._model: SentenceTransformer | None = None

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(self._model_name)
        return self._model

    def encode(self, texts: list[str], normalize: bool = True) -> np.ndarray:
        """Encode a list of texts into embeddings."""
        return self.model.encode(texts, normalize_embeddings=normalize).astype(np.float32)

    def encode_query(self, query: str, normalize: bool = True) -> np.ndarray:
        """Encode a single query string."""
        return self.encode([query], normalize=normalize)
