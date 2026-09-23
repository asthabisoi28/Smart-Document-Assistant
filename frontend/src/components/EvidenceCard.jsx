import React, { useState } from 'react';
import { FileText, ChevronDown, ChevronUp, Bookmark, ExternalLink } from 'lucide-react';

export default function EvidenceCard({ sources }) {
  const [expandedIndex, setExpandedIndex] = useState(0);

  if (!sources || sources.length === 0) {
    return (
      <div className="text-center py-6 text-slate-400 text-xs italic bg-slate-50 border border-slate-200/60 rounded-xl">
        No specific supporting evidence snippets retrieved.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
          <Bookmark className="w-3.5 h-3.5 text-brand-600" />
          Retrieved Sources ({sources.length})
        </h3>
        <span className="text-[11px] text-slate-400">Cited Document Excerpts</span>
      </div>

      <div className="space-y-2">
        {sources.map((item, idx) => {
          const isExpanded = expandedIndex === idx;
          const isPdf = item.file_type === 'pdf';
          const locationLabel = isPdf && item.page_number
            ? `Page ${item.page_number}`
            : (item.line_range || 'Document Excerpt');

          return (
            <div
              key={item.chunk_id || idx}
              className={`border rounded-xl transition-all duration-200 bg-white overflow-hidden ${
                isExpanded ? 'border-brand-300 shadow-sm' : 'border-slate-200 hover:border-slate-300'
              }`}
            >
              <button
                type="button"
                onClick={() => setExpandedIndex(isExpanded ? null : idx)}
                className="w-full text-left px-3.5 py-2.5 flex items-center justify-between gap-3 focus:outline-none hover:bg-slate-50/50"
              >
                <div className="flex items-center gap-2.5 min-w-0">
                  <span className="flex items-center justify-center w-5 h-5 rounded bg-slate-100 text-slate-600 font-mono text-[10px] font-bold shrink-0">
                    {idx + 1}
                  </span>
                  <FileText className={`w-4 h-4 shrink-0 ${isPdf ? 'text-rose-500' : 'text-emerald-500'}`} />
                  <span className="text-xs font-semibold text-slate-800 truncate" title={item.filename}>
                    {item.filename}
                  </span>
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200 shrink-0">
                    {locationLabel}
                  </span>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  {isExpanded ? (
                    <ChevronUp className="w-4 h-4 text-slate-400" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-slate-400" />
                  )}
                </div>
              </button>

              {isExpanded && (
                <div className="px-3.5 pb-3 pt-1 border-t border-slate-100 bg-slate-50/50">
                  <div className="p-3 bg-white border border-slate-200 rounded-lg text-xs leading-relaxed text-slate-700 font-mono whitespace-pre-wrap select-text">
                    {item.snippet}
                  </div>
                  <div className="mt-2 flex items-center justify-between text-[10px] text-slate-400">
                    <span>Chunk ID: {item.chunk_id}</span>
                    <span>Format: {item.file_type.toUpperCase()}</span>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
