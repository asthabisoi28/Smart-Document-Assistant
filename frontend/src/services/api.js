// Centralized API base URL configuration.
// In production: reads VITE_API_URL env var (e.g. "https://backend.up.railway.app")
// In development: falls back to relative "/api" which Vite's dev proxy forwards to localhost:8000
const VITE_API_URL = import.meta.env.VITE_API_URL;

if (!VITE_API_URL && import.meta.env.PROD) {
  console.error(
    '[Smart Document Assistant] VITE_API_URL is not set in production! ' +
    'API calls will fail. Set VITE_API_URL in your Vercel environment variables ' +
    'to your Railway backend URL (e.g. https://your-backend.up.railway.app).'
  );
}

const API_BASE = VITE_API_URL ? `${VITE_API_URL.replace(/\/+$/, '')}/api` : '/api';

export async function checkHealth() {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error('Health check failed');
  return res.json();
}

export async function fetchDocuments() {
  const res = await fetch(`${API_BASE}/documents`);
  if (!res.ok) throw new Error('Failed to fetch documents');
  return res.json();
}

export async function uploadDocuments(files) {
  const formData = new FormData();
  for (let i = 0; i < files.length; i++) {
    formData.append('files', files[i]);
  }

  const res = await fetch(`${API_BASE}/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || 'Upload failed');
  }

  return res.json();
}

export async function deleteDocument(docId) {
  const res = await fetch(`${API_BASE}/documents/${docId}`, {
    method: 'DELETE',
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || 'Delete failed');
  }
  return res.json();
}

export async function askQuestion(question, topK = 5, sessionId = null) {
  const res = await fetch(`${API_BASE}/query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ question, top_k: topK, session_id: sessionId }),
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || 'Query failed');
  }

  return res.json();
}

export async function summarizeDocument(docId, sessionId = null) {
  const res = await fetch(`${API_BASE}/summarize`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ doc_id: docId, session_id: sessionId }),
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || 'Summarization failed');
  }

  return res.json();
}

