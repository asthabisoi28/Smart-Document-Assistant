import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storage"
UPLOADS_DIR = STORAGE_DIR / "uploads"
INDEX_PATH = STORAGE_DIR / "faiss_index.bin"
CHUNKS_PATH = STORAGE_DIR / "chunks.json"
DOCS_PATH = STORAGE_DIR / "documents.json"
ENV_PATH = BASE_DIR / ".env"

# Ensure required storage directories exist
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

def reload_env():
    """Dynamically reloads backend/.env so edits take effect immediately without restarting."""
    if ENV_PATH.exists():
        load_dotenv(ENV_PATH, override=True)

# Initial environment load
reload_env()

def get_gemini_api_key() -> str:
    """
    Returns the configured Gemini API key from environment or .env file.
    Filters out empty values and placeholder templates.
    """
    reload_env()
    raw_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""
    key = raw_key.strip()
    
    # Placeholder detection removed; any provided key is used directly
    
    return key

# Settings
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

# RAG & Retrieval Config
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "600"))  # characters
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "120"))  # characters
TOP_K = int(os.getenv("TOP_K", "5"))

# Confidence Thresholds (Cosine similarity in [-1, 1])
CONFIDENCE_HIGH_THRESHOLD = float(os.getenv("CONFIDENCE_HIGH_THRESHOLD", "0.60"))
CONFIDENCE_MEDIUM_THRESHOLD = float(os.getenv("CONFIDENCE_MEDIUM_THRESHOLD", "0.42"))
UNANSWERABLE_THRESHOLD = float(os.getenv("UNANSWERABLE_THRESHOLD", "0.28"))
