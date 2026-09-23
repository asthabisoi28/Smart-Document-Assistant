from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class DocumentInfo(BaseModel):
    id: str
    filename: str
    file_type: Literal["pdf", "txt"]
    file_size: int
    upload_timestamp: str
    page_count: Optional[int] = None
    chunk_count: int = 0
    status: str = "indexed"

class ChunkMetadata(BaseModel):
    chunk_id: str
    doc_id: str
    filename: str
    file_type: Literal["pdf", "txt"]
    page_number: Optional[int] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    text: str
    char_length: int

class EvidenceItem(BaseModel):
    chunk_id: str
    doc_id: str
    filename: str
    file_type: Literal["pdf", "txt"]
    page_number: Optional[int] = None
    line_range: Optional[str] = None
    snippet: str
    similarity_score: float = Field(..., description="Cosine similarity score between query and chunk in [0, 1]")

class ConfidenceIndicator(BaseModel):
    level: Literal["High", "Medium", "Low"]
    score: float = Field(..., description="Calculated aggregate evidence score (0-100)")
    max_similarity: float
    avg_similarity: float
    supporting_documents: List[str]
    pages: List[int]
    evidence_count: int
    disclaimer: str = (
        "Confidence is estimated strictly from semantic retrieval similarity scores and context coverage. "
        "It reflects evidence relevance, not a guaranteed probabilistic truth."
    )

class QueryRequest(BaseModel):
    question: str
    top_k: Optional[int] = 5
    session_id: Optional[str] = None  # UUID for chat session

class QueryResponse(BaseModel):
    question: str
    answer: str
    is_answerable: bool
    api_key_configured: bool = True
    error_message: Optional[str] = None
    sources: List[EvidenceItem]
    confidence_score: float = Field(0.0, description="Confidence value between 0 and 1 derived from retrieval similarity scores.")
    # Optional conversation snapshot (not exposed to client but useful internally)
    conversation_history: Optional[List[dict]] = None

# Model for document summarization request
class SummarizeRequest(BaseModel):
    doc_id: str
    session_id: Optional[str] = None

# Model for summarization response
class SummarizeResponse(BaseModel):
    doc_id: str
    summary: str
