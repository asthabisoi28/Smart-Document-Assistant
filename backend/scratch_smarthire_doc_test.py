import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.embeddings import EmbeddingService
from app.parser import DocumentParser
from app.chunker import TextChunker
import numpy as np

embed_svc = EmbeddingService()

# Sample document text simulating a real project spec document
sample_doc_text = """
# Project Specification: SmartHire Platform

## Executive Summary
SmartHire is an next-generation automated candidate screening and recruitment platform designed to streamline hiring workflows.

## System Architecture & Technical Stack
The SmartHire project is built using modern cloud-native architecture:
- Frontend: React 18, TypeScript, TailwindCSS
- Backend: Python 3.11, FastAPI, Celery
- Database: PostgreSQL, Redis
- Machine Learning: PyTorch, HuggingFace Transformers for resume parsing
- Infrastructure: Docker, Kubernetes, AWS ECS

## Deployment Policy
Deploys automatically via GitHub Actions CI/CD pipeline upon merging to main branch.
"""

# Let's inspect how the current chunker chunks this document:
chunker = TextChunker(chunk_size=300, chunk_overlap=60)
parsed = {"page_number": None, "line_start": 1, "line_end": 20, "segments": [{"text": sample_doc_text}]}
chunks = chunker.chunk_document("doc101", "smarthire_spec.txt", "txt", parsed)

print(f"Total chunks generated: {len(chunks)}")
for i, c in enumerate(chunks):
    print(f"\n--- Chunk {i+1} ---")
    print(repr(c.text))
    
    q_vec = embed_svc.embed_query("what tech stacks are used in SmartHire project?")
    c_vec = embed_svc.embed_texts([c.text])
    score = float((q_vec @ c_vec.T)[0, 0])
    print(f"Similarity Score: {score:.4f}")
