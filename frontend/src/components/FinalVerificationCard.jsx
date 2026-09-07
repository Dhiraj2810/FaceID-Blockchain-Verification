import React from 'react';
import { ShieldCheck, ShieldAlert, CheckCircle2, AlertTriangle } from 'lucide-react';

export default function FinalVerificationCard({ pipelineResult }) {
  if (!pipelineResult || !pipelineResult.verification) {
    return null;
  }

  const ver = pipelineResult.verification;
  const isVerified = ver.verified && ver.status === 'VERIFIED';

  return (
    <div
      className={`rounded-2xl p-6 border shadow-2xl transition-all ${
        isVerified
          ? 'glass-panel-glow border-emerald-500/40 bg-gradient-to-br from-emerald-950/40 via-slate-900/80 to-slate-950/90 shadow-emerald-500/10'
          : 'glass-panel border-rose-500/60 bg-gradient-to-br from-rose-950/40 via-slate-900/80 to-slate-950/90 shadow-rose-500/15'
      }`}
    >
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
        
        {/* Banner Status Icon & Text */}
        <div className="flex items-center gap-4 text-center sm:text-left">
          <div
            className={`w-14 h-14 rounded-2xl flex items-center justify-center flex-shrink-0 shadow-lg ${
              isVerified
                ? 'bg-emerald-950 border border-emerald-500/50 text-emerald-400 shadow-emerald-500/20'
                : 'bg-rose-950 border border-rose-500/60 text-rose-400 shadow-rose-500/20 animate-pulse'
            }`}
          >
            {isVerified ? (
              <ShieldCheck className="w-8 h-8" />
            ) : (
              <ShieldAlert className="w-8 h-8" />
            )}
          </div>

          <div>
            <div className="flex items-center justify-center sm:justify-start gap-2">
              <h2
                className={`text-2xl font-bold font-['Outfit'] tracking-tight ${
                  isVerified ? 'text-emerald-300' : 'text-rose-400'
                }`}
              >
                {isVerified ? '✅ BLOCKCHAIN VERIFIED' : '❌ TAMPER DETECTED'}
              </h2>
            </div>
            <p className="text-xs text-slate-300 mt-1 max-w-lg">
              {isVerified
                ? 'The downloaded web evidence fingerprint matches the immutable fingerprint stored on the Sepolia smart contract.'
                : 'CRITICAL ALERT: The evidence content fingerprint has been modified or corrupted and does NOT match the immutable on-chain record!'}
            </p>
          </div>
        </div>

        {/* Hashes Summary Pill */}
        <div className="bg-slate-950/80 p-3 rounded-xl border border-slate-800 font-mono text-[11px] space-y-1 w-full sm:w-auto flex-shrink-0">
          <div className="flex justify-between gap-3 text-slate-400">
            <span>Local Hash:</span>
            <span className="text-slate-200 font-bold">{ver.local_hash ? `${ver.local_hash.slice(0, 10)}...` : 'N/A'}</span>
          </div>
          <div className="flex justify-between gap-3 text-slate-400">
            <span>Chain Hash:</span>
            <span className="text-emerald-300 font-bold">{ver.on_chain_hash ? `${ver.on_chain_hash.slice(0, 10)}...` : 'N/A'}</span>
          </div>
        </div>

      </div>
    </div>
  );
}
