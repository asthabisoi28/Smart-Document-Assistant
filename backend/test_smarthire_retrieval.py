import pytest
import faiss
from app.parser import DocumentParser
from app.chunker import TextChunker
from app.embeddings import EmbeddingService
from app.vector_store import VectorStore
from app.rag_service import RAGService

def test_smarthire_tech_stack_retrieval(tmp_path):
    # 1. Create a sample document containing a SmartHire tech-stack statement
    doc_content = (
        "# Project Specification: SmartHire Platform\n\n"
        "## Executive Summary\n"
        "SmartHire is an automated candidate screening platform designed to streamline hiring.\n\n"
        "## System Architecture & Tech Stack\n"
        "The SmartHire project is built using modern technologies:\n"
        "- Frontend: React 18, TypeScript, TailwindCSS\n"
        "- Backend: Python 3.11, FastAPI, PostgreSQL\n"
        "- Machine Learning: PyTorch, HuggingFace Transformers\n"
        "- Infrastructure: Docker, Kubernetes, AWS ECS\n"
    )
    
    file_path = tmp_path / "smarthire_spec.txt"
    file_path.write_text(doc_content, encoding="utf-8")

    # 2. Parse & Chunk
    parsed = DocumentParser.parse_txt(file_path)
    chunker = TextChunker()
    chunks = chunker.chunk_document("doc_smarthire_1", "smarthire_spec.txt", "txt", parsed)
    
    assert len(chunks) > 0

    # 3. Embed & Index in FAISS
    embed_svc = EmbeddingService()
    texts = [c.text for c in chunks]
    embeddings = embed_svc.embed_texts(texts)

    vstore = VectorStore(dimension=embed_svc.dimension)
    vstore.chunks = []
    vstore.index = faiss.IndexFlatIP(embed_svc.dimension)
    vstore.add_chunks(chunks, embeddings)

    # 4. Query RAG Service for SmartHire tech stack
    rag = RAGService(vector_store=vstore, embedding_service=embed_svc)
    query = "what tech stacks are used in SmartHire project?"
    
    response = rag.answer_question(question=query, top_k=3)
    
    # Assert retrieval succeeded and relevant chunks are present
    assert len(response.sources) > 0, "Expected retrieved sources for SmartHire query"
    top_source = response.sources[0]
    
    # Verify the chunk contains the expected tech stack content
    assert any(tech in top_source.snippet for tech in ["React", "FastAPI", "Python", "PostgreSQL"]), \
        f"Expected tech stack details in snippet, got: {top_source.snippet}"
    
    # Verify similarity score is well above anti-hallucination threshold
    assert top_source.similarity_score >= 0.50, f"Expected similarity score >= 0.50, got {top_source.similarity_score}"
    assert response.confidence_score > 0.40, f"Expected confidence score > 0.40, got {response.confidence_score}"

def test_unrelated_query_returns_no_information(tmp_path):
    # If the information genuinely does not exist, return unanswerable / 0 confidence
    doc_content = "SmartHire is a tool for scheduling recruitment interviews."
    file_path = tmp_path / "interview_info.txt"
    file_path.write_text(doc_content, encoding="utf-8")

    parsed = DocumentParser.parse_txt(file_path)
    chunker = TextChunker()
    chunks = chunker.chunk_document("doc_2", "interview_info.txt", "txt", parsed)

    embed_svc = EmbeddingService()
    embeddings = embed_svc.embed_texts([c.text for c in chunks])

    vstore = VectorStore(dimension=embed_svc.dimension)
    vstore.chunks = []
    vstore.index = faiss.IndexFlatIP(embed_svc.dimension)
    vstore.add_chunks(chunks, embeddings)

    rag = RAGService(vector_store=vstore, embedding_service=embed_svc)
    query = "what is the financial budget for NASA space mission Artemis?"
    
    response = rag.answer_question(question=query, top_k=3)
    assert response.is_answerable is False
    assert response.confidence_score == 0.0
    assert "couldn't find information" in response.answer.lower()
