import json
import logging
from pathlib import Path
from typing import List, Tuple, Dict, Any
import numpy as np
import faiss

from app.models import ChunkMetadata
from app.config import INDEX_PATH, CHUNKS_PATH, DOCS_PATH, UPLOADS_DIR

logger = logging.getLogger(__name__)

class VectorStore:
    """Manages FAISS IndexFlatIP vector index with persistence and chunk metadata mapping."""

    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.chunks: List[ChunkMetadata] = []
        self.index: faiss.IndexFlatIP = faiss.IndexFlatIP(dimension)
        self.load()
        self._prune_stale_chunks_on_startup()
        self._clean_documents_metadata()

    def add_chunks(self, chunks: List[ChunkMetadata], embeddings: np.ndarray):
        """Adds chunks and their normalized embedding vectors to FAISS and memory."""
        if len(chunks) == 0:
            return

        if embeddings.shape[0] != len(chunks):
            raise ValueError(f"Mismatch: {len(chunks)} chunks vs {embeddings.shape[0]} embeddings")

        if embeddings.shape[1] != self.dimension:
            raise ValueError(f"Embedding dimension {embeddings.shape[1]} does not match index {self.dimension}")

        # Add to FAISS index
        self.index.add(embeddings)
        self.chunks.extend(chunks)
        self.save()
        logger.info(f"Added {len(chunks)} chunks to FAISS index. Total chunks now: {len(self.chunks)}")

    def search(self, query_vector: np.ndarray, top_k: int = 5) -> List[Tuple[ChunkMetadata, float]]:
        """
        Searches FAISS for top-k chunks with highest cosine similarity.
        Returns list of (ChunkMetadata, similarity_score).
        """
        if self.index.ntotal == 0 or len(self.chunks) == 0:
            return []

        actual_k = min(top_k, self.index.ntotal)
        scores, indices = self.index.search(query_vector, actual_k)

        results: List[Tuple[ChunkMetadata, float]] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx != -1 and idx < len(self.chunks):
                # Cosine similarity score (can be clamped to [0, 1] for display)
                similarity = float(np.clip(score, 0.0, 1.0))
                results.append((self.chunks[idx], similarity))

        return results

    def get_chunks_by_doc_id(self, doc_id: str) -> List[ChunkMetadata]:
        """Returns all chunks associated with doc_id."""
        return [c for c in self.chunks if c.doc_id == doc_id]

    def delete_document(self, doc_id: str) -> int:
        """Removes all chunks associated with doc_id and rebuilds the FAISS index."""
        remaining_chunks = [c for c in self.chunks if c.doc_id != doc_id]
        removed_count = len(self.chunks) - len(remaining_chunks)

        if removed_count == 0:
            return 0

        self.chunks = remaining_chunks

        # Rebuild FAISS index from remaining chunks
        self.index = faiss.IndexFlatIP(self.dimension)
        if len(self.chunks) > 0:
            from app.embeddings import EmbeddingService
            texts = [c.text for c in self.chunks]
            embeddings = EmbeddingService().embed_texts(texts)
            self.index.add(embeddings)

        self.save()
        logger.info(f"Deleted document {doc_id} ({removed_count} chunks removed).")
        return removed_count

    def save(self):
        """Saves FAISS index to binary file and chunks metadata to JSON."""
        try:
            faiss.write_index(self.index, str(INDEX_PATH))
            chunks_data = [chunk.model_dump() for chunk in self.chunks]
            with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
                json.dump(chunks_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist vector store: {e}")

    def load(self):
        """Loads FAISS index from disk if present; otherwise initializes empty index."""
        if INDEX_PATH.exists() and CHUNKS_PATH.exists():
            try:
                self.index = faiss.read_index(str(INDEX_PATH))
                with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
                    chunks_data = json.load(f)
                self.chunks = [ChunkMetadata(**item) for item in chunks_data]
                logger.info(f"Loaded existing FAISS index with {self.index.ntotal} vectors and {len(self.chunks)} chunk records.")
            except Exception as e:
                logger.warning(f"Could not load existing index from {INDEX_PATH}: {e}. Creating fresh index.")
                self.index = faiss.IndexFlatIP(self.dimension)
                self.chunks = []
        else:
            self.index = faiss.IndexFlatIP(self.dimension)
            self.chunks = []

    def _prune_stale_chunks_on_startup(self):
        """Remove chunks whose document IDs are not present in the current documents metadata.
        Called during initialization to ensure only active document chunks remain.
        """
        from app.config import DOCS_PATH
        if not DOCS_PATH.exists():
            return
        try:
            with open(DOCS_PATH, "r", encoding="utf-8") as f:
                docs_data = json.load(f)
            active_doc_ids = {doc.get("id") for doc in docs_data if isinstance(doc, dict)}
        except Exception as e:
            logger.warning(f"Failed to read documents metadata for stale-chunk pruning: {e}")
            return
        original_count = len(self.chunks)
        self.chunks = [c for c in self.chunks if c.doc_id in active_doc_ids]
        pruned = original_count - len(self.chunks)
        if pruned > 0:
            self.index = faiss.IndexFlatIP(self.dimension)
            if self.chunks:
                from app.embeddings import EmbeddingService
                texts = [c.text for c in self.chunks]
                embeddings = EmbeddingService().embed_texts(texts)
                self.index.add(embeddings)
            self.save()
            logger.info(f"Pruned {pruned} stale chunks from FAISS index during startup.")
    def _clean_documents_metadata(self):
        """Remove entries from documents.json whose files are missing and clean associated chunks.
        Also removes any chunks whose parent document was deleted.
        """
        if not DOCS_PATH.exists():
            return
        try:
            with open(DOCS_PATH, "r", encoding="utf-8") as f:
                docs_data = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to read documents metadata for cleanup: {e}")
            return
        # Determine which document files actually exist
        existing_files = {p.name for p in UPLOADS_DIR.iterdir() if p.is_file()}
        cleaned_docs = []
        removed_ids = set()
        for doc in docs_data:
            doc_id = doc.get("id")
            filename = doc.get("filename")
            expected_name = f"{doc_id}_{filename}" if (doc_id and filename) else None
            file_exists = (
                (expected_name and expected_name in existing_files) or
                (doc_id and any(f.startswith(f"{doc_id}_") for f in existing_files))
            )
            if file_exists:
                cleaned_docs.append(doc)
            else:
                if doc_id:
                    removed_ids.add(doc_id)
        # Remove chunks belonging to removed documents
        if removed_ids:
            original_chunk_count = len(self.chunks)
            self.chunks = [c for c in self.chunks if c.doc_id not in removed_ids]
            if len(self.chunks) != original_chunk_count:
                self.index = faiss.IndexFlatIP(self.dimension)
                if self.chunks:
                    from app.embeddings import EmbeddingService
                    texts = [c.text for c in self.chunks]
                    embeddings = EmbeddingService().embed_texts(texts)
                    self.index.add(embeddings)
                self.save()
                logger.info(f"Cleaned {original_chunk_count - len(self.chunks)} chunks of removed documents.")
        # Persist cleaned documents metadata
        try:
            with open(DOCS_PATH, "w", encoding="utf-8") as f:
                json.dump(cleaned_docs, f, ensure_ascii=False, indent=2)
            logger.info(f"Cleaned documents metadata; {len(docs_data) - len(cleaned_docs)} stale entries removed.")
        except Exception as e:
            logger.warning(f"Failed to write cleaned documents metadata: {e}")
