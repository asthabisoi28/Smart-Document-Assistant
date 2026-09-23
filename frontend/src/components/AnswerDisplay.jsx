import React, { useState } from 'react';
import { Copy, Check, Sparkles, AlertCircle, Info, KeyRound, CheckCircle2 } from 'lucide-react';

import EvidenceCard from './EvidenceCard';

export default function AnswerDisplay({ queryResult, isLoading }) {
  const [copied, setCopied] = useState(false);

  if (isLoading) {
    return (
      <div className="bg-white border border-slate-200 rounded-2xl p-8 shadow-sm text-center space-y-4 animate-pulse">
        <div className="w-12 h-12 mx-auto rounded-full bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600">
          <Sparkles className="w-6 h-6 animate-spin" />
        </div>
        <div>
          <h3 className="text-base font-semibold text-slate-800">Generating Grounded Answer...</h3>
          <p className="text-xs text-slate-500 mt-1">
            Retrieving nearest embeddings from FAISS & querying Gemini 3.5 Flash
          </p>
        </div>
      </div>
    );
  }

  if (!queryResult) {
    return null;
  }

  const {
    question,
    answer,
    is_answerable,
    api_key_configured = true,
    error_message,
    sources
  } = queryResult;

  const handleCopy = () => {
    if (!answer) return;
    navigator.clipboard.writeText(answer);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-7">
      {/* Query Title & Action Bar */}
      <div className="flex items-start justify-between gap-4 pb-4 border-b border-slate-100">
        <div className="space-y-1">
          <div className="text-[11px] font-bold text-indigo-600 uppercase tracking-wider flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5" />
            Document Question
          </div>
          <h2 className="text-base font-bold text-slate-900 leading-snug">
            "{question}"
          </h2>
        </div>

        {answer && (
          <button
            type="button"
            onClick={handleCopy}
            className="flex items-center gap-1.5 text-xs text-slate-600 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 px-3 py-1.5 rounded-lg font-medium transition-colors shrink-0"
            title="Copy answer"
          >
            {copied ? (
              <>
                <Check className="w-3.5 h-3.5 text-emerald-600" />
                <span>Copied</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5" />
                <span>Copy</span>
              </>
            )}
          </button>
        )}
      </div>

      {/* =========================================
          SECTION 1: ANSWER (Displayed FIRST)
         ========================================= */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4 text-brand-600" />
            Answer
          </h3>
          {is_answerable && answer && (
            <span className="text-[10px] font-medium text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full">
              Synthesized by Gemini 3.5 Flash
            </span>
          )}
        </div>

        {/* Case A: API Key is missing */}
        {!api_key_configured ? (
          <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-xs space-y-2">
            <div className="flex items-center gap-2 font-bold text-amber-950 text-sm">
              <KeyRound className="w-4 h-4 text-amber-600 shrink-0" />
              Gemini API Key Required
            </div>
            <p className="leading-relaxed text-amber-800">
              Relevant document chunks were successfully retrieved from FAISS, but <code className="bg-amber-100/80 px-1 py-0.5 rounded text-amber-900 font-mono">GEMINI_API_KEY</code> is not configured in <code className="bg-amber-100/80 px-1 py-0.5 rounded text-amber-900 font-mono">backend/.env</code>.
            </p>
            <p className="text-[11px] text-amber-700">
              Please open <code className="font-mono">backend/.env</code> and enter your key:
              <br />
              <span className="font-mono bg-white/80 border border-amber-200 px-2 py-1 rounded inline-block mt-1 text-slate-800 font-semibold">
                GEMINI_API_KEY=AIzaSy...
              </span>
            </p>
            <p className="text-[11px] text-amber-600 italic">
              Once added, ask your question again. You can inspect the retrieved passages below in Sources & Evidence.
            </p>
          </div>
        ) : error_message ? (
          /* Case B: API execution error — shown with clean user-facing message */
          <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start gap-2.5">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
            <div>
              <div className="font-semibold text-rose-900">Unable to Generate Answer</div>
              <p className="mt-0.5 text-rose-700">{error_message}</p>
            </div>
          </div>
        ) : !is_answerable ? (
          /* Case C: Information not present (Unsupported query / Anti-hallucination) */
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-slate-800 text-xs space-y-1.5">
            <div className="flex items-center gap-2 font-semibold text-slate-900">
              <Info className="w-4 h-4 text-slate-500 shrink-0" />
              Information Not Found in Uploaded Documents
            </div>
            <p className="text-slate-700 leading-relaxed text-sm">
              {answer || `I couldn't find information about "${question}" in the uploaded documents.`}
            </p>
            <p className="text-[11px] text-slate-400 italic">
              The assistant will not use outside knowledge or speculate when information is absent.
            </p>
          </div>
        ) : (
          /* Case D: Successful grounded context-aware answer */
          <div className="p-4 rounded-xl bg-slate-50/70 border border-slate-200/80">
            <div className="prose prose-slate max-w-none text-sm leading-relaxed text-slate-800 whitespace-pre-wrap">
              {answer}
            </div>
          </div>
        )}
      </div>

      {/* =========================================
          SECTION 2: SOURCES & EVIDENCE (Displayed AFTER Answer)
         ========================================= */}
      <div className="pt-4 border-t border-slate-200 space-y-4">


        {/* Source Citations & Snippets */}
        <EvidenceCard sources={sources} />
      </div>
    </div>
  );
}
