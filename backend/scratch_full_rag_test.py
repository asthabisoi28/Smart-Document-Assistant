import sys
import re
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.embeddings import EmbeddingService
from app.models import ChunkMetadata
import faiss

embed_svc = EmbeddingService()

# 1. Enhanced Chunker logic with Header Context Preservation
def chunk_text_smart(doc_id: str, filename: str, file_type: str, text: str, page_number=None, line_start=None, line_end=None, chunk_size=800, chunk_overlap=150):
    lines = text.splitlines()
    chunks = []
    
    current_doc_title = filename.replace('.pdf', '').replace('.txt', '').replace('_', ' ')
    current_header = ""
    
    paragraphs = []
    curr_p = []
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if curr_p:
                paragraphs.append("\n".join(curr_p))
                curr_p = []
            continue
        
        # Check if line is a header
        is_header = (
            stripped.startswith('#') or 
            stripped.startswith('==') or 
            stripped.startswith('Doc') or
            stripped.startswith('Project:') or 
            stripped.startswith('Section:') or
            (len(stripped) < 60 and stripped.endswith(':'))
        )
        if is_header:
            if curr_p:
                paragraphs.append("\n".join(curr_p))
                curr_p = []
            paragraphs.append(stripped)
        else:
            curr_p.append(line)
            
    if curr_p:
        paragraphs.append("\n".join(curr_p))

    # Group paragraphs into chunks
    curr_chunk_p = []
    curr_len = 0
    active_header = ""
    
    for p in paragraphs:
        is_header = p.startswith('#') or p.startswith('Project:') or p.startswith('Section:') or (len(p) < 60 and p.endswith(':'))
        if is_header:
            active_header = p.lstrip('#').strip()
            
        p_len = len(p)
        if curr_len + p_len > chunk_size and curr_chunk_p:
            chunk_body = "\n".join(curr_chunk_p)
            context_prefix = f"[{current_doc_title}"
            if active_header and active_header.lower() not in chunk_body.lower():
                context_prefix += f" | {active_header}"
            context_prefix += "]\n"
            
            full_chunk_text = context_prefix + chunk_body
            chunks.append(full_chunk_text)
            
            # Keep overlap paragraph if available
            curr_chunk_p = [curr_chunk_p[-1]] if len(curr_chunk_p) > 1 else []
            curr_len = sum(len(x) for x in curr_chunk_p)

        curr_chunk_p.append(p)
        curr_len += p_len
        
    if curr_chunk_p:
        chunk_body = "\n".join(curr_chunk_p)
        context_prefix = f"[{current_doc_title}"
        if active_header and active_header.lower() not in chunk_body.lower():
            context_prefix += f" | {active_header}"
        context_prefix += "]\n"
        chunks.append(context_prefix + chunk_body)
        
    return chunks

# Test document
sample_doc_text = """
# Project Specification: SmartHire Platform

## Executive Summary
SmartHire is a next-generation automated candidate screening and recruitment platform designed to streamline hiring workflows.

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

chunks = chunk_text_smart("doc1", "SmartHire_Project_Spec.txt", "txt", sample_doc_text)

print(f"Generated {len(chunks)} smart chunks:\n")
for i, c in enumerate(chunks):
    print(f"--- Chunk {i+1} ---")
    print(c)
    print()

# 2. Multi-query Retrieval
user_query = "what tech stacks are used in SmartHire project?"

# Generate query variations
query_variations = [
    user_query,
    "SmartHire project tech stack technologies tools built using architecture",
    "what technologies and tools are used in SmartHire project?"
]

# Embed document chunks
chunk_vecs = embed_svc.embed_texts(chunks)

print(f"=== Multi-Query Retrieval Results for '{user_query}' ===")
for i, c in enumerate(chunks):
    scores = []
    for q_var in query_variations:
        q_vec = embed_svc.embed_query(q_var)
        sim = float((q_vec @ chunk_vecs[i:i+1].T)[0, 0])
        scores.append(sim)
    max_sim = max(scores)
    print(f"Chunk {i+1} Max Score: {max_sim:.4f} (scores: {[round(s, 4) for s in scores]})")
