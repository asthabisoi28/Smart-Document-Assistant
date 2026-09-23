from typing import List, Dict

# In‑memory session chat history
# session_id -> list of entries {question, answer, is_answerable}
SESSION_HISTORY: Dict[str, List[Dict[str, object]]] = {}

def add_to_history(session_id: str, entry: Dict[str, object]) -> None:
    """Append a Q&A entry to a session's history.
    If the session does not exist it is created.
    """
    if not session_id:
        return
    SESSION_HISTORY.setdefault(session_id, []).append(entry)

def get_history(session_id: str) -> List[Dict[str, object]]:
    """Return the list of Q&A history for the given session.
    Returns empty list if none.
    """
    return SESSION_HISTORY.get(session_id, [])
