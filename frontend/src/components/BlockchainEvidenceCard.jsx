import React, { useState } from 'react';
import { Database, Copy, Check, ExternalLink, Hash, Link2, Clock } from 'lucide-react';

export default function BlockchainEvidenceCard({ pipelineResult }) {
  const [copiedKey, setCopiedKey] = useState(null);

  if (!pipelineResult || !pipelineResult.blockchain || !pipelineResult.blockchain.registered) {
    return (
      <div className="glass-panel rounded-2xl p-5 border border-slate-800/80">
        <div className="flex items-center gap-2 mb-3">
          <Database className="w-5 h-5 text-cyan-400" />
          <h3 className="text-base font-semibold text-white font-['Outfit']">Blockchain Evidence Record</h3>
        </div>
        <p className="text-xs text-slate-500 italic">No blockchain transaction submitted yet.</p>
      </div>
    );
  }

  const chain = pipelineResult.blockchain;
  const etherscanUrl = `https://sepolia.etherscan.io/tx/${chain.transaction_hash}`;

  const copyToClipboard = (text, key) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  return (
    <div className="glass-panel rounded-2xl p-5 border border-slate-800/80 shadow-xl space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Database className="w-5 h-5 text-emerald-400" />
          <h3 className="text-base font-semibold text-white font-['Outfit']">On-Chain Evidence Record</h3>
        </div>
        <span className="bg-emerald-950/80 text-emerald-300 border border-emerald-500/40 text-xs font-mono px-2.5 py-1 rounded-md">
          {chain.network || 'Ethereum Sepolia'}
        </span>
      </div>

      <div className="space-y-3 font-mono text-xs">
        {/* SHA-256 Content Fingerprint */}
        <div className="bg-slate-950/70 p-3 rounded-xl border border-slate-800 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-[11px] font-sans">
            <span className="flex items-center gap-1.5 text-cyan-400 font-semibold">
              <Hash className="w-3.5 h-3.5" /> SHA-256 Evidence Fingerprint
            </span>
            <button
              onClick={() => copyToClipboard(chain.hash, 'hash')}
              className="text-slate-400 hover:text-cyan-300 flex items-center gap-1 transition-colors"
            >
              {copiedKey === 'hash' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copiedKey === 'hash' ? 'Copied' : 'Copy'}</span>
            </button>
          </div>
          <div className="text-slate-200 break-all bg-black/60 p-2 rounded border border-slate-900 text-[11px]">
            {chain.hash}
          </div>
        </div>

        {/* Contract Address */}
        <div className="bg-slate-950/70 p-3 rounded-xl border border-slate-800 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-[11px] font-sans">
            <span className="flex items-center gap-1.5 text-teal-400 font-semibold">
              <Link2 className="w-3.5 h-3.5" /> Smart Contract Address
            </span>
            <button
              onClick={() => copyToClipboard(chain.contract_address, 'contract')}
              className="text-slate-400 hover:text-cyan-300 flex items-center gap-1 transition-colors"
            >
              {copiedKey === 'contract' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copiedKey === 'contract' ? 'Copied' : 'Copy'}</span>
            </button>
          </div>
          <div className="text-slate-300 truncate bg-black/60 p-2 rounded border border-slate-900 text-[11px]">
            {chain.contract_address}
          </div>
        </div>

        {/* Transaction Hash */}
        <div className="bg-slate-950/70 p-3 rounded-xl border border-slate-800 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-[11px] font-sans">
            <span className="flex items-center gap-1.5 text-emerald-400 font-semibold">
              <Database className="w-3.5 h-3.5" /> Transaction Hash (Tx)
            </span>
            <button
              onClick={() => copyToClipboard(chain.transaction_hash, 'tx')}
              className="text-slate-400 hover:text-cyan-300 flex items-center gap-1 transition-colors"
            >
              {copiedKey === 'tx' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copiedKey === 'tx' ? 'Copied' : 'Copy'}</span>
            </button>
          </div>
          <div className="text-slate-300 truncate bg-black/60 p-2 rounded border border-slate-900 text-[11px]">
            {chain.transaction_hash}
          </div>
        </div>

        {/* Etherscan Button & Record ID */}
        <div className="flex flex-wrap items-center justify-between gap-2 pt-1 font-sans">
          <span className="text-[11px] text-slate-400 font-mono">
            Record ID: <strong className="text-cyan-300">#{chain.record_id}</strong>
          </span>

          <a
            href={etherscanUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-950/80 text-emerald-300 border border-emerald-500/50 hover:bg-emerald-900 hover:border-emerald-400 text-xs font-semibold transition-all shadow-sm"
          >
            <span>View Transaction on Etherscan</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>
      </div>
    </div>
  );
}
