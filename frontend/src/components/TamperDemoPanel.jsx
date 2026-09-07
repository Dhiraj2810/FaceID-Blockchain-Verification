import React, { useState } from 'react';
import { ShieldAlert, ShieldCheck, Play, RefreshCw, Copy, Check, Hash, Loader2 } from 'lucide-react';

export default function TamperDemoPanel({ pipelineResult }) {
  const [tamperState, setTamperState] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [copiedKey, setCopiedKey] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  const handleTamperTest = async (mode) => {
    setIsProcessing(true);
    setErrorMessage(null);

    const apiBase = '/api';
    const evidencePath = pipelineResult?.match?.evidence_path;
    const recordId = pipelineResult?.blockchain?.record_id;

    try {
      const res = await fetch(`${apiBase}/tamper-test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          evidence_path: evidencePath,
          record_id: recordId,
          mode: mode // 'original' or 'tamper'
        })
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Tamper test execution failed');
      }

      const data = await res.json();
      setTamperState(data);
    } catch (err) {
      setErrorMessage(err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const copyToClipboard = (text, key) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  return (
    <div className="glass-panel rounded-2xl p-6 border border-slate-800/80 shadow-2xl space-y-4">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-5 h-5 text-amber-400" />
          <h3 className="text-base font-semibold text-white font-['Outfit']">Tamper Verification</h3>
        </div>
        <span className="text-xs font-mono text-slate-400">
          Live Anti-Tamper Audit
        </span>
      </div>

      <p className="text-xs text-slate-400">
        Simulate an evidence file modification to verify that on-chain cryptographic hashes instantly reject tampered files.
      </p>

      {/* Buttons */}
      <div className="flex flex-wrap gap-3">
        <button
          onClick={() => handleTamperTest('original')}
          disabled={isProcessing}
          className="flex-1 min-w-[140px] py-2.5 px-4 rounded-xl text-xs font-semibold bg-emerald-950/80 text-emerald-300 border border-emerald-600/50 hover:bg-emerald-900 transition-all flex items-center justify-center gap-2 shadow-sm disabled:opacity-50"
        >
          {isProcessing ? <Loader2 className="w-4 h-4 animate-spin" /> : <ShieldCheck className="w-4 h-4 text-emerald-400" />}
          <span>Verify Original</span>
        </button>

        <button
          onClick={() => handleTamperTest('tamper')}
          disabled={isProcessing}
          className="flex-1 min-w-[140px] py-2.5 px-4 rounded-xl text-xs font-semibold bg-rose-950/80 text-rose-300 border border-rose-600/50 hover:bg-rose-900 transition-all flex items-center justify-center gap-2 shadow-sm disabled:opacity-50"
        >
          {isProcessing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4 text-rose-400" />}
          <span>Run Tamper Test</span>
        </button>
      </div>

      {errorMessage && (
        <div className="p-3 rounded-xl bg-rose-950/30 border border-rose-500/40 text-rose-300 text-xs font-mono">
          ⚠ {errorMessage}
        </div>
      )}

      {/* Results Display */}
      {tamperState && (
        <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 space-y-3 font-mono text-xs">
          
          {/* Status Badge */}
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
            <span className="text-[11px] text-slate-400 uppercase font-sans font-semibold">Test Result:</span>
            {tamperState.verified ? (
              <span className="bg-emerald-950 text-emerald-300 border border-emerald-500/50 px-2.5 py-0.5 rounded text-xs font-bold flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5" /> ✅ VERIFIED (MATCH)
              </span>
            ) : (
              <span className="bg-rose-950 text-rose-300 border border-rose-500/50 px-2.5 py-0.5 rounded text-xs font-bold flex items-center gap-1">
                <ShieldAlert className="w-3.5 h-3.5" /> ❌ TAMPERED (MISMATCH)
              </span>
            )}
          </div>

          {/* Original Hash */}
          <div className="space-y-1">
            <div className="flex justify-between text-[11px] text-slate-400">
              <span>Original Hash:</span>
              <button
                onClick={() => copyToClipboard(tamperState.original_hash, 'orig')}
                className="hover:text-cyan-300 flex items-center gap-1"
              >
                {copiedKey === 'orig' ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
              </button>
            </div>
            <div className="text-slate-300 bg-black/60 p-2 rounded truncate border border-slate-900">
              {tamperState.original_hash}
            </div>
          </div>

          {/* On-Chain Hash */}
          <div className="space-y-1">
            <div className="flex justify-between text-[11px] text-slate-400">
              <span>On-Chain Hash (Sepolia):</span>
              <button
                onClick={() => copyToClipboard(tamperState.on_chain_hash, 'chain')}
                className="hover:text-cyan-300 flex items-center gap-1"
              >
                {copiedKey === 'chain' ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
              </button>
            </div>
            <div className="text-emerald-400 bg-black/60 p-2 rounded truncate border border-slate-900 font-bold">
              {tamperState.on_chain_hash}
            </div>
          </div>

          {/* Current / Evaluated Hash */}
          <div className="space-y-1">
            <div className="flex justify-between text-[11px] text-slate-400">
              <span>Current File Hash:</span>
              <button
                onClick={() => copyToClipboard(tamperState.current_hash, 'curr')}
                className="hover:text-cyan-300 flex items-center gap-1"
              >
                {copiedKey === 'curr' ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
              </button>
            </div>
            <div
              className={`p-2 rounded truncate border border-slate-900 font-bold ${
                tamperState.verified ? 'text-emerald-300 bg-black/60' : 'text-rose-400 bg-rose-950/40 border-rose-500/40'
              }`}
            >
              {tamperState.current_hash}
            </div>
          </div>

        </div>
      )}

    </div>
  );
}
