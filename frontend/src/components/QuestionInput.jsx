import React, { useState } from 'react';
import { Search, ArrowRight, CornerDownLeft, Sparkles, X } from 'lucide-react';

export default function QuestionInput({ onAsk, isLoading, hasDocuments }) {
  const [question, setQuestion] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!question.trim() || isLoading || !hasDocuments) return;
    onAsk(question.trim());
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm space-y-3">
      <form onSubmit={handleSubmit} className="relative">
        <div className="relative flex items-center">
          <div className="absolute left-3.5 text-slate-400 pointer-events-none">
            <Search className="w-5 h-5" />
          </div>

          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={!hasDocuments || isLoading}
            placeholder={
              hasDocuments
                ? "Ask anything about the uploaded documents (e.g. 'What are the main findings?')"
                : "Upload at least one document first to ask questions..."
            }
            className="w-full pl-11 pr-24 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 focus:bg-white transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          />

          {question && !isLoading && (
            <button
              type="button"
              onClick={() => setQuestion('')}
              className="absolute right-14 p-1 text-slate-400 hover:text-slate-600 focus:outline-none"
            >
              <X className="w-4 h-4" />
            </button>
          )}

          <button
            type="submit"
            disabled={!question.trim() || !hasDocuments || isLoading}
            className="absolute right-2 px-3 py-2 bg-gradient-to-r from-brand-600 to-indigo-600 hover:from-brand-700 hover:to-indigo-700 text-white rounded-lg text-xs font-semibold flex items-center gap-1 shadow-sm disabled:opacity-40 disabled:cursor-not-allowed transition-all"
          >
            {isLoading ? (
              <span className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <>
                <span>Ask</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </>
            )}
          </button>
        </div>
      </form>

      <div className="flex items-center justify-between text-[11px] text-slate-400 px-1">
        <div className="flex items-center gap-1.5">
          <CornerDownLeft className="w-3.5 h-3.5" />
          <span>Press <kbd className="px-1.5 py-0.5 bg-slate-100 border border-slate-200 rounded text-[10px] font-mono text-slate-600">Enter</kbd> to submit query</span>
        </div>
        <span>Grounded search using FAISS top-k embeddings</span>
      </div>
    </div>
  );
}
