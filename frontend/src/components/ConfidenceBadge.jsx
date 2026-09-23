import React, { useState } from 'react';
import { ShieldCheck, ShieldAlert, Shield, Info, HelpCircle } from 'lucide-react';

export default function ConfidenceBadge({ confidence }) {
  const [showTooltip, setShowTooltip] = useState(false);

  if (!confidence) return null;

  const { level, score, max_similarity, avg_similarity, supporting_documents, pages, evidence_count, disclaimer } = confidence;

  const config = {
    High: {
      bg: 'bg-emerald-50',
      text: 'text-emerald-800',
      border: 'border-emerald-200',
      badgeBg: 'bg-emerald-600',
      barColor: 'bg-emerald-500',
      icon: ShieldCheck,
      description: 'Strong direct semantic alignment with source passages.'
    },
    Medium: {
      bg: 'bg-amber-50',
      text: 'text-amber-800',
      border: 'border-amber-200',
      badgeBg: 'bg-amber-500',
      barColor: 'bg-amber-500',
      icon: Shield,
      description: 'Moderate semantic alignment with partial source coverage.'
    },
    Low: {
      bg: 'bg-rose-50',
      text: 'text-rose-800',
      border: 'border-rose-200',
      badgeBg: 'bg-rose-500',
      barColor: 'bg-rose-500',
      icon: ShieldAlert,
      description: 'Weak or indirect alignment; verify information carefully.'
    }
  }[level] || {
    bg: 'bg-slate-50',
    text: 'text-slate-800',
    border: 'border-slate-200',
    badgeBg: 'bg-slate-500',
    barColor: 'bg-slate-500',
    icon: Shield,
    description: 'Unknown confidence state.'
  };

  const IconComponent = config.icon;

  return (
    <div className={`rounded-xl border ${config.border} ${config.bg} p-4 text-xs transition-all`}>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-2.5">
        <div className="flex items-center gap-2">
          <div className={`p-1.5 rounded-lg text-white ${config.badgeBg}`}>
            <IconComponent className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-sm text-slate-900 tracking-tight">
                Evidence Level: <span className={config.text}>{level}</span>
              </span>
              <button
                type="button"
                onClick={() => setShowTooltip(!showTooltip)}
                className="text-slate-400 hover:text-slate-600 focus:outline-none"
                title="Evidence explanation"
              >
                <HelpCircle className="w-3.5 h-3.5" />
              </button>
            </div>
            <p className="text-[11px] text-slate-500 mt-0.5">
              {config.description}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-right">
            <div className="font-mono font-bold text-slate-800 text-sm">{score}%</div>
            <div className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Evidence Score</div>
          </div>
          <div className="w-20 bg-slate-200/80 rounded-full h-2 overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${config.barColor}`}
              style={{ width: `${Math.min(100, Math.max(5, score))}%` }}
            />
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-slate-200/60 text-[11px] text-slate-600 font-medium">
        <div>
          <span className="text-slate-400">Peak Similarity:</span>{' '}
          <span className="font-mono font-semibold text-slate-700">{max_similarity}</span>
        </div>
        <div>
          <span className="text-slate-400">Mean Similarity:</span>{' '}
          <span className="font-mono font-semibold text-slate-700">{avg_similarity}</span>
        </div>
        <div>
          <span className="text-slate-400">Supporting Docs:</span>{' '}
          <span className="font-semibold text-slate-700">{supporting_documents?.length || 0}</span>
        </div>
        <div>
          <span className="text-slate-400">Cited Pages:</span>{' '}
          <span className="font-semibold text-slate-700">
            {pages && pages.length > 0 ? `p. ${pages.join(', ')}` : 'N/A (text)'}
          </span>
        </div>
      </div>


    </div>
  );
}
