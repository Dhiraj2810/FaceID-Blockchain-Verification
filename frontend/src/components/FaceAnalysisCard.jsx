import React from 'react';
import { UserCheck, Binary, Sliders, CheckCircle2, XCircle } from 'lucide-react';

export default function FaceAnalysisCard({ pipelineResult }) {
  if (!pipelineResult || !pipelineResult.face) {
    return (
      <div className="glass-panel rounded-2xl p-5 border border-slate-800/80">
        <div className="flex items-center gap-2 mb-3">
          <UserCheck className="w-5 h-5 text-cyan-400" />
          <h3 className="text-base font-semibold text-white font-['Outfit']">Face Analysis</h3>
        </div>
        <p className="text-xs text-slate-500 italic">No analysis data yet. Upload an image to begin.</p>
      </div>
    );
  }

  const faceData = pipelineResult.face || {};
  const matchData = pipelineResult.match || {};
  const similarityScore = matchData.similarity ? (matchData.similarity * 100).toFixed(1) : 'N/A';

  return (
    <div className="glass-panel rounded-2xl p-5 border border-slate-800/80 shadow-xl space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <UserCheck className="w-5 h-5 text-cyan-400" />
          <h3 className="text-base font-semibold text-white font-['Outfit']">Face Analysis</h3>
        </div>
        <span className="text-xs font-mono bg-cyan-950/80 text-cyan-300 border border-cyan-800/60 px-2 py-0.5 rounded">
          SCRFD + ArcFace
        </span>
      </div>

      <div className="grid grid-cols-2 gap-3 font-mono text-xs">
        {/* Face Detected */}
        <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800">
          <div className="text-[11px] text-slate-400 font-sans mb-1">Face Detected</div>
          <div className="flex items-center gap-1.5 font-bold text-sm">
            {faceData.detected ? (
              <span className="text-emerald-400 flex items-center gap-1">
                <CheckCircle2 className="w-4 h-4" /> YES
              </span>
            ) : (
              <span className="text-rose-400 flex items-center gap-1">
                <XCircle className="w-4 h-4" /> NO
              </span>
            )}
          </div>
        </div>

        {/* Face Count */}
        <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800">
          <div className="text-[11px] text-slate-400 font-sans mb-1">Face Count</div>
          <div className="font-bold text-sm text-cyan-300">
            {faceData.count ?? 0} Primary Face
          </div>
        </div>

        {/* ArcFace Embedding */}
        <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800">
          <div className="text-[11px] text-slate-400 font-sans mb-1">ArcFace Embedding</div>
          <div className="font-bold text-xs text-teal-300 flex items-center gap-1">
            <Binary className="w-3.5 h-3.5" /> 512-d L2 Vector
          </div>
        </div>

        {/* Similarity Score */}
        <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800">
          <div className="text-[11px] text-slate-400 font-sans mb-1">Top Similarity</div>
          <div className={`font-bold text-sm ${matchData.found ? 'text-emerald-400' : 'text-slate-400'}`}>
            {similarityScore}%
          </div>
        </div>
      </div>
    </div>
  );
}
