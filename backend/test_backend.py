import os
import sys
import tempfile
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

def create_sample_pdf(file_path: Path):
    """Creates a sample multi-page PDF using PyMuPDF."""
    import pymupdf as fitz
    doc = fitz.open()
    
    # Page 1
    page1 = doc.new_page()
    page1.insert_text(
        fitz.Point(50, 72),
        "Smart Document Assistant Architecture\n\n"
        "The Smart Document Assistant is designed with FastAPI, PyMuPDF, FAISS, and Gemini 3.5 Flash.\n"
        "It supports parsing PDF and TXT documents with source attribution and page citations.\n"
        "Embeddings are computed locally using Sentence Transformers.",
        fontsize=12
    )

    # Page 2
    page2 = doc.new_page()
    page2.insert_text(
        fitz.Point(50, 72),
        "Retention and Governance Policy\n\n"
        "All uploaded documents are retained in the local storage directory for exactly 30 days.\n"
        "Users can manually remove their documents at any time using the delete endpoint.\n"
        "All vectors are stored in a FAISS index with L2 normalized inner product distances.",
        fontsize=12
    )

    doc.save(str(file_path))
    doc.close()

def create_sample_txt(file_path: Path):
    """Creates a sample TXT file."""
    content = (
        "Embedding and Vector Search Specifications\n"
        "The primary embedding model is sentence-transformers/all-MiniLM-L6-v2.\n"
        "It outputs 384-dimensional dense vectors.\n"
        "The vector search utilizes FAISS IndexFlatIP to calculate cosine similarities directly.\n"
        "The confidence indicator provides evidence levels: High, Medium, and Low."
    )
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

def run_tests():
    print("==================================================")
    print("Running Smart Document Assistant Verification Suite")
    print("==================================================")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        pdf_file = temp_path / "architecture_policy.pdf"
        txt_file = temp_path / "embedding_specs.txt"

        create_sample_pdf(pdf_file)
        create_sample_txt(txt_file)

        print("[OK] Generated test PDF and TXT files.")

        # 1. Test Parsers
        from app.parser import DocumentParser
        pdf_parsed = DocumentParser.parse_pdf(pdf_file)
        assert pdf_parsed["page_count"] == 2, f"Expected 2 pages, got {pdf_parsed['page_count']}"
        assert len(pdf_parsed["segments"]) == 2, "Expected 2 segments for 2 pages"
        assert pdf_parsed["segments"][0]["page_number"] == 1
        assert pdf_parsed["segments"][1]["page_number"] == 2
        print(f"[OK] PDF Parser verified: {pdf_parsed['page_count']} pages parsed successfully.")

        txt_parsed = DocumentParser.parse_txt(txt_file)
        assert len(txt_parsed["segments"]) >= 1
        assert "all-MiniLM-L6-v2" in txt_parsed["segments"][0]["text"]
        print(f"[OK] TXT Parser verified: {txt_parsed['line_count']} lines parsed successfully.")

        # 2. Test Chunker
        from app.chunker import TextChunker
        chunker = TextChunker(chunk_size=300, chunk_overlap=50)
        pdf_chunks = chunker.chunk_document("doc1", "architecture_policy.pdf", "pdf", pdf_parsed)
        txt_chunks = chunker.chunk_document("doc2", "embedding_specs.txt", "txt", txt_parsed)

        assert len(pdf_chunks) >= 2, "Expected at least 2 chunks for PDF"
        # Check page numbers
        assert any(c.page_number == 1 for c in pdf_chunks)
        assert any(c.page_number == 2 for c in pdf_chunks)
        assert all(c.page_number is None for c in txt_chunks)
        print(f"[OK] Chunker verified: {len(pdf_chunks)} PDF chunks and {len(txt_chunks)} TXT chunks generated with page metadata.")

        # 3. Test Embeddings
        from app.embeddings import EmbeddingService
        embed_svc = EmbeddingService()
        assert embed_svc.dimension == 384, f"Expected dimension 384, got {embed_svc.dimension}"

        all_chunks = pdf_chunks + txt_chunks
        texts = [c.text for c in all_chunks]
        embeddings = embed_svc.embed_texts(texts)
        assert embeddings.shape == (len(all_chunks), 384), f"Embeddings shape {embeddings.shape} mismatch"
        print(f"[OK] EmbeddingService verified: {len(texts)} chunks embedded to shape {embeddings.shape}.")

        # 4. Test FAISS Vector Store
        from app.vector_store import VectorStore
        # Use an in-memory index for testing
        vstore = VectorStore(dimension=384)
        vstore.chunks = []
        import faiss
        vstore.index = faiss.IndexFlatIP(384)
        vstore.add_chunks(all_chunks, embeddings)
        assert vstore.index.ntotal == len(all_chunks)
        print(f"[OK] FAISS VectorStore verified: {vstore.index.ntotal} vectors indexed.")

        # 5. Test Retrieval for Specific Question
        from app.rag_service import RAGService
        rag = RAGService(vector_store=vstore, embedding_service=embed_svc)

        # Test query 1: Document retention period
        q1 = "How long are uploaded documents retained?"
        q1_vec = embed_svc.embed_query(q1)
        results1 = vstore.search(q1_vec, top_k=3)
        top_chunk, top_score = results1[0]
        
        assert "architecture_policy.pdf" in top_chunk.filename
        assert top_chunk.page_number == 2, f"Expected Page 2 for retention policy, got {top_chunk.page_number}"
        assert top_score > 0.45, f"Expected top score > 0.45, got {top_score}"
        print(f"[OK] Retrieval query 1 verified: Found in '{top_chunk.filename}' Page {top_chunk.page_number} with score {top_score:.3f}")



        # Test query 2: Unanswerable / Out of Domain query (Anti-Hallucination check)
        q_unanswerable = "What is the secret recipe for baking chocolate brownies in Paris?"
        resp_unanswerable = rag.answer_question(q_unanswerable, top_k=3)
        assert resp_unanswerable.is_answerable is False, "Expected is_answerable=False for out-of-domain query"
        assert "couldn't find information" in resp_unanswerable.answer.lower() or "not found" in resp_unanswerable.answer.lower() or "cannot answer" in resp_unanswerable.answer.lower()
        print(f"[OK] Anti-Hallucination Guardrail verified: Correctly rejected unanswerable query with response: '{resp_unanswerable.answer}'")

        # Test Chat History & Session ID
        session_id = "test-session-123"
        resp_session = rag.answer_question(q1, top_k=3, session_id=session_id)
        assert resp_session.conversation_history is not None
        print(f"[OK] Session-based Conversation Memory verified: history length = {len(resp_session.conversation_history)}")

        # Test Summarize Document
        sum_resp = rag.summarize_document("doc1", session_id=session_id)
        assert sum_resp.doc_id == "doc1"
        assert len(sum_resp.summary) > 0
        print(f"[OK] Document Summarization verified for doc1.")

        # Test Error Classification (Mock exception handling without calling Gemini API)
        from app.rag_service import classify_gemini_error
        
        # 1. Test 503 UNAVAILABLE
        err_503 = Exception("503 UNAVAILABLE. {'error': {'code': 503, 'message': 'This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later.', 'status': 'UNAVAILABLE'}}")
        cat_503, _ = classify_gemini_error(err_503)
        assert cat_503 == "service unavailable", f"Expected 'service unavailable', got '{cat_503}'"

        # 2. Test 404 Model Not Found
        err_404 = Exception("404 Model not found")
        cat_404, _ = classify_gemini_error(err_404)
        assert cat_404 == "model not available", f"Expected 'model not available', got '{cat_404}'"

        # 3. Test 429 Quota Exceeded
        err_429 = Exception("429 RESOURCE_EXHAUSTED: Quota exceeded for quota metric")
        cat_429, _ = classify_gemini_error(err_429)
        assert cat_429 == "quota/rate limit", f"Expected 'quota/rate limit', got '{cat_429}'"

        # 4. Test 401 Invalid Key
        err_401 = Exception("401 API_KEY_INVALID: Invalid API key provided")
        cat_401, _ = classify_gemini_error(err_401)
        assert cat_401 == "invalid API key", f"Expected 'invalid API key', got '{cat_401}'"

        print(f"[OK] Gemini Error Classifier verified: 503, 404, 429, 401 correctly categorized.")

        # Test document deletion
        removed = vstore.delete_document("doc1")
        assert removed == len(pdf_chunks)
        assert vstore.index.ntotal == len(txt_chunks)
        print(f"[OK] Vector Store document deletion verified: Removed {removed} chunks, {vstore.index.ntotal} remaining.")

    print("==================================================")
    print("ALL VERIFICATION SUITE TESTS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    run_tests()

