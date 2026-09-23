import React, { useState } from 'react';
import { X, Sparkles, Copy, Check, FileText, Loader2 } from 'lucide-react';

export default function SummaryModal({ doc, summary, isLoading, error, onClose }) {
  const [copied, setCopied] = useState(false);

  if (!doc) return null;

  const handleCopy = () => {
    if (!summary) return;
    navigator.clipboard.writeText(summary);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white border border-slate-200 rounded-2xl max-w-xl w-full p-6 shadow-xl space-y-5 animate-in fade-in zoom-in-95 duration-200">
        
        {/* Header */}
        <div className="flex items-start justify-between gap-4 border-b border-slate-100 pb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-brand-50 flex items-center justify-center text-brand-600 shrink-0">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <div className="text-[10px] font-bold text-brand-600 uppercase tracking-wider">
                Automatic Document Summary
              </div>
              <h3 className="text-sm font-bold text-slate-800 truncate max-w-xs sm:max-w-md" title={doc.filename}>
                {doc.filename}
              </h3>
            </div>
          </div>
          
          <button
            type="button"
            onClick={onClose}
            className="p-1 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="space-y-4 max-h-96 overflow-y-auto pr-1">
          {isLoading ? (
            <div className="py-12 text-center space-y-3">
              <Loader2 className="w-8 h-8 mx-auto text-brand-600 animate-spin" />
              <p className="text-xs font-semibold text-slate-700">Generating Grounded Summary...</p>
              <p className="text-[11px] text-slate-400 max-w-xs mx-auto">
                Reading document chunks & requesting summary from Gemini 3.5 Flash-Lite
              </p>
            </div>
          ) : error ? (
            <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs">
              <div className="font-semibold text-rose-900">Summary Failed</div>
              <p className="mt-1 text-rose-700">{error}</p>
            </div>
          ) : (
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 text-xs leading-relaxed text-slate-800 whitespace-pre-wrap font-sans">
              {summary}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between pt-3 border-t border-slate-100">
          <div className="text-[11px] text-slate-400 italic">
            Grounded strictly in uploaded document contents.
          </div>

          <div className="flex items-center gap-2">
            {summary && !isLoading && (
              <button
                type="button"
                onClick={handleCopy}
                className="flex items-center gap-1.5 text-xs text-slate-600 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 px-3 py-1.5 rounded-lg font-medium transition-colors"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copied ? 'Copied' : 'Copy'}</span>
              </button>
            )}
            <button
              type="button"
              onClick={onClose}
              className="text-xs font-medium text-slate-700 bg-slate-200/70 hover:bg-slate-200 px-4 py-1.5 rounded-lg transition-colors"
            >
              Close
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}
