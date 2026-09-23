import os
import json
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import List

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import (
    DOCS_PATH,
    UPLOADS_DIR,
    get_gemini_api_key,
    GEMINI_MODEL_NAME,
    EMBEDDING_MODEL_NAME
)
from app.models import (
    DocumentInfo,
    QueryRequest,
    QueryResponse,
    SummarizeRequest,
    SummarizeResponse
)
from app.parser import DocumentParser
from app.chunker import TextChunker
from app.embeddings import EmbeddingService
from app.vector_store import VectorStore
from app.rag_service import RAGService

app = FastAPI(
    title="Smart Document Assistant API",
    description="RAG Document Assistant with FAISS, PyMuPDF, Sentence Transformers, and Gemini 3.5 Flash",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize core services
embedding_service = EmbeddingService()
vector_store = VectorStore(dimension=384)
chunker = TextChunker()
rag_service = RAGService(vector_store=vector_store, embedding_service=embedding_service)

def load_documents_metadata() -> List[DocumentInfo]:
    if DOCS_PATH.exists():
        try:
            with open(DOCS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            return [DocumentInfo(**item) for item in data]
        except Exception:
            return []
    return []

def save_documents_metadata(docs: List[DocumentInfo]):
    with open(DOCS_PATH, "w", encoding="utf-8") as f:
        json.dump([d.model_dump() for d in docs], f, ensure_ascii=False, indent=2)

@app.get("/api/health")
def health_check():
    docs = load_documents_metadata()
    api_key = get_gemini_api_key()
    has_api_key = bool(api_key)
    return {
        "status": "healthy",
        "total_documents": len(docs),
        "total_chunks": len(vector_store.chunks),
        "embedding_model": EMBEDDING_MODEL_NAME,
        "gemini_model": GEMINI_MODEL_NAME,
        "gemini_api_key_configured": has_api_key
    }

@app.get("/api/documents", response_model=List[DocumentInfo])
def get_documents():
    """Returns list of uploaded documents and their processing metadata."""
    return load_documents_metadata()

@app.post("/api/upload", response_model=List[DocumentInfo])
async def upload_documents(files: List[UploadFile] = File(...)):
    """Uploads and indexes one or more PDF or TXT documents."""
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    docs = load_documents_metadata()
    processed_new_docs: List[DocumentInfo] = []

    for file in files:
        filename = file.filename
        ext = filename.split(".")[-1].lower() if "." in filename else ""
        if ext not in ["pdf", "txt"]:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format for '{filename}'. Only PDF and TXT are supported."
            )

        doc_id = str(uuid.uuid4())[:8]
        saved_filename = f"{doc_id}_{filename}"
        saved_file_path = UPLOADS_DIR / saved_filename

        # Write uploaded file to disk
        with open(saved_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_size = os.path.getsize(saved_file_path)

        try:
            # 1. Parse document
            parsed = DocumentParser.parse_file(saved_file_path, ext)

            # 2. Chunk document
            chunks = chunker.chunk_document(
                doc_id=doc_id,
                filename=filename,
                file_type=ext,
                parsed_data=parsed
            )

            # 3. Embed chunks & Add to FAISS index
            if chunks:
                texts = [c.text for c in chunks]
                embeddings = embedding_service.embed_texts(texts)
                vector_store.add_chunks(chunks, embeddings)

            doc_info = DocumentInfo(
                id=doc_id,
                filename=filename,
                file_type=ext,
                file_size=file_size,
                upload_timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                page_count=parsed.get("page_count"),
                chunk_count=len(chunks),
                status="indexed"
            )

            docs.append(doc_info)
            processed_new_docs.append(doc_info)

        except Exception as e:
            if saved_file_path.exists():
                saved_file_path.unlink()
            raise HTTPException(status_code=500, detail=f"Failed to process {filename}: {str(e)}")

    save_documents_metadata(docs)
    return processed_new_docs

@app.delete("/api/documents/{doc_id}")
def delete_document(doc_id: str):
    """Deletes a document from metadata, filesystem, and FAISS index."""
    docs = load_documents_metadata()
    target = next((d for d in docs if d.id == doc_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Document not found")

    # 1. Remove chunks from vector store
    vector_store.delete_document(doc_id)

    # 2. Delete raw file
    prefix = f"{doc_id}_"
    for f in UPLOADS_DIR.glob(f"{prefix}*"):
        try:
            f.unlink()
        except Exception:
            pass

    # 3. Update documents metadata
    updated_docs = [d for d in docs if d.id != doc_id]
    save_documents_metadata(updated_docs)

    return {"message": f"Document {target.filename} deleted successfully", "doc_id": doc_id}

@app.post("/api/query", response_model=QueryResponse)
def query_documents(request: QueryRequest):
    """Answers questions based on indexed document chunks with conversation context."""
    return rag_service.answer_question(
        request.question,
        top_k=request.top_k or 5,
        session_id=request.session_id
    )

@app.post("/api/summarize", response_model=SummarizeResponse)
def summarize_document(request: SummarizeRequest):
    """Generates a concise summary for a specific uploaded document."""
    return rag_service.summarize_document(request.doc_id, session_id=request.session_id)

