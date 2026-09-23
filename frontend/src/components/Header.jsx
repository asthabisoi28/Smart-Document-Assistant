import React from 'react';
import { BookOpen, Sparkles, Server, CheckCircle2, AlertCircle, KeyRound } from 'lucide-react';

export default function Header({ health, isOnline }) {
  const isKeyConfigured = health?.gemini_api_key_configured;

  const rawModel = health?.gemini_model || "gemini-3.5-flash-lite";
  const formattedModel = rawModel
    .replace(/^gemini-/i, "Gemini ")
    .replace(/-/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-indigo-600 flex items-center justify-center text-white shadow-md shadow-brand-500/20">
            <BookOpen className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold tracking-tight text-slate-900">
                Smart Document Assistant
              </h1>
              <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200/60 hidden sm:flex items-center gap-1">
                <Sparkles className="w-3 h-3" /> {formattedModel} + FAISS
              </span>
            </div>
            
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          {/* Gemini API Key Status Badge */}
          {isOnline && (
            isKeyConfigured ? (
              <span className="hidden sm:flex items-center gap-1 text-[11px] font-medium text-emerald-700 bg-emerald-50 border border-emerald-200/70 px-2.5 py-1 rounded-lg">
                <Sparkles className="w-3 h-3 text-emerald-500" />
                Gemini LLM Ready
              </span>
            ) : (
              <span className="flex items-center gap-1 text-[11px] font-medium text-amber-800 bg-amber-50 border border-amber-200/80 px-2.5 py-1 rounded-lg" title="Add GEMINI_API_KEY to backend/.env">
                <KeyRound className="w-3 h-3 text-amber-500" />
                API Key Needed in .env
              </span>
            )
          )}

          {/* Backend Status */}
          <div className="flex items-center gap-2 text-xs text-slate-600 bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-lg">
            <Server className="w-3.5 h-3.5 text-slate-400" />
            <span className="font-medium hidden xs:inline">Backend:</span>
            {isOnline ? (
              <span className="flex items-center gap-1 text-emerald-600 font-semibold">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" /> Online
              </span>
            ) : (
              <span className="flex items-center gap-1 text-rose-600 font-semibold">
                <AlertCircle className="w-3.5 h-3.5 text-rose-500" /> Offline
              </span>
            )}
            {health && (
              <span className="hidden md:inline text-slate-400 pl-1 border-l border-slate-200">
                {health.total_chunks} chunks
              </span>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
