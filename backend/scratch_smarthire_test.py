import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.embeddings import EmbeddingService
from app.vector_store import VectorStore
from app.chunker import TextChunker
from app.models import ChunkMetadata
import faiss

embed_svc = EmbeddingService()

queries = [
    "what tech stacks are used in SmartHire project?",
    "what tech stack is used in SmartHire project?",
    "what technologies are used in SmartHire project?",
    "SmartHire tech stack",
    "SmartHire technologies tools",
]

doc_texts = [
    "SmartHire project tech stack: React, Node.js, Express, MongoDB, Python, and Docker.",
    "The SmartHire project is built using React on the frontend and FastAPI on the backend with PostgreSQL for the database.",
    "Technologies and tools used in SmartHire: React.js, Python, PyTorch, Docker, Kubernetes, and AWS.",
    "SmartHire platform overview: An AI-powered hiring assistant that simplifies candidate screening and interview scheduling."
]

print("=== Direct Query Embeddings Similarity Scores ===")
for q in queries:
    q_vec = embed_svc.embed_query(q)
    print(f"\nQuery: '{q}'")
    for doc in doc_texts:
        d_vec = embed_svc.embed_query(doc)
        sim = float((q_vec @ d_vec.T)[0, 0])
        print(f"  Score: {sim:.4f} | Doc: '{doc[:60]}...'")
