from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer
from app.config import EMBEDDING_MODEL_NAME

class EmbeddingService:
    """Generates normalized vector embeddings using Sentence Transformers."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
            cls._instance._model = None
        return cls._instance

    def _get_model(self) -> SentenceTransformer:
        if self._model is None:
            # Model loads once as a singleton
            self._model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        return self._model

    @property
    def dimension(self) -> int:
        model = self._get_model()
        if hasattr(model, "get_embedding_dimension"):
            return model.get_embedding_dimension()
        return model.get_sentence_embedding_dimension()

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """
        Embeds a list of strings and normalizes the vectors to unit length
        so that inner product equals cosine similarity.
        """
        if not texts:
            return np.empty((0, self.dimension), dtype=np.float32)

        model = self._get_model()
        embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        # L2-normalize vectors
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1e-12
        normalized = embeddings / norms
        return normalized.astype(np.float32)

    def embed_query(self, query: str) -> np.ndarray:
        """Embeds a single query string as a 2D float32 normalized vector."""
        return self.embed_texts([query])
