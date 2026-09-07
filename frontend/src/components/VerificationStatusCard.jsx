import React from 'react';
import { CheckCircle2, XCircle, Clock, ShieldCheck, Loader2, MinusCircle } from 'lucide-react';

export default function VerificationStatusCard({ pipelineResult, isLoading }) {
  // Map stage status based on real FastAPI pipelineResult schema
  const getStageStatus = (stageKey) => {
    if (isLoading) return 'loading';
    if (!pipelineResult) return 'idle';

    const face = pipelineResult.face;
    const search = pipelineResult.search;
    const match = pipelineResult.match;
    const chain = pipelineResult.blockchain;
    const ver = pipelineResult.verification;

    switch (stageKey) {
      case 'detection':
        return face?.detected ? 'success' : 'failed';
      case 'embedding':
        return face?.detected ? 'success' : 'failed';
      case 'search':
        if (!face?.detected) return 'skipped';
        return (search?.candidates_found > 0) ? 'success' : 'skipped';
      case 'match':
        if (!search || search.candidates_found === 0) return 'skipped';
        return match?.found ? 'success' : 'skipped';
      case 'hash':
        if (!match?.found) return 'skipped';
        return chain?.hash ? 'success' : 'failed';
      case 'blockchain':
        if (!match?.found) return 'skipped';
        return chain?.registered ? 'success' : 'failed';
      case 'integrity':
        if (!chain?.registered) return 'skipped';
        return ver?.verified ? 'success' : 'failed';
      default:
        return 'idle';
    }
  };

  const steps = [
    { label: 'Face Detection', key: 'detection', desc: 'InsightFace SCRFD' },
    { label: 'Face Embedding', key: 'embedding', desc: 'ArcFace 512-d Vector' },
    { label: 'Web Search', key: 'search', desc: 'Google Lens (SerpApi)' },
    { label: 'Face Match', key: 'match', desc: 'Cosine Verification (≥0.70)' },
    { label: 'Evidence Hash', key: 'hash', desc: 'SHA-256 Binary Hash' },
    { label: 'Blockchain', key: 'blockchain', desc: 'Ethereum Sepolia Tx' },
    { label: 'Integrity', key: 'integrity', desc: 'On-Chain Recalculation' },
  ];

  return (
    <div className="glass-panel rounded-2xl p-6 border border-slate-800/80 shadow-2xl">
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-cyan-400" />
          <h3 className="text-base font-semibold text-white font-['Outfit']">Verification Status Checklist</h3>
        </div>
        <span className="text-xs font-mono text-slate-400">
          7-Stage Audit
        </span>
      </div>

      <div className="space-y-2.5">
        {steps.map((step) => {
          const status = getStageStatus(step.key);
          return (
            <div
              key={step.key}
              className={`flex items-center justify-between p-2.5 rounded-xl border transition-all ${
                status === 'success'
                  ? 'bg-emerald-950/20 border-emerald-500/30 text-emerald-300'
                  : status === 'failed'
                  ? 'bg-rose-950/20 border-rose-500/30 text-rose-300'
                  : status === 'skipped'
                  ? 'bg-slate-950/40 border-slate-800/60 text-slate-400'
                  : status === 'loading'
                  ? 'bg-cyan-950/20 border-cyan-500/30 text-cyan-300'
                  : 'bg-slate-950/40 border-slate-800/80 text-slate-400'
              }`}
            >
              <div>
                <div className="text-xs font-semibold text-slate-200">{step.label}</div>
                <div className="text-[11px] font-mono text-slate-500">{step.desc}</div>
              </div>

              <div>
                {status === 'success' && (
                  <div className="flex items-center gap-1 text-emerald-400 font-mono text-xs font-bold bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-500/40">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>PASSED</span>
                  </div>
                )}
                {status === 'failed' && (
                  <div className="flex items-center gap-1 text-rose-400 font-mono text-xs font-bold bg-rose-950/60 px-2 py-0.5 rounded border border-rose-500/40">
                    <XCircle className="w-3.5 h-3.5" />
                    <span>FAILED</span>
                  </div>
                )}
                {status === 'skipped' && (
                  <div className="flex items-center gap-1 text-slate-400 font-mono text-xs bg-slate-900/60 px-2 py-0.5 rounded border border-slate-800">
                    <MinusCircle className="w-3.5 h-3.5 text-slate-500" />
                    <span>SKIPPED</span>
                  </div>
                )}
                {status === 'loading' && (
                  <div className="flex items-center gap-1 text-cyan-400 font-mono text-xs bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-500/40">
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>RUNNING</span>
                  </div>
                )}
                {status === 'idle' && (
                  <div className="flex items-center gap-1 text-slate-500 font-mono text-xs bg-slate-900/60 px-2 py-0.5 rounded border border-slate-800">
                    <Clock className="w-3.5 h-3.5" />
                    <span>WAITING</span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
