import React from 'react';
import { FileText, Trash2, Layers, Calendar, HardDrive } from 'lucide-react';

function formatBytes(bytes, decimals = 1) {
  if (!+bytes) return '0 B';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
}

export default function DocumentList({ documents, onDelete, onSummarize, isDeleting }) {
  if (!documents || documents.length === 0) {
    return (
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm text-center">
        <div className="w-10 h-10 mx-auto rounded-xl bg-slate-100 flex items-center justify-center text-slate-400 mb-2">
          <FileText className="w-5 h-5" />
        </div>
        <p className="text-xs font-semibold text-slate-700">No documents indexed yet</p>
        <p className="text-[11px] text-slate-400 mt-0.5">
          Upload PDF or TXT files above to begin asking questions.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-bold text-slate-800 flex items-center gap-2">
          <Layers className="w-4 h-4 text-brand-600" />
          Indexed Documents ({documents.length})
        </h2>
        <span className="text-[11px] text-slate-400 font-medium">Stored locally + FAISS</span>
      </div>

      <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
        {documents.map((doc) => {
          const isPdf = doc.file_type === 'pdf';
          return (
            <div
              key={doc.id}
              className="p-3 rounded-xl border border-slate-200 hover:border-slate-300 bg-slate-50/50 hover:bg-slate-50 flex items-center justify-between gap-3 transition-colors text-xs"
            >
              <div className="flex items-center gap-3 min-w-0">
                <div className={`p-2 rounded-lg ${isPdf ? 'bg-rose-100 text-rose-600' : 'bg-emerald-100 text-emerald-600'} shrink-0`}>
                  <FileText className="w-4 h-4" />
                </div>
                <div className="min-w-0">
                  <div className="font-semibold text-slate-800 truncate" title={doc.filename}>
                    {doc.filename}
                  </div>
                  <div className="flex items-center gap-2 text-[11px] text-slate-400 mt-0.5 flex-wrap">
                    <span className="uppercase font-bold text-[10px] text-slate-500 bg-slate-200/70 px-1.5 py-0.2 rounded">
                      {doc.file_type}
                    </span>
                    <span>{formatBytes(doc.file_size)}</span>
                    {doc.page_count && (
                      <span>• {doc.page_count} {doc.page_count === 1 ? 'page' : 'pages'}</span>
                    )}
                    <span>• {doc.chunk_count} chunks</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-1.5 shrink-0">
                <button
                  type="button"
                  onClick={() => onSummarize && onSummarize(doc)}
                  className="flex items-center gap-1 text-[11px] font-semibold text-brand-600 hover:text-brand-700 bg-brand-50 hover:bg-brand-100 px-2.5 py-1 rounded-lg transition-colors"
                  title="Summarize document"
                >
                  <FileText className="w-3 h-3" />
                  <span>Summarize</span>
                </button>
                <button
                  type="button"
                  onClick={() => onDelete(doc.id)}
                  disabled={isDeleting}
                  className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                  title="Delete document and remove from FAISS index"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
