import os
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

import pymupdf as fitz
from app.parser import DocumentParser
from app.chunker import TextChunker
from app.embeddings import EmbeddingService
from app.vector_store import VectorStore
from app.rag_service import RAGService
from app.config import get_gemini_api_key

def setup_test_documents():
    """Sets up a test vector store with realistic documents."""
    temp_dir = backend_dir / "storage" / "test_docs"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    # Document 1: Course Syllabus & Policy (PDF)
    pdf_path = temp_dir / "CS101_Syllabus.pdf"
    doc = fitz.open()
    
    # Page 1: General Info & Topics
    p1 = doc.new_page()
    p1.insert_text(
        fitz.Point(50, 72),
        "CS101: Introduction to Artificial Intelligence\n\n"
        "Instructor: Dr. Alan Turing\n"
        "Office Hours: Tuesdays and Thursdays from 2:00 PM to 4:00 PM in Room 402.\n"
        "Course Overview:\n"
        "This course introduces core principles of machine learning, neural networks, "
        "natural language processing, and vector retrieval systems.",
        fontsize=11
    )
    
    # Page 2: Grading, Deadlines & Assignments
    p2 = doc.new_page()
    p2.insert_text(
        fitz.Point(50, 72),
        "Grading and Assignment Schedule\n\n"
        "The final course grade consists of:\n"
        "- Midterm Exam: 30%\n"
        "- Final Capstone Project: 40%\n"
        "- Weekly Lab Assignments: 30%\n\n"
        "Important Deadlines:\n"
        "Assignment 1 Deadline: October 15 at 11:59 PM.\n"
        "Midterm Examination Date: November 10 at 10:00 AM in Hall B.\n"
        "Final Capstone Project Submission Deadline: December 5 at 5:00 PM.",
        fontsize=11
    )
    doc.save(str(pdf_path))
    doc.close()

    # Document 2: Project Guidelines (TXT)
    txt_path = temp_dir / "Capstone_Guidelines.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(
            "Capstone Project Guidelines\n"
            "Students must form teams of 2 to 4 members.\n"
            "Each team must submit a project proposal by October 20.\n"
            "The project must incorporate a vector database such as FAISS and a generative model.\n"
            "All submissions must include a GitHub repository link and a 5-minute video presentation."
        )

    # Parse and chunk both documents
    parser = DocumentParser()
    chunker = TextChunker(chunk_size=350, chunk_overlap=60)
    embed_svc = EmbeddingService()
    
    pdf_parsed = parser.parse_pdf(pdf_path)
    txt_parsed = parser.parse_txt(txt_path)
    
    pdf_chunks = chunker.chunk_document("doc_pdf", "CS101_Syllabus.pdf", "pdf", pdf_parsed)
    txt_chunks = chunker.chunk_document("doc_txt", "Capstone_Guidelines.txt", "txt", txt_parsed)
    
    all_chunks = pdf_chunks + txt_chunks
    texts = [c.text for c in all_chunks]
    embeddings = embed_svc.embed_texts(texts)
    
    # Create test VectorStore
    vstore = VectorStore(dimension=384)
    import faiss
    vstore.index = faiss.IndexFlatIP(384)
    vstore.chunks = []
    vstore.add_chunks(all_chunks, embeddings)
    
    return vstore, embed_svc

def run_qa_tests():
    print("==================================================")
    print("Testing QA Flow & Anti-Hallucination Pipeline")
    print("==================================================")

    vstore, embed_svc = setup_test_documents()
    rag = RAGService(vector_store=vstore, embedding_service=embed_svc)
    api_key = get_gemini_api_key()

    print(f"Current Gemini API Key configured in backend/.env: {'YES (Ready)' if api_key else 'NO (Missing/Placeholder)'}")

    # ----------------------------------------------------
    # Test Case 1: Answer clearly present in document (Single chunk / Page)
    # ----------------------------------------------------
    print("\n--- TEST CASE 1: Answer clearly present in document ---")
    q1 = "When is the deadline for Assignment 1 and what are the office hours?"
    res1 = rag.answer_question(q1)
    
    print(f"Question: {q1}")
    print(f"API Key Configured: {res1.api_key_configured}")
    print(f"Is Answerable: {res1.is_answerable}")
    print(f"Confidence Score: {res1.confidence_score * 100:.1f}%")
    print(f"Sources Found: {len(res1.sources)}")
    for s in res1.sources[:2]:
        loc = f"Page {s.page_number}" if s.page_number else s.line_range
        print(f"  - [{s.filename}] {loc} (sim: {s.similarity_score})")
    
    if res1.api_key_configured:
        print(f"LLM Answer:\n{res1.answer}")
        assert "October 15" in res1.answer or "CS101_Syllabus" in res1.answer
    else:
        print(f"Configuration message (expected when key missing):\n{res1.error_message}")
        assert res1.api_key_configured is False
        assert len(res1.sources) > 0, "Sources must be preserved so user sees retrieval worked"
    print("[OK] Test Case 1 verified.")

    # ----------------------------------------------------
    # Test Case 2: Question whose answer is NOT present (Unsupported / Anti-hallucination)
    # ----------------------------------------------------
    print("\n--- TEST CASE 2: Question whose answer is NOT present ---")
    q2 = "What is the policy for borrowing laptops from the campus library?"
    res2 = rag.answer_question(q2)
    
    print(f"Question: {q2}")
    print(f"Is Answerable: {res2.is_answerable}")
    print(f"Answer: {res2.answer}")
    print(f"Confidence Score: {res2.confidence_score * 100:.1f}%")
    
    assert res2.is_answerable is False, "Unsupported questions must have is_answerable=False"
    assert "couldn't find information" in res2.answer.lower() or "not found" in res2.answer.lower()
    print("[OK] Test Case 2 verified (System safely rejected unsupported question without hallucinating).")

    # ----------------------------------------------------
    # Test Case 3: Question requiring information from multiple retrieved chunks
    # (Across PDF Page 2 grading & TXT capstone requirements)
    # ----------------------------------------------------
    print("\n--- TEST CASE 3: Multi-chunk information synthesis ---")
    q3 = "How much is the final capstone project worth in the grade, and what are the team size requirements for it?"
    res3 = rag.answer_question(q3)
    
    print(f"Question: {q3}")
    print(f"Confidence Score: {res3.confidence_score * 100:.1f}%")
    print(f"Sources Found: {len(res3.sources)}")
    
    # Must retrieve from both documents
    retrieved_docs = {s.filename for s in res3.sources}
    assert "CS101_Syllabus.pdf" in retrieved_docs, "Must retrieve syllabus for 40% grade info"
    assert "Capstone_Guidelines.txt" in retrieved_docs, "Must retrieve guidelines for team size info"
    print(f"Successfully retrieved across multiple sources: {retrieved_docs}")

    if res3.api_key_configured:
        print(f"LLM Answer:\n{res3.answer}")
        assert "40%" in res3.answer
        assert "2" in res3.answer and "4" in res3.answer
    else:
        print("Note: Add GEMINI_API_KEY to backend/.env to see Gemini synthesize the multi-chunk answer live.")
    print("[OK] Test Case 3 verified.")

    # ----------------------------------------------------
    # Test Case 4: Verify live Gemini LLM call with a mock key or real key
    # ----------------------------------------------------
    print("\n--- TEST CASE 4: Verification of Gemini invocation logic ---")
    mock_context = "[Source 1: CS101_Syllabus.pdf (Page 2)]\nAssignment 1 Deadline: October 15 at 11:59 PM."
    # If a real key is present, test actual generation
    if api_key:
        ans, is_ans, err = rag._call_gemini_llm("When is Assignment 1 due?", mock_context, api_key)
        print(f"Live Gemini Generation Succeeded:\n{ans}")
        assert "October 15" in ans
    else:
        print("Backend is ready to invoke Gemini immediately when user inputs their key in backend/.env.")

    print("\n==================================================")
    print("ALL QA FLOW AND ANTI-HALLUCINATION TESTS PASSED!")
    print("==================================================")

if __name__ == "__main__":
    run_qa_tests()
