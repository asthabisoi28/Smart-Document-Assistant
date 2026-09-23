import os
import re
import logging
from typing import List, Tuple, Optional
import numpy as np

from app.models import (
    QueryResponse,
    EvidenceItem,
    ChunkMetadata,
    SummarizeResponse,
)
from app.config import (
    get_gemini_api_key,
    GEMINI_MODEL_NAME,
    TOP_K,
    CONFIDENCE_HIGH_THRESHOLD,
    CONFIDENCE_MEDIUM_THRESHOLD,
    UNANSWERABLE_THRESHOLD
)
from app.embeddings import EmbeddingService
from app.vector_store import VectorStore

logger = logging.getLogger(__name__)

# In-memory conversation history dictionary keyed by session_id
CHAT_HISTORY: dict = {}

def classify_gemini_error(e: Exception) -> Tuple[str, str]:
    """
    Categorizes Gemini exceptions safely without exposing API keys or secrets.
    Returns (category, sanitized_message)
    """
    err_raw = str(e)
    # Sanitize to never leak keys matching common API key patterns
    sanitized = re.sub(r'(?:AIza|AQ\.)[A-Za-z0-9_-]{20,}', '[REDACTED_KEY]', err_raw)
    err_lower = sanitized.lower()

    if "api_key_invalid" in err_lower or "invalid api key" in err_lower or "api key not valid" in err_lower or "401" in err_lower or ("403" in err_lower and "key" in err_lower):
        category = "invalid API key"
    elif "resource_exhausted" in err_lower or "429" in err_lower or "quota" in err_lower:
        category = "quota/rate limit"
    elif "503" in err_lower or "high demand" in err_lower or ("service" in err_lower and "unavailable" in err_lower) or "unavailable" in err_lower:
        category = "service unavailable"
    elif "not_found" in err_lower or "404" in err_lower or "no longer available" in err_lower or "not supported for generatecontent" in err_lower or ("model" in err_lower and "not found" in err_lower):
        category = "model not available"
    elif "invalid_argument" in err_lower or ("request" in err_lower and "format" in err_lower) or "contents" in err_lower:
        category = "request/content format error"
    elif "sdk" in err_lower or "import" in err_lower or "attributeerror" in err_lower:
        category = "incorrect Gemini SDK usage"
    else:
        category = "Gemini API error"

    return category, sanitized

class RAGService:
    def __init__(self, vector_store: VectorStore, embedding_service: EmbeddingService):
        self.vector_store = vector_store
        self.embedding_service = embedding_service



    def _call_gemini_llm(self, question: str, context_text: str, api_key: str, history: Optional[List[dict]] = None) -> Tuple[str, bool, Optional[str]]:
        """
        Invokes Gemini with strict factual grounding instructions.
        Uses the configured model (default: gemini-3.5-flash) via google.genai SDK.
        Returns: (answer_text, is_answerable, error_message)
        """
        system_instruction = (
            "You are a helpful, factual Smart Document Assistant.\n"
            "Your task is to answer the user's question using ONLY the provided document excerpts.\n\n"
            "STRICT RULES:\n"
            "1. Synthesize the provided document excerpts into a natural, coherent, and context-aware answer.\n"
            "2. DO NOT simply repeat or dump raw chunks. Explain the answer smoothly in your own words based strictly on the context.\n"
            "3. If the answer spans multiple documents or pages, synthesize information across them and cite each source (e.g. [filename.pdf, Page 2]).\n"
            "4. If the provided excerpts do NOT contain enough information to answer the question, DO NOT invent or speculate. Clearly state:\n"
            f"   \"I couldn't find information about '{question}' in the uploaded documents.\"\n"
            "5. Do NOT use outside knowledge or extrapolate beyond what is explicitly stated in the excerpts."
        )

        history_text = ""
        if history:
            history_lines = []
            for item in history[-5:]:
                q_val = item.get("question", "")
                a_val = item.get("answer", "")
                if q_val and a_val:
                    history_lines.append(f"User: {q_val}\nAssistant: {a_val}")
            if history_lines:
                history_text = "PREVIOUS CONVERSATION HISTORY:\n" + "\n---\n".join(history_lines) + "\n\n"

        prompt = f"""{history_text}RETRIEVED DOCUMENT EXCERPTS:
{context_text}

USER QUESTION:
{question}

Please provide a well-structured, natural answer based ONLY on the excerpts above:"""

        # Use only the configured active Gemini model (default: gemini-3.5-flash)
        model_name = GEMINI_MODEL_NAME

        logger.info("Querying Gemini API using model: %s", model_name)

        unsupported_indicators = [
            "couldn't find information",
            "could not find information",
            "not found in the uploaded documents",
            "does not contain information",
            "do not contain information",
            "cannot answer this question based on"
        ]

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)
            # Log the size of the context+prompt for diagnostics (character count)
            logger.debug("Prompt length (characters): %d", len(prompt))
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.1,
                    max_output_tokens=512,
                )
            )
            # Primary check: direct text field
            if response and getattr(response, "text", None):
                answer_text = response.text.strip()
                is_ans = not any(ind in answer_text.lower() for ind in unsupported_indicators)
                return answer_text, is_ans, None

            # Fallback: inspect candidates for generated parts
            if response and getattr(response, "candidates", None):
                try:
                    candidate = response.candidates[0]
                    # Collect text from all parts if available
                    parts_texts = []
                    for part in getattr(candidate.content, "parts", []):
                        if hasattr(part, "text"):
                            parts_texts.append(part.text)
                    answer_text = " ".join(parts_texts).strip()
                    if answer_text:
                        is_ans = not any(ind in answer_text.lower() for ind in unsupported_indicators)
                        # Log finish reason for diagnostics (won't expose secrets)
                        finish_reason = getattr(candidate, "finish_reason", "unknown")
                        logger.debug("Gemini candidate finish_reason: %s", finish_reason)
                        return answer_text, is_ans, None
                except Exception as e_fallback:
                    logger.debug("Error extracting text from Gemini candidates: %s", e_fallback)

            # If no text could be extracted, return a clear error message
            return "", False, "Gemini returned no generated text. Please check the prompt or try a different query."
        except Exception as e:
            category, safe_msg = classify_gemini_error(e)
            # Full details stay in backend logs only
            logger.warning(f"google.genai call to {model_name} failed [{category}]: {safe_msg}")

            # Return clean, user-facing messages — never expose raw API internals
            user_messages = {
                "quota/rate limit": (
                    "Gemini is temporarily unavailable because the API quota has been exceeded. "
                    "Please try again later."
                ),
                "invalid API key": (
                    "The configured Gemini API key is invalid. "
                    "Please check the GEMINI_API_KEY in backend/.env."
                ),
                "service unavailable": (
                    "Gemini is temporarily unavailable due to high demand. "
                    "Please try again shortly."
                ),
                "model not available": (
                    "The configured Gemini model is currently unavailable. "
                    "Please contact the administrator."
                ),
                "request/content format error": (
                    "There was an issue processing your request. "
                    "Please try rephrasing your question."
                ),
                "incorrect Gemini SDK usage": (
                    "An internal configuration error occurred. "
                    "Please contact the administrator."
                ),
            }
            user_msg = user_messages.get(
                category,
                "Unable to generate a response from Gemini. Please try again later."
            )
            return "", False, user_msg

    def answer_question(self, question: str, top_k: int = TOP_K, session_id: Optional[str] = None) -> QueryResponse:
        """
        End-to-end RAG pipeline:
        User Question
        -> Retrieve relevant chunks from FAISS
        -> Check whether sufficient relevant context exists
        -> Check API key configuration
        -> Include conversation history if session_id provided
        -> Send question + context to Gemini for natural synthesis
        -> Return answer FIRST, then sources/evidence
        """
        question_clean = question.strip()
        current_history = CHAT_HISTORY.get(session_id, []) if session_id else None

        if not question_clean:
            return QueryResponse(
                question=question,
                answer="Please enter a question to search your documents.",
                is_answerable=False,
                api_key_configured=True,
                error_message=None,
                sources=[],
                conversation_history=current_history
            )

        if len(self.vector_store.chunks) == 0:
            return QueryResponse(
                question=question_clean,
                answer="No documents have been uploaded yet. Please upload PDF or TXT documents to ask questions.",
                is_answerable=False,
                api_key_configured=True,
                error_message=None,
                sources=[],
                conversation_history=current_history
            )

        # 1. Embed query
        query_vec = self.embedding_service.embed_query(question_clean)

        # 2. Retrieve top-k chunks from FAISS
        retrieved_items = self.vector_store.search(query_vec, top_k=top_k)

        max_similarity = max([score for _, score in retrieved_items]) if retrieved_items else 0.0

        # Format sources list
        sources: List[EvidenceItem] = []
        context_parts = []

        # Build context but cap total characters to avoid exceeding model token budget
        MAX_CONTEXT_CHARS = 2000
        current_len = 0

        for idx, (chunk, score) in enumerate(retrieved_items):
            line_range_str = f"Lines {chunk.line_start}-{chunk.line_end}" if chunk.line_start else None
            loc_label = f"Page {chunk.page_number}" if chunk.page_number else (line_range_str or "Document Content")

            chunk_text = f"[Source {idx + 1}: {chunk.filename} | Location: {loc_label} | Cosine Similarity: {score:.2f}]\n{chunk.text}\n"
            if current_len + len(chunk_text) > MAX_CONTEXT_CHARS:
                break
            context_parts.append(chunk_text)
            current_len += len(chunk_text)

            sources.append(EvidenceItem(
                chunk_id=chunk.chunk_id,
                doc_id=chunk.doc_id,
                filename=chunk.filename,
                file_type=chunk.file_type,
                page_number=chunk.page_number,
                line_range=line_range_str,
                snippet=chunk.text,
                similarity_score=round(score, 3)
            ))

        # 3. Check whether sufficient relevant context exists (Anti-Hallucination Guardrail)
        if max_similarity < UNANSWERABLE_THRESHOLD:
            unsupported_msg = f"I couldn't find information about '{question_clean}' in the uploaded documents."
            return QueryResponse(
                question=question_clean,
                answer=unsupported_msg,
                is_answerable=False,
                api_key_configured=True,
                error_message=None,
                sources=sources,
                conversation_history=current_history
            )

        # 4. Check Gemini API key configuration
        api_key = get_gemini_api_key()
        if not api_key:
            return QueryResponse(
                question=question_clean,
                answer="",
                is_answerable=False,
                api_key_configured=False,
                error_message=(
                    "Gemini API key is not configured. Please add GEMINI_API_KEY to backend/.env "
                    "to generate the context-aware answer with Gemini 3.5 Flash."
                ),
                sources=sources,
                conversation_history=current_history
            )

        # 5. Send question + context to Gemini for natural synthesis (with history)
        context_text = "\n---\n".join(context_parts)
        history_list = CHAT_HISTORY.get(session_id, []) if session_id else None
        answer_text, is_answerable, error_message = self._call_gemini_llm(
            question_clean, context_text, api_key, history=history_list
        )

        # Save conversation turn
        if session_id and answer_text and is_answerable:
            if session_id not in CHAT_HISTORY:
                CHAT_HISTORY[session_id] = []
            CHAT_HISTORY[session_id].append({"question": question_clean, "answer": answer_text})

        return QueryResponse(
            question=question_clean,
            answer=answer_text,
            is_answerable=is_answerable,
            api_key_configured=True,
            error_message=error_message,
            sources=sources,
            conversation_history=CHAT_HISTORY.get(session_id, []) if session_id else None
        )

    def summarize_document(self, doc_id: str, session_id: Optional[str] = None) -> SummarizeResponse:
        """
        Generates a concise summary grounded strictly in the requested document.
        """
        chunks = self.vector_store.get_chunks_by_doc_id(doc_id)
        if not chunks:
            return SummarizeResponse(
                doc_id=doc_id,
                summary="No document content found to summarize."
            )

        api_key = get_gemini_api_key()
        if not api_key:
            return SummarizeResponse(
                doc_id=doc_id,
                summary="Gemini API key is not configured. Unable to generate document summary."
            )

        context_parts = []
        curr_len = 0
        for chunk in chunks:
            if curr_len + len(chunk.text) > 5000:
                break
            context_parts.append(chunk.text)
            curr_len += len(chunk.text)

        doc_text = "\n\n".join(context_parts)

        prompt = f"""DOCUMENT CONTENT:
{doc_text}

USER REQUEST:
Please provide a concise, clear, and well-structured summary of the document above. Ground your summary ONLY on the provided text. Do not invent or extrapolate."""

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=GEMINI_MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction="You are a helpful document assistant that generates concise document summaries.",
                    temperature=0.2,
                    max_output_tokens=512,
                )
            )

            summary_text = ""
            if response and getattr(response, "text", None):
                summary_text = response.text.strip()
            elif response and getattr(response, "candidates", None):
                candidate = response.candidates[0]
                parts_texts = [p.text for p in getattr(candidate.content, "parts", []) if hasattr(p, "text")]
                summary_text = " ".join(parts_texts).strip()

            if not summary_text:
                summary_text = "Unable to generate summary for this document."

            return SummarizeResponse(doc_id=doc_id, summary=summary_text)
        except Exception as e:
            category, safe_msg = classify_gemini_error(e)
            logger.warning(f"Summarization error [{category}]: {safe_msg}")
            return SummarizeResponse(
                doc_id=doc_id,
                summary=f"Error generating summary: {safe_msg}"
            )

