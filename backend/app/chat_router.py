# backend/app/chat_router.py

from fastapi import APIRouter, HTTPException
from .chat import get_history

router = APIRouter()

@router.get('/history/{session_id}', tags=['Chat History'])
def get_chat_history(session_id: str):
    """Return stored Q&A history for a session."""
    return get_history(session_id)
