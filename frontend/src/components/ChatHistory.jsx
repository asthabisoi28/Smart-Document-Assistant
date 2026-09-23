import React, { useState } from 'react';
import { MessageSquare, Bot, User, ChevronDown, ChevronUp, History } from 'lucide-react';

export default function ChatHistory({ history }) {
  const [isOpen, setIsOpen] = useState(true);

  if (!history || history.length === 0) {
    return (
      <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-2">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
            <History className="w-4 h-4 text-brand-600" />
            Chat History & Context (0)
          </h3>
        </div>
        <p className="text-[11px] text-slate-400 italic">
          No conversation turns in this session yet. Ask a question to build session context.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
          <History className="w-4 h-4 text-brand-600" />
          Chat History & Context ({history.length})
        </h3>
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className="text-slate-400 hover:text-slate-600 text-xs font-medium flex items-center gap-1"
        >
          {isOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
      </div>

      {isOpen && (
        <div className="space-y-3 max-h-60 overflow-y-auto pr-1">
          {history.map((turn, idx) => (
            <div key={idx} className="p-3 rounded-xl bg-slate-50 border border-slate-200/80 space-y-2 text-xs">
              <div className="flex items-start gap-2 font-semibold text-slate-800">
                <User className="w-3.5 h-3.5 text-brand-600 mt-0.5 shrink-0" />
                <span className="leading-snug">{turn.question}</span>
              </div>
              <div className="flex items-start gap-2 text-slate-600 pl-5 pt-1 border-t border-slate-200/60">
                <Bot className="w-3.5 h-3.5 text-indigo-500 mt-0.5 shrink-0" />
                <div className="leading-relaxed line-clamp-3">{turn.answer}</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
