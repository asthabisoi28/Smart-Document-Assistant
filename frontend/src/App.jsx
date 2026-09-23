import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import DocumentUpload from './components/DocumentUpload';
import DocumentList from './components/DocumentList';
import QuestionInput from './components/QuestionInput';
import AnswerDisplay from './components/AnswerDisplay';
import ChatHistory from './components/ChatHistory';
import SummaryModal from './components/SummaryModal';
import { fetchDocuments, deleteDocument, askQuestion, summarizeDocument, checkHealth } from './services/api';
import { FileSearch } from 'lucide-react';

export default function App() {
  const [documents, setDocuments] = useState([]);
  const [health, setHealth] = useState(null);
  const [isOnline, setIsOnline] = useState(false);
  const [isQuerying, setIsQuerying] = useState(false);
  const [queryResult, setQueryResult] = useState(null);
  const [queryError, setQueryError] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Conversation session state
  const [sessionId, setSessionId] = useState('');
  const [chatHistory, setChatHistory] = useState([]);

  // Document summarization modal state
  const [summaryDoc, setSummaryDoc] = useState(null);
  const [summaryContent, setSummaryContent] = useState('');
  const [isSummarizing, setIsSummarizing] = useState(false);
  const [summaryError, setSummaryError] = useState(null);

  useEffect(() => {
    // Generate or retrieve persistent client session ID
    let sid = localStorage.getItem('sda_session_id');
    if (!sid) {
      sid = typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : `session-${Date.now()}`;
      localStorage.setItem('sda_session_id', sid);
    }
    setSessionId(sid);
  }, []);

  const loadData = async () => {
    try {
      const [h, docs] = await Promise.all([
        checkHealth().catch(() => null),
        fetchDocuments().catch(() => [])
      ]);
      setHealth(h);
      setIsOnline(!!h);
      setDocuments(docs || []);
    } catch {
      setIsOnline(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleUploadComplete = () => {
    loadData();
  };

  const handleDelete = async (docId) => {
    if (!confirm('Are you sure you want to delete this document from the vector index?')) return;
    setIsDeleting(true);
    try {
      await deleteDocument(docId);
      await loadData();
      if (queryResult) {
        setQueryResult(null);
      }
    } catch (err) {
      alert(err.message || 'Failed to delete document');
    } finally {
      setIsDeleting(false);
    }
  };

  const handleAsk = async (question) => {
    setIsQuerying(true);
    setQueryError(null);
    try {
      const res = await askQuestion(question, 5, sessionId);
      setQueryResult(res);
      if (res.conversation_history) {
        setChatHistory(res.conversation_history);
      }
    } catch (err) {
      setQueryError(err.message || 'Failed to process query');
    } finally {
      setIsQuerying(false);
    }
  };

  const handleSummarize = async (doc) => {
    setSummaryDoc(doc);
    setSummaryContent('');
    setSummaryError(null);
    setIsSummarizing(true);
    try {
      const res = await summarizeDocument(doc.id, sessionId);
      setSummaryContent(res.summary);
    } catch (err) {
      setSummaryError(err.message || 'Failed to summarize document');
    } finally {
      setIsSummarizing(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900">
      <Header health={health} isOnline={isOnline} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          
          {/* Left Column: Documents & Ingestion (5 cols on lg) */}
          <div className="lg:col-span-5 space-y-6">
            <DocumentUpload onUploadComplete={handleUploadComplete} />
            <DocumentList
              documents={documents}
              onDelete={handleDelete}
              onSummarize={handleSummarize}
              isDeleting={isDeleting}
            />
            <ChatHistory history={chatHistory} />
          </div>

          {/* Right Column: Q&A, Grounded Answers & Citations (7 cols on lg) */}
          <div className="lg:col-span-7 space-y-6">
            <QuestionInput
              onAsk={handleAsk}
              isLoading={isQuerying}
              hasDocuments={documents.length > 0}
            />

            {queryError && (
              <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs">
                {queryError}
              </div>
            )}

            {/* Answer Display */}
            {queryResult || isQuerying ? (
              <AnswerDisplay
                queryResult={queryResult}
                isLoading={isQuerying}
              />
            ) : (
              /* Empty state placeholder */
              <div className="bg-white border border-slate-200 rounded-2xl p-10 shadow-sm text-center space-y-3">
                <div className="w-12 h-12 mx-auto rounded-2xl bg-brand-50 flex items-center justify-center text-brand-600">
                  <FileSearch className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-800">
                    {documents.length > 0 ? "Ready to Answer Questions" : "Upload Documents to Begin"}
                  </h3>
                  <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
                    {documents.length > 0
                      ? "Ask any question above. The assistant will retrieve exact passages, synthesize grounded answers, and cite source documents."
                      : "Add your PDF or TXT files on the left panel to build the vector knowledge base."}
                  </p>
                </div>
              </div>
            )}
          </div>

        </div>
      </main>

      {/* Summarization Modal */}
      {summaryDoc && (
        <SummaryModal
          doc={summaryDoc}
          summary={summaryContent}
          isLoading={isSummarizing}
          error={summaryError}
          onClose={() => setSummaryDoc(null)}
        />
      )}

      <footer className="border-t border-slate-200 bg-white py-4 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-slate-500">
          <div>
            Smart Document Assistant &bull; PyMuPDF &bull; FAISS &bull; {health?.gemini_model ? health.gemini_model.replace(/^gemini-/i, "Gemini ").replace(/-/g, " ").replace(/\b\w/g, c => c.toUpperCase()) : "Gemini 3.5 Flash Lite"}
          </div>
          <div className="text-[11px] text-slate-400">
            Session: {sessionId ? `${sessionId.slice(0, 8)}...` : 'Initializing'}
          </div>
        </div>
      </footer>
    </div>
  );
}
