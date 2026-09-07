import React, { useState } from 'react';
import { Globe, ExternalLink, ChevronDown, ChevronUp, CheckCircle, XCircle, Search } from 'lucide-react';

export default function WebEvidenceCard({ pipelineResult }) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!pipelineResult || !pipelineResult.search) {
    return (
      <div className="glass-panel rounded-2xl p-5 border border-slate-800/80">
        <div className="flex items-center gap-2 mb-3">
          <Globe className="w-5 h-5 text-cyan-400" />
          <h3 className="text-base font-semibold text-white font-['Outfit']">Web Evidence (Google Lens)</h3>
        </div>
        <p className="text-xs text-slate-500 italic">No reverse search evidence available. Analyze an image first.</p>
      </div>
    );
  }

  const searchData = pipelineResult.search || {};
  const matchData = pipelineResult.match || {};
  const candidates = searchData.candidates || [];

  // Determine backend base URL for evidence images
  const apiBase = window.location.origin.includes('5173') ? 'http://localhost:8000' : '';
  const evidenceImgUrl = matchData.evidence_image 
    ? (matchData.evidence_image.startsWith('http') ? matchData.evidence_image : `${apiBase}${matchData.evidence_image}`)
    : null;

  return (
    <div className="glass-panel rounded-2xl p-5 border border-slate-800/80 shadow-xl space-y-4">
      
      {/* Card Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Globe className="w-5 h-5 text-cyan-400" />
          <h3 className="text-base font-semibold text-white font-['Outfit']">Web Evidence Discovery</h3>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="bg-slate-900 text-slate-300 px-2.5 py-1 rounded-md border border-slate-800">
            {searchData.candidates_found ?? 0} Discovered
          </span>
        </div>
      </div>

      {/* Best Matching Hero Result */}
      {matchData.found ? (
        <div className="bg-slate-950/70 p-4 rounded-xl border border-cyan-500/30 flex flex-col md:flex-row gap-4 items-center">
          {/* Matched Image Preview */}
          {evidenceImgUrl && (
            <div className="w-28 h-28 rounded-lg overflow-hidden border border-cyan-500/40 bg-black flex-shrink-0 relative group">
              <img
                src={evidenceImgUrl}
                alt="Matched Candidate"
                className="w-full h-full object-cover group-hover:scale-105 transition-transform"
              />
              <span className="absolute bottom-1 right-1 bg-emerald-950/90 border border-emerald-500/60 text-emerald-300 text-[10px] font-mono font-bold px-1.5 py-0.5 rounded">
                MATCH
              </span>
            </div>
          )}

          {/* Details */}
          <div className="flex-1 space-y-2 text-xs">
            <div className="flex items-center justify-between gap-2">
              <span className="text-[11px] font-mono text-cyan-400 uppercase font-semibold">
                ★ Top Evidence Match
              </span>
              <span className="bg-emerald-950 text-emerald-300 border border-emerald-500/40 px-2 py-0.5 rounded font-mono font-bold">
                {(matchData.similarity * 100).toFixed(1)}% SIMILARITY
              </span>
            </div>

            <h4 className="font-semibold text-white text-sm line-clamp-1" title={matchData.candidate_title}>
              {matchData.candidate_title || 'Verified Web Candidate'}
            </h4>

            <p className="text-slate-400 font-mono text-[11px] truncate max-w-md">
              {matchData.source_url}
            </p>

            <a
              href={matchData.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-950 text-cyan-300 border border-cyan-700/60 hover:bg-cyan-900 hover:border-cyan-400 text-xs font-medium transition-all"
            >
              <span>Open Source Web Post</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          </div>
        </div>
      ) : (
        <div className="p-3 bg-amber-950/20 border border-amber-500/30 rounded-xl text-amber-300 text-xs">
          ⚠ No candidate met the similarity threshold (≥0.70).
        </div>
      )}

      {/* Expandable Candidates List */}
      {candidates.length > 0 && (
        <div className="border-t border-slate-800/80 pt-3">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="w-full flex items-center justify-between text-xs font-mono text-slate-400 hover:text-cyan-300 transition-colors py-1"
          >
            <span>Candidate Evaluation List ({candidates.length})</span>
            {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>

          {isExpanded && (
            <div className="mt-3 space-y-2 max-h-60 overflow-y-auto pr-1">
              {candidates.map((cand, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-2 rounded-lg bg-slate-950/60 border border-slate-800/80 text-xs hover:border-slate-700"
                >
                  <div className="flex items-center gap-2.5 truncate max-w-[70%]">
                    {cand.thumbnail_url ? (
                      <img
                        src={cand.thumbnail_url}
                        alt=""
                        className="w-8 h-8 rounded object-cover border border-slate-700 flex-shrink-0"
                      />
                    ) : (
                      <div className="w-8 h-8 rounded bg-slate-900 border border-slate-800 flex items-center justify-center flex-shrink-0 text-slate-500">
                        <Search className="w-3.5 h-3.5" />
                      </div>
                    )}

                    <div className="truncate">
                      <a
                        href={cand.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-slate-200 hover:text-cyan-300 font-medium truncate block"
                      >
                        {cand.domain}
                      </a>
                      <span className="text-[10px] text-slate-500 font-mono truncate block">
                        {cand.title}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 font-mono text-xs flex-shrink-0">
                    <span className="text-slate-400">{(cand.similarity * 100).toFixed(0)}%</span>
                    {cand.matched ? (
                      <span className="bg-emerald-950 text-emerald-300 border border-emerald-500/40 text-[10px] px-1.5 py-0.5 rounded font-bold">
                        MATCH
                      </span>
                    ) : (
                      <span className="bg-slate-900 text-slate-500 border border-slate-800 text-[10px] px-1.5 py-0.5 rounded">
                        NO MATCH
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

    </div>
  );
}
